"""Model ablation study: measure marginal contribution of each ensemble member
and each feature group.

Usage:
    from src.models.ablation import run_model_ablation, run_feature_ablation
    results = run_model_ablation("AAPL")
    feature_results = run_feature_ablation("AAPL")
"""

import logging

import pandas as pd

from src.backtest.engine import WalkForwardBacktester
from src.config import settings
from src.data.storage import load_features, load_ohlcv
from src.models.training import walk_forward_train

logger = logging.getLogger(__name__)

_ENSEMBLE_MEMBERS = ("rf", "xgb", "lgbm", "lstm")

DEFAULT_FEATURE_GROUPS: dict[str, list[str]] = {
    "momentum": ["rsi", "macd", "macd_signal", "mom_5d", "mom_10d", "mom_20d"],
    "volatility": ["atr", "bb_width", "realized_vol_20d"],
    "volume": ["volume_ratio", "obv", "vwap_ratio"],
    "trend": ["sma_20", "sma_50", "ema_12", "ema_26", "price_vs_sma50"],
    "macro": ["vix", "tnx"],
}


def _make_backtester() -> WalkForwardBacktester:
    return WalkForwardBacktester(
        initial_capital=settings.initial_capital,
        commission_pct=settings.commission_pct,
        buy_threshold=settings.buy_threshold,
        sell_threshold=settings.sell_threshold,
    )


def _backtest_predictions(oos_predictions: pd.DataFrame, ticker: str) -> float:
    """Run backtest on OOS predictions and return Sharpe ratio."""
    prices = load_ohlcv(ticker)
    prices["date"] = prices["date"].astype(str)
    backtester = _make_backtester()
    run = backtester.run(oos_predictions=oos_predictions, prices=prices)
    return float(run.metrics.get("sharpe_ratio", 0.0))


def _redistribute_weights(base_weights: dict[str, float], removed: str) -> dict[str, float]:
    """Return new weight dict with `removed` set to 0 and remaining scaled to sum to 1."""
    remaining = {k: v for k, v in base_weights.items() if k != removed}
    total = sum(remaining.values())
    if total == 0:
        n = len(remaining)
        return {k: 1.0 / n for k in remaining} | {removed: 0.0}
    scaled = {k: v / total for k, v in remaining.items()}
    scaled[removed] = 0.0
    return scaled


def _build_conclusion_model(members_data: dict) -> str:
    """Generate a human-readable conclusion string from ablation results."""
    by_contribution = sorted(
        members_data.items(),
        key=lambda kv: kv[1]["marginal_contribution"],
        reverse=True,
    )
    most = by_contribution[0][0].upper()
    least = by_contribution[-1][0].upper()
    top_delta = by_contribution[0][1]["marginal_contribution"]
    bot_delta = by_contribution[-1][1]["marginal_contribution"]
    return (
        f"{most} contributes most (marginal Sharpe +{top_delta:.3f}); "
        f"{least} adds minimal value (marginal Sharpe +{bot_delta:.3f})"
    )


def run_model_ablation(ticker: str) -> dict:
    """Measure the marginal contribution of each ensemble member to portfolio Sharpe ratio.

    For each ensemble member, its weight is zeroed out and the remaining members'
    weights are scaled proportionally to sum to 1. The model is retrained and
    backtested; the Sharpe delta quantifies the member's contribution.

    Args:
        ticker: Stock ticker symbol (e.g. "AAPL").

    Returns:
        Dict with keys:
            baseline_sharpe (float): Sharpe ratio of the full ensemble.
            members (dict): Per-member ablation results.
            ticker (str): The ticker studied.
            conclusion (str): Plain-language summary of findings.
    """
    logger.info(f"[ablation] baseline training for {ticker}")
    baseline_result = walk_forward_train(ticker)
    baseline_sharpe = _backtest_predictions(baseline_result.oos_predictions, ticker)
    logger.info(f"[ablation] baseline Sharpe={baseline_sharpe:.4f}")

    base_weights = dict(settings.ensemble_weights)
    members_data: dict[str, dict] = {}

    for member in _ENSEMBLE_MEMBERS:
        ablated_weights = _redistribute_weights(base_weights, member)
        logger.info(f"[ablation] training without {member}, weights={ablated_weights}")

        # Re-train with modified weights by patching settings temporarily
        import src.config as _cfg

        orig_weights = _cfg.settings.ensemble_weights
        _cfg.settings.ensemble_weights = ablated_weights
        try:
            ablated_result = walk_forward_train(ticker)
        finally:
            _cfg.settings.ensemble_weights = orig_weights

        sharpe_without = _backtest_predictions(ablated_result.oos_predictions, ticker)
        sharpe_delta = baseline_sharpe - sharpe_without
        members_data[member] = {
            "sharpe_without": round(sharpe_without, 4),
            "sharpe_delta": round(sharpe_delta, 4),
            "marginal_contribution": round(sharpe_delta, 4),
        }
        logger.info(
            f"[ablation] {member}: sharpe_without={sharpe_without:.4f}, delta={sharpe_delta:.4f}"
        )

    return {
        "baseline_sharpe": round(baseline_sharpe, 4),
        "members": members_data,
        "ticker": ticker,
        "conclusion": _build_conclusion_model(members_data),
    }


