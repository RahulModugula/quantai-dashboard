"""Cross-asset correlation analysis for portfolio diversification."""

import pandas as pd

from src.data.storage import load_ohlcv


def compute_correlation_matrix(
    tickers: list[str],
    period: int = 252,
    db_path: str | None = None,
) -> pd.DataFrame:
    """Compute pairwise return correlations for a list of tickers.

    Args:
        tickers: List of ticker symbols
        period: Number of trailing trading days to use
        db_path: Optional database path override

    Returns:
        Correlation matrix as a DataFrame
    """
    returns = {}
    for ticker in tickers:
        df = load_ohlcv(ticker, db_path=db_path)
        if df.empty:
            continue
        close = df.set_index("date")["close"].sort_index().tail(period)
        returns[ticker] = close.pct_change().dropna()

    if not returns:
        return pd.DataFrame()

    returns_df = pd.DataFrame(returns).dropna()
    return returns_df.corr().round(4)


def high_correlation_pairs(
    corr_matrix: pd.DataFrame,
    threshold: float = 0.80,
) -> list[dict]:
    """Return ticker pairs with absolute correlation above threshold.

    Useful for identifying concentration risk — highly correlated assets
    don't provide meaningful diversification.
    """
    pairs = []
    tickers = corr_matrix.columns.tolist()
    for i, t1 in enumerate(tickers):
        for t2 in tickers[i + 1 :]:
            val = corr_matrix.loc[t1, t2]
            if abs(val) >= threshold:
                pairs.append(
                    {
                        "ticker_a": t1,
                        "ticker_b": t2,
                        "correlation": round(float(val), 4),
                    }
                )
    return sorted(pairs, key=lambda x: abs(x["correlation"]), reverse=True)


def correlation_to_dict(corr_matrix: pd.DataFrame) -> dict:
    """Serialize a correlation DataFrame to a JSON-friendly dict."""
    if corr_matrix.empty:
        return {"tickers": [], "matrix": []}
    return {
        "tickers": corr_matrix.columns.tolist(),
        "matrix": [[round(float(v), 4) for v in row] for row in corr_matrix.values],
    }
