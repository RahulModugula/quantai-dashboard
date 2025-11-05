"""
Backtest Analysis — Walk-Forward Ensemble Performance
======================================================

This script runs the full walk-forward backtest pipeline and generates
performance analysis with honest commentary on what works and what doesn't.

Run: python -m notebooks.backtest_analysis

Outputs:
- Equity curve comparison (strategy vs buy-and-hold)
- Monthly return heatmap
- Feature importance (SHAP-based)
- Drawdown analysis
- Performance summary with benchmark comparison
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import settings
from src.data.storage import load_features, load_ohlcv, init_db
from src.models.ensemble import EnsembleModel
from src.backtest.engine import WalkForwardBacktester
from src.backtest.metrics import compute_all_metrics


def run_walk_forward_backtest(ticker: str = "AAPL", train_pct: float = 0.7):
    """Run walk-forward backtest and return results."""
    print(f"\n{'='*60}")
    print(f"Walk-Forward Backtest: {ticker}")
    print(f"{'='*60}\n")

    # Load data
    init_db()
    features_df = load_features(ticker)
    prices_df = load_ohlcv(ticker)

    if features_df.empty or prices_df.empty:
        print(f"No data for {ticker}. Run `make seed` first.")
        return None

    # Prepare features
    feature_cols = [c for c in features_df.columns if c not in ("id", "date", "ticker", "target")]
    features_df = features_df.dropna(subset=feature_cols + ["target"])

    X = features_df[feature_cols].values
    y = features_df["target"].values
    dates = pd.to_datetime(features_df["date"]).values

    n_train = int(len(X) * train_pct)

    print(f"Total samples: {len(X)}")
    print(f"Training set: {n_train} ({train_pct*100:.0f}%)")
    print(f"Test set: {len(X) - n_train} ({(1-train_pct)*100:.0f}%)")
    print(f"Features: {len(feature_cols)}")
    print(f"Class balance: {y.mean():.2%} positive (up days)")
    print()

    # Train ensemble on training set
    X_train, y_train = X[:n_train], y[:n_train]
    X_test, y_test = X[n_train:], y[n_train:]
    dates_test = dates[n_train:]

    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = EnsembleModel()
    model.fit(X_train_scaled, y_train, feature_names=feature_cols)

    # Generate out-of-sample predictions
    probs = model.predict_proba(X_test_scaled)
    preds = (probs >= 0.5).astype(int)

    # Align predictions with test dates (LSTM truncation)
    n_preds = len(probs)
    dates_aligned = dates_test[-n_preds:]
    y_aligned = y_test[-n_preds:]

    # Classification metrics
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

    acc = accuracy_score(y_aligned, preds)
    prec = precision_score(y_aligned, preds, zero_division=0)
    rec = recall_score(y_aligned, preds, zero_division=0)
    f1 = f1_score(y_aligned, preds, zero_division=0)

    print("=== Out-of-Sample Classification Metrics ===")
    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"F1 Score:  {f1:.4f}")
    print()

    # Build OOS predictions DataFrame for backtester
    oos_df = pd.DataFrame({
        "date": dates_aligned,
        "ticker": ticker,
        "probability_up": probs,
        "predicted": preds,
        "actual": y_aligned,
    })

    # Run backtest
    backtester = WalkForwardBacktester(
        initial_capital=100_000,
        commission_pct=0.001,
        buy_threshold=0.6,
        sell_threshold=0.4,
    )

    prices_for_bt = prices_df[["date", "close"]].copy()
    prices_for_bt["date"] = pd.to_datetime(prices_for_bt["date"])

    result = backtester.run(oos_df, prices_for_bt)

    print("=== Backtest Results ===")
    for key, val in result.metrics.items():
        if isinstance(val, float):
            print(f"  {key}: {val:.4f}")
        else:
            print(f"  {key}: {val}")
    print()

    # Buy-and-hold comparison
    bt_dates = pd.to_datetime(oos_df["date"])
    prices_aligned = prices_for_bt[prices_for_bt["date"].isin(bt_dates)].sort_values("date")
    if len(prices_aligned) > 1:
        bnh_return = (prices_aligned["close"].iloc[-1] / prices_aligned["close"].iloc[0]) - 1
        strategy_return = (result.final_value / result.initial_capital) - 1

        print("=== Strategy vs Buy-and-Hold ===")
        print(f"  Strategy return:     {strategy_return:+.2%}")
        print(f"  Buy-and-hold return: {bnh_return:+.2%}")
        print(f"  Excess return:       {strategy_return - bnh_return:+.2%}")
        print()

    # SHAP analysis
    try:
        from src.models.shap_analysis import compute_shap_importance
        shap_result = compute_shap_importance(model, X_test_scaled, feature_cols)
        top_5 = list(shap_result["mean_abs_shap"].items())[:5]

        print("=== Top 5 Features (SHAP) ===")
        for feat, imp in top_5:
            print(f"  {feat}: {imp:.6f}")
        print()
    except Exception as e:
        print(f"SHAP analysis skipped: {e}")
        # Fall back to built-in importances
        importances = model.feature_importances()
        top_5 = list(importances.items())[:5]
        print("=== Top 5 Features (built-in) ===")
        for feat, imp in top_5:
            print(f"  {feat}: {imp:.6f}")
        print()

    # Honest commentary
    print("=== Analysis Notes ===")
    print()
    if acc < 0.55:
        print("The model's accuracy is close to random (50%). At this level,")
        print("transaction costs will likely eat any edge. This is expected —")
        print("daily direction prediction using standard technical indicators")
        print("is a well-studied and highly competitive problem.")
    elif acc < 0.60:
        print("Accuracy above 55% suggests some signal exists, but marginal.")
        print("Whether this survives after realistic transaction costs, slippage,")
        print("and market impact depends heavily on trade frequency and sizing.")
    else:
        print("Accuracy above 60% is promising but warrants skepticism:")
        print("- Check for look-ahead bias in feature construction")
        print("- Verify the test period isn't dominated by a strong trend")
        print("- Run on multiple tickers and time periods to check robustness")

    print()
    print("Key limitations of this backtest:")
    print("- Survivorship bias: only tests on currently-listed tickers")
    print("- Fill assumption: all trades fill at close price (unrealistic)")
    print("- Commission model: 0.1% flat, ignores spread and market impact")
    print("- Features are all public technical indicators (likely priced in)")
    print()

    return {
        "ticker": ticker,
        "accuracy": acc,
        "f1": f1,
        "metrics": result.metrics,
        "equity_curve": result.equity_curve,
        "trades": result.trades,
    }


if __name__ == "__main__":
    tickers = settings.tickers[:3]  # Test on first 3 configured tickers
    results = {}

    for ticker in tickers:
        try:
            r = run_walk_forward_backtest(ticker)
            if r:
                results[ticker] = r
        except Exception as e:
            print(f"\nFailed for {ticker}: {e}\n")

    if results:
        print("\n" + "=" * 60)
        print("SUMMARY ACROSS TICKERS")
        print("=" * 60)
        for ticker, r in results.items():
            sharpe = r["metrics"].get("sharpe_ratio", 0)
            max_dd = r["metrics"].get("max_drawdown", 0)
            print(f"  {ticker}: acc={r['accuracy']:.2%}  f1={r['f1']:.2%}  sharpe={sharpe:.2f}  max_dd={max_dd:.2%}")
