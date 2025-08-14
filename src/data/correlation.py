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
