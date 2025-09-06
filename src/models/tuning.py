"""Optuna-based hyperparameter optimization for trading strategy thresholds."""

import logging

import numpy as np
import optuna
import pandas as pd

from src.backtest.engine import WalkForwardBacktester
from src.data.storage import load_features, load_ohlcv
from src.models.ensemble import EnsembleModel
from src.models.training import FEATURE_COLS

logger = logging.getLogger(__name__)

optuna.logging.set_verbosity(optuna.logging.WARNING)


def optimize_thresholds(
    ticker: str,
    n_trials: int = 50,
    db_path: str | None = None,
) -> dict:
    """Find optimal buy/sell thresholds and position size via Optuna.

    Trains an EnsembleModel on the first 70% of data, generates predictions
    on the remaining 30%, then searches for threshold parameters that
    maximize the Sharpe ratio on walk-forward backtest results.

    Args:
        ticker: Stock ticker symbol.
        n_trials: Number of Optuna trials to run.
        db_path: Optional path to the SQLite database.

    Returns:
        Dict with keys: best_params, best_sharpe, study_summary.
    """
    # Load data
    features_df = load_features(ticker, db_path=db_path)
    ohlcv_df = load_ohlcv(ticker, db_path=db_path)

    features_df = features_df.dropna(subset=FEATURE_COLS + ["target"]).reset_index(drop=True)

    if len(features_df) < 100:
        raise ValueError(f"Insufficient data for {ticker}: {len(features_df)} rows")

    # Split 70/30
    split_idx = int(len(features_df) * 0.7)
    train_df = features_df.iloc[:split_idx]
    test_df = features_df.iloc[split_idx:]

    feature_names = [c for c in FEATURE_COLS if c in features_df.columns]
    X_train = train_df[feature_names].values
    y_train = train_df["target"].values
    X_test = test_df[feature_names].values

    # Train ensemble once
    model = EnsembleModel()
    model.fit(X_train, y_train, feature_names=feature_names)

    # Generate predictions on test set
    probabilities = model.predict_proba(X_test)

    # LSTM windowing may shorten output; align with tail of test_df
    n_preds = len(probabilities)
    test_tail = test_df.iloc[-n_preds:].copy()

    oos_predictions = pd.DataFrame({
        "date": pd.to_datetime(test_tail["date"]).values,
        "ticker": ticker,
        "probability_up": probabilities,
    })

    prices = ohlcv_df[["date", "ticker", "close"]].copy()
    prices["date"] = pd.to_datetime(prices["date"])

    def objective(trial: optuna.Trial) -> float:
        buy_threshold = trial.suggest_float("buy_threshold", 0.5, 0.9)
        sell_threshold = trial.suggest_float("sell_threshold", 0.1, 0.5)
        max_position_pct = trial.suggest_float("max_position_pct", 0.05, 0.25)

        backtester = WalkForwardBacktester(
            buy_threshold=buy_threshold,
            sell_threshold=sell_threshold,
            max_position_pct=max_position_pct,
        )

        try:
            result = backtester.run(oos_predictions, prices)
        except (ValueError, KeyError):
            return 0.0

        sharpe = result.metrics.get("sharpe_ratio", 0.0)
        if sharpe is None or np.isnan(sharpe):
            return 0.0
        return sharpe

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=n_trials)

    best = study.best_trial
    logger.info(f"Best Sharpe {best.value:.4f} with params {best.params}")

    return {
        "best_params": best.params,
        "best_sharpe": best.value,
        "study_summary": {
            "n_trials": len(study.trials),
            "best_trial_number": best.number,
            "param_importances": {
                p: float(v)
                for p, v in optuna.importance.get_param_importances(study).items()
            },
        },
    }