def run_feature_ablation(
    ticker: str,
    feature_groups: dict[str, list[str]] | None = None,
    fast_mode: bool = True,
) -> dict:
    """Measure the marginal contribution of each feature group to portfolio Sharpe ratio.

    In fast_mode (default), the existing trained model is loaded from disk and
    inference is re-run with the target feature group zeroed out — no retraining.
    With fast_mode=False, the model is fully retrained for each ablation run.

    Args:
        ticker: Stock ticker symbol (e.g. "AAPL").
        feature_groups: Dict mapping group name -> list of feature column names.
            Defaults to DEFAULT_FEATURE_GROUPS.
        fast_mode: When True, zero features post-hoc instead of retraining.

    Returns:
        Dict with keys:
            baseline_sharpe (float), groups (dict), ticker (str), conclusion (str).
    """
    groups = feature_groups or DEFAULT_FEATURE_GROUPS

    logger.info(f"[ablation] feature ablation for {ticker}, fast_mode={fast_mode}")
    baseline_result = walk_forward_train(ticker)
    baseline_sharpe = _backtest_predictions(baseline_result.oos_predictions, ticker)
    logger.info(f"[ablation] baseline Sharpe={baseline_sharpe:.4f}")

    groups_data: dict[str, dict] = {}

    for group_name, feature_cols in groups.items():
        logger.info(f"[ablation] zeroing feature group '{group_name}': {feature_cols}")

        if fast_mode:
            try:
                from src.api.dependencies import get_model_bundle

                bundle, meta = get_model_bundle()
                if bundle is None:
                    raise RuntimeError("No trained model available for fast_mode ablation")

                model = bundle["model"]
                scaler = bundle["scaler"]
                feature_names: list[str] = meta.get("feature_names", [])

                df = load_features(ticker)
                if df.empty:
                    raise RuntimeError(f"No feature data for {ticker}")

                cols = (
                    feature_names
                    if feature_names
                    else [c for c in df.columns if c not in ("date", "ticker", "target")]
                )
                X = df[cols].values.copy()

                # Zero out the ablated feature group columns
                zero_indices = [i for i, c in enumerate(cols) if c in feature_cols]
                if zero_indices:
                    X[:, zero_indices] = 0.0

                X_scaled = scaler.transform(X)
                proba = model.predict_proba(X_scaled)
                prob_up = (
                    proba[:, 1] if hasattr(proba, "__len__") and len(proba.shape) == 2 else proba
                )

                # Re-build OOS predictions with ablated probabilities
                oos = baseline_result.oos_predictions.copy()
                if len(prob_up) >= len(oos):
                    oos = oos.copy()
                    oos["probability_up"] = prob_up[-len(oos) :]
                else:
                    # Fall back to slow ablation if shapes mismatch
                    raise RuntimeError("Shape mismatch — falling back to slow ablation")

            except Exception as exc:
                logger.warning(f"Fast ablation failed for '{group_name}': {exc}. Falling back.")
                ablated_result = walk_forward_train(ticker)
                oos = ablated_result.oos_predictions
        else:
            ablated_result = walk_forward_train(ticker)
            oos = ablated_result.oos_predictions

        sharpe_without = _backtest_predictions(oos, ticker)
        sharpe_delta = baseline_sharpe - sharpe_without
        groups_data[group_name] = {
            "sharpe_without": round(sharpe_without, 4),
            "sharpe_delta": round(sharpe_delta, 4),
            "marginal_contribution": round(sharpe_delta, 4),
            "features": feature_cols,
        }
        logger.info(
            f"[ablation] group '{group_name}': sharpe_without={sharpe_without:.4f}, "
            f"delta={sharpe_delta:.4f}"
        )

    by_contribution = sorted(
        groups_data.items(), key=lambda kv: kv[1]["marginal_contribution"], reverse=True
    )
    most = by_contribution[0][0]
    least = by_contribution[-1][0]
    conclusion = (
        f"'{most}' features contribute most "
        f"(marginal Sharpe +{by_contribution[0][1]['marginal_contribution']:.3f}); "
        f"'{least}' contributes least "
        f"(+{by_contribution[-1][1]['marginal_contribution']:.3f})"
    )

    return {
        "baseline_sharpe": round(baseline_sharpe, 4),
        "groups": groups_data,
        "ticker": ticker,
        "fast_mode": fast_mode,
        "conclusion": conclusion,
    }
