import logging
from dataclasses import dataclass, field
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from src.config import settings
from src.data.storage import load_features
from src.models.ensemble import EnsembleModel
from src.models.registry import save_model

logger = logging.getLogger(__name__)

FEATURE_COLS = [
    "rsi_14",
    "macd",
    "macd_signal",
    "macd_hist",
    "bb_upper",
    "bb_middle",
    "bb_lower",
    "bb_pct_b",
    "bb_bandwidth",
    "atr_14",
    "stoch_k",
    "stoch_d",
    "adx_14",
    "close_to_sma50",
    "close_to_sma200",
    "sma50_to_sma200",
    "return_lag_1",
    "return_lag_2",
    "return_lag_3",
    "return_lag_5",
    "volatility_5",
    "volatility_20",
    "momentum_5",
    "momentum_20",
    "mean_reversion_20",
    "volume_ratio",
    "obv",
]


@dataclass
class FoldResult:
    fold_idx: int
    train_start: datetime
    train_end: datetime
    test_start: datetime
    test_end: datetime
    train_accuracy: float
    test_accuracy: float
    oos_predictions: pd.DataFrame = field(default_factory=pd.DataFrame)


@dataclass
class TrainingResult:
    ticker: str
    model_version: str
    feature_names: list[str]
    fold_results: list[FoldResult]
    oos_predictions: pd.DataFrame

    @property
    def mean_test_accuracy(self) -> float:
        if not self.fold_results:
            return 0.0
        return np.mean([f.test_accuracy for f in self.fold_results])


def walk_forward_train(
    ticker: str,
    window: int | None = None,
    retrain_interval: int | None = None,
    db_path: str | None = None,
) -> TrainingResult:
    """
    Walk-forward training with expanding window.

    For each fold:
        - Train on all data from start to t
        - Test on data from t to t+retrain_interval
        - Collect out-of-sample predictions
    """
    window = window or settings.walk_forward_window
    retrain_interval = retrain_interval or settings.retrain_interval

    df = load_features(ticker, db_path=db_path)
    if df.empty:
        raise ValueError(f"No feature data found for {ticker}")

    df = df.dropna(subset=FEATURE_COLS + ["target"]).reset_index(drop=True)

    feature_names = [c for c in FEATURE_COLS if c in df.columns]
    X = df[feature_names].values
    y = df["target"].values
    dates = pd.to_datetime(df["date"])

    # Scale features
    scaler = StandardScaler()

    fold_results = []
    all_oos_preds = []

    fold_idx = 0
    test_start_idx = (
        window  # expanding window: train on [0, window], test on [window, window+interval]
    )

    while test_start_idx < len(X):
        test_end_idx = min(test_start_idx + retrain_interval, len(X))

        X_train = X[:test_start_idx]
        y_train = y[:test_start_idx]
        X_test = X[test_start_idx:test_end_idx]
        y_test = y[test_start_idx:test_end_idx]

        # Fit scaler on train, apply to test
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        model = EnsembleModel(sequence_length=settings.sequence_length)
        model.fit(X_train_scaled, y_train, feature_names=feature_names)

        train_preds = model.predict(X_train_scaled)
        n_train_preds = len(train_preds)
        train_acc = float(np.mean(train_preds == y_train[-n_train_preds:]))

        oos_proba = model.predict_proba(X_test_scaled)
        oos_pred = (oos_proba >= 0.5).astype(int)

        # Align: LSTM may produce fewer predictions due to sequence offset
        n_preds = len(oos_proba)
        test_acc = float(np.mean(oos_pred == y_test[-n_preds:]))

        fold = FoldResult(
            fold_idx=fold_idx,
            train_start=dates.iloc[0],
            train_end=dates.iloc[test_start_idx - 1],
            test_start=dates.iloc[test_start_idx],
            test_end=dates.iloc[test_end_idx - 1],
            train_accuracy=train_acc,
            test_accuracy=test_acc,
        )

        # Store OOS predictions aligned with dates
        test_dates = dates.iloc[test_start_idx:test_end_idx].values[-n_preds:]
        oos_df = pd.DataFrame(
            {
                "date": test_dates,
                "ticker": ticker,
                "probability_up": oos_proba,
                "prediction": oos_pred,
                "actual": y_test[-n_preds:],
            }
        )
        all_oos_preds.append(oos_df)

        logger.info(
            f"Fold {fold_idx}: train_acc={train_acc:.3f}, test_acc={test_acc:.3f} "
            f"({dates.iloc[test_start_idx].date()} to {dates.iloc[test_end_idx - 1].date()})"
        )

        fold_results.append(fold)
        fold_idx += 1
        test_start_idx += retrain_interval

    # Train final model on all data
    logger.info("Training final model on full dataset")
    X_scaled = scaler.fit_transform(X)
    final_model = EnsembleModel(sequence_length=settings.sequence_length)
    final_model.fit(X_scaled, y, feature_names=feature_names)

    oos_predictions = (
        pd.concat(all_oos_preds, ignore_index=True) if all_oos_preds else pd.DataFrame()
    )

    mean_acc = np.mean([f.test_accuracy for f in fold_results]) if fold_results else 0.0

    version_id = save_model(
        {"model": final_model, "scaler": scaler},
        metadata={
            "ticker": ticker,
            "feature_names": feature_names,
            "n_folds": len(fold_results),
            "mean_test_accuracy": mean_acc,
            "total_samples": len(X),
        },
    )

    logger.info(f"Training done. Mean OOS accuracy: {mean_acc:.3f}. Model: {version_id}")

    return TrainingResult(
        ticker=ticker,
        model_version=version_id,
        feature_names=feature_names,
        fold_results=fold_results,
        oos_predictions=oos_predictions,
    )
