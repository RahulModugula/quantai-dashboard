"""Market regime detection based on volatility and trend analysis."""

import logging
from math import sqrt

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Minimum rows required to compute 200-day MA and 20-day vol
MIN_BARS = 210

# Annualized volatility thresholds
LOW_VOL_THRESHOLD = 0.15
HIGH_VOL_THRESHOLD = 0.30


class RegimeDetector:
    """Classify market regimes along volatility and trend dimensions."""

    def __init__(self, vol_window: int = 20, trend_short: int = 50, trend_long: int = 200):
        self.vol_window = vol_window
        self.trend_short = trend_short
        self.trend_long = trend_long

    def classify(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add regime columns to OHLCV DataFrame.

        Returns df with added columns:
        - realized_vol: 20-day annualized realized volatility
        - vol_regime: 'low_vol' | 'normal_vol' | 'high_vol'
        - trend_regime: 'trending_up' | 'trending_down' | 'sideways'
        - regime: combined label

        Raises:
            ValueError: If df has fewer than MIN_BARS rows.
        """
        if len(df) < MIN_BARS:
            raise ValueError(
                f"Insufficient history: {len(df)} rows (need >= {MIN_BARS} for 200-day MA)"
            )

        result = df.copy()

        returns = result["close"].pct_change()
        result["realized_vol"] = returns.rolling(self.vol_window).std() * sqrt(252)

        result["vol_regime"] = result["realized_vol"].apply(self._vol_regime_label)

        ma_short = result["close"].rolling(self.trend_short).mean()
        ma_long = result["close"].rolling(self.trend_long).mean()
        result["_ma_short"] = ma_short
        result["_ma_long"] = ma_long

        result["trend_regime"] = result.apply(
            lambda row: self._trend_regime_label(row["close"], row["_ma_short"], row["_ma_long"]),
            axis=1,
        )

        result["regime"] = result.apply(
            lambda row: self._combined_label(row["vol_regime"], row["trend_regime"]),
            axis=1,
        )

        result.drop(columns=["_ma_short", "_ma_long"], inplace=True)

        return result

    def current_regime(self, df: pd.DataFrame) -> dict:
        """Return regime classification for the most recent row."""
        classified = self.classify(df)
        last = classified.iloc[-1]
        date_val = last["date"] if "date" in last.index else classified.index[-1]
        return {
            "date": str(date_val),
            "regime": last["regime"],
            "vol_regime": last["vol_regime"],
            "trend_regime": last["trend_regime"],
            "realized_vol": round(float(last["realized_vol"]), 6)
            if not pd.isna(last["realized_vol"])
            else None,
        }

    def regime_performance(self, df: pd.DataFrame, equity_curve: pd.Series) -> dict:
        """Compute mean daily return per regime label.

        Returns {regime_label: {'mean_daily_return': float, 'count': int, 'sharpe': float}}
        """
        classified = self.classify(df)
        daily_returns = equity_curve.pct_change().dropna()

        regime_series = classified["regime"].reset_index(drop=True)
        returns_aligned = daily_returns.reset_index(drop=True)

        combined = pd.DataFrame({"regime": regime_series, "return": returns_aligned}).dropna()

        result = {}
        for label, group in combined.groupby("regime"):
            returns_group = group["return"]
            mean_ret = float(returns_group.mean())
            count = int(len(returns_group))
            std = float(returns_group.std())
            sharpe = (mean_ret / std * sqrt(252)) if std > 0 and count > 1 else 0.0
            result[label] = {
                "mean_daily_return": round(mean_ret, 6),
                "count": count,
                "sharpe": round(sharpe, 4),
            }

        return result

    def regime_statistics(self, df: pd.DataFrame) -> dict:
        """Compute aggregate statistics for each regime label.

        Returns:
            {regime_label: {'count': int, 'pct_time': float, 'avg_duration_days': float}}
        """
        classified = self.classify(df)
        regime_col = classified["regime"]
        total = len(regime_col)

        stats: dict[str, dict] = {}
        current_label: str | None = None
        run_len = 0
        runs: dict[str, list[int]] = {}

        for label in regime_col:
            if label != current_label:
                if current_label is not None:
                    runs.setdefault(current_label, []).append(run_len)
                current_label = label
                run_len = 1
            else:
                run_len += 1
        if current_label is not None:
            runs.setdefault(current_label, []).append(run_len)

        for label, run_lengths in runs.items():
            count = int(regime_col[regime_col == label].count())
            stats[label] = {
                "count": count,
                "pct_time": round(count / total, 4) if total > 0 else 0.0,
                "avg_duration_days": round(float(np.mean(run_lengths)), 1),
            }

        return stats

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _vol_regime_label(vol: float) -> str:
        if pd.isna(vol):
            return "normal_vol"
        if vol < LOW_VOL_THRESHOLD:
            return "low_vol"
        if vol > HIGH_VOL_THRESHOLD:
            return "high_vol"
        return "normal_vol"

    @staticmethod
    def _trend_regime_label(price: float, ma_short: float, ma_long: float) -> str:
        if pd.isna(ma_short) or pd.isna(ma_long):
            return "sideways"
        if ma_short > ma_long and price > ma_short:
            return "trending_up"
        if ma_short < ma_long and price < ma_short:
            return "trending_down"
        return "sideways"

    @staticmethod
    def _combined_label(vol_regime: str, trend_regime: str) -> str:
        if trend_regime == "trending_up":
            if vol_regime == "high_vol":
                return "bull_high_vol"
            return "bull_low_vol"
        if trend_regime == "trending_down":
            return "bear"
        return "sideways"
