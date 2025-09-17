import numpy as np
import pandas as pd


def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()

    # Avoid division by zero when avg_loss is 0 (all gains period)
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def compute_macd(
    series: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    """MACD line, signal line, histogram."""
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line

    return pd.DataFrame({
        "macd": macd_line,
        "macd_signal": signal_line,
        "macd_hist": histogram,
    })


def compute_bollinger_bands(
    series: pd.Series,
    period: int = 20,
    num_std: float = 2.0,
) -> pd.DataFrame:
    """Bollinger Bands with %B and bandwidth."""
    middle = series.rolling(window=period).mean()
    rolling_std = series.rolling(window=period).std()

    upper = middle + (num_std * rolling_std)
    lower = middle - (num_std * rolling_std)

    pct_b = (series - lower) / (upper - lower).replace(0, np.nan)
    bandwidth = (upper - lower) / middle.replace(0, np.nan)

    return pd.DataFrame({
        "bb_upper": upper,
        "bb_middle": middle,
        "bb_lower": lower,
        "bb_pct_b": pct_b,
        "bb_bandwidth": bandwidth,
    })


def compute_stochastic(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    k_period: int = 14,
    d_period: int = 3,
) -> pd.DataFrame:
    """Stochastic Oscillator (%K and %D)."""
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    denom = (highest_high - lowest_low).replace(0, np.nan)
    pct_k = 100 * (close - lowest_low) / denom
    pct_d = pct_k.rolling(window=d_period).mean()
    return pd.DataFrame({"stoch_k": pct_k, "stoch_d": pct_d})


def compute_atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> pd.Series:
    """Average True Range."""
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = true_range.ewm(alpha=1 / period, min_periods=period).mean()
    return atr


def compute_adx(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> pd.Series:
    """Average Directional Index — measures trend strength (0-100)."""
    prev_high = high.shift(1)
    prev_low = low.shift(1)
    prev_close = close.shift(1)

    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    plus_dm = np.where((high - prev_high) > (prev_low - low), np.maximum(high - prev_high, 0), 0)
    minus_dm = np.where((prev_low - low) > (high - prev_high), np.maximum(prev_low - low, 0), 0)

    plus_dm = pd.Series(plus_dm, index=high.index)
    minus_dm = pd.Series(minus_dm, index=high.index)

    atr = tr.ewm(alpha=1 / period, min_periods=period).mean()
    plus_di = 100 * plus_dm.ewm(alpha=1 / period, min_periods=period).mean() / atr.replace(0, np.nan)
    minus_di = 100 * minus_dm.ewm(alpha=1 / period, min_periods=period).mean() / atr.replace(0, np.nan)

    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.ewm(alpha=1 / period, min_periods=period).mean()
    return adx


def compute_rolling_stats(df: pd.DataFrame, windows: list[int] = None) -> pd.DataFrame:
    """Rolling volatility, momentum (rate of change), and mean reversion z-score."""
    if windows is None:
        windows = [5, 10, 20, 60]

    returns = df["close"].pct_change()
    result = pd.DataFrame(index=df.index)

    for w in windows:
        result[f"volatility_{w}"] = returns.rolling(window=w).std() * np.sqrt(252)
        result[f"momentum_{w}"] = df["close"].pct_change(periods=w)

        # Mean reversion z-score
        rolling_mean = df["close"].rolling(window=w).mean()
        rolling_std = df["close"].rolling(window=w).std()
        result[f"mean_reversion_{w}"] = (
            (df["close"] - rolling_mean) / rolling_std.replace(0, np.nan)
        )

    return result


def compute_sma_ratios(df: pd.DataFrame) -> pd.DataFrame:
    """Price relative to key moving averages and golden/death cross signal."""
    close = df["close"]
    sma_50 = close.rolling(window=50).mean()
    sma_200 = close.rolling(window=200).mean()

    result = pd.DataFrame(index=df.index)
    result["close_to_sma50"] = close / sma_50.replace(0, np.nan)
    result["close_to_sma200"] = close / sma_200.replace(0, np.nan)
    result["sma50_to_sma200"] = sma_50 / sma_200.replace(0, np.nan)
    return result


def compute_lagged_returns(df: pd.DataFrame, lags: list[int] = None) -> pd.DataFrame:
    """Lagged daily returns as features for autocorrelation capture."""
    if lags is None:
        lags = [1, 2, 3, 5]
    returns = df["close"].pct_change()
    result = pd.DataFrame(index=df.index)
    for lag in lags:
        result[f"return_lag_{lag}"] = returns.shift(lag)
    return result


def compute_volume_features(df: pd.DataFrame) -> pd.DataFrame:
    """Volume ratio, OBV, and VWAP proxy."""
    result = pd.DataFrame(index=df.index)

    # Volume relative to 20-day average
    vol_avg = df["volume"].rolling(window=20).mean()
    result["volume_ratio"] = df["volume"] / vol_avg.replace(0, np.nan)

    # On-Balance Volume
    direction = np.sign(df["close"].diff())
    result["obv"] = (df["volume"] * direction).cumsum()

    # Normalize OBV for comparability
    obv_mean = result["obv"].rolling(window=20).mean()
    obv_std = result["obv"].rolling(window=20).std()
    result["obv_zscore"] = (result["obv"] - obv_mean) / obv_std.replace(0, np.nan)

    return result


def build_feature_matrix(df: pd.DataFrame, min_rows: int = 60) -> pd.DataFrame:
    """Build complete feature matrix from OHLCV data.

    Returns a clean dataframe with all features and a binary target
    (1 = next day close is higher, 0 = lower).

    Args:
        df: OHLCV dataframe
        min_rows: Minimum rows required after warmup; raises if data is too short
    """
    if len(df) < min_rows:
        raise ValueError(
            f"Insufficient history: need at least {min_rows} rows, got {len(df)}"
        )

    features = df[["date", "ticker", "open", "high", "low", "close", "volume"]].copy()

    # Technical indicators
    features["rsi_14"] = compute_rsi(df["close"])

    macd_df = compute_macd(df["close"])
    features = pd.concat([features, macd_df], axis=1)

    bb_df = compute_bollinger_bands(df["close"])
    features = pd.concat([features, bb_df], axis=1)

    features["atr_14"] = compute_atr(df["high"], df["low"], df["close"])

    stoch_df = compute_stochastic(df["high"], df["low"], df["close"])
    features = pd.concat([features, stoch_df], axis=1)

    features["adx_14"] = compute_adx(df["high"], df["low"], df["close"])

    # Rolling statistics
    rolling_df = compute_rolling_stats(df, windows=[5, 20])
    features = pd.concat([features, rolling_df], axis=1)

    # SMA ratios
    sma_df = compute_sma_ratios(df)
    features = pd.concat([features, sma_df], axis=1)

    # Lagged returns
    lag_df = compute_lagged_returns(df)
    features = pd.concat([features, lag_df], axis=1)

    # Volume features
    vol_df = compute_volume_features(df)
    features = pd.concat([features, vol_df], axis=1)

    # Macro features (VIX) if available in the data
    # These must be merged externally before calling build_feature_matrix
    if "vix_close" in df.columns:
        features["vix_close"] = df["vix_close"]
        vix_ma = df["vix_close"].rolling(window=20).mean()
        features["vix_regime"] = (df["vix_close"] > vix_ma).astype(int)

    # Target: next-day return direction
    features["target"] = (df["close"].shift(-1) > df["close"]).astype(int)

    # Drop rows with NaN from indicator warmup periods
    features = features.dropna().reset_index(drop=True)

    # Drop the last row since it has no valid target
    features = features.iloc[:-1]

    return features
