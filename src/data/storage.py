import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    text,
)

from src.config import settings

logger = logging.getLogger(__name__)

metadata = MetaData()

ohlcv_table = Table(
    "ohlcv",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("date", DateTime, nullable=False),
    Column("ticker", String, nullable=False),
    Column("open", Float),
    Column("high", Float),
    Column("low", Float),
    Column("close", Float),
    Column("volume", Integer),
)

features_table = Table(
    "features",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("date", DateTime, nullable=False),
    Column("ticker", String, nullable=False),
    Column("rsi_14", Float),
    Column("macd", Float),
    Column("macd_signal", Float),
    Column("macd_hist", Float),
    Column("bb_upper", Float),
    Column("bb_middle", Float),
    Column("bb_lower", Float),
    Column("bb_pct_b", Float),
    Column("bb_bandwidth", Float),
    Column("atr_14", Float),
    Column("stoch_k", Float),
    Column("stoch_d", Float),
    Column("adx_14", Float),
    Column("close_to_sma50", Float),
    Column("close_to_sma200", Float),
    Column("sma50_to_sma200", Float),
    Column("return_lag_1", Float),
    Column("return_lag_2", Float),
    Column("return_lag_3", Float),
    Column("return_lag_5", Float),
    Column("volatility_5", Float),
    Column("volatility_20", Float),
    Column("momentum_5", Float),
    Column("momentum_20", Float),
    Column("mean_reversion_20", Float),
    Column("volume_ratio", Float),
    Column("obv", Float),
    Column("target", Integer),
)

trades_table = Table(
    "trades",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("timestamp", DateTime, nullable=False),
    Column("ticker", String, nullable=False),
    Column("side", String, nullable=False),
    Column("shares", Float),
    Column("price", Float),
    Column("commission", Float),
    Column("pnl", Float),
)

portfolio_snapshots_table = Table(
    "portfolio_snapshots",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("timestamp", DateTime, nullable=False),
    Column("total_value", Float),
    Column("cash", Float),
    Column("positions_value", Float),
    Column("daily_return", Float),
    Column("cumulative_return", Float),
)

backtest_results_table = Table(
    "backtest_results",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("ticker", String),
    Column("start_date", DateTime),
    Column("end_date", DateTime),
    Column("initial_capital", Float),
    Column("final_value", Float),
    Column("total_return", Float),
    Column("sharpe_ratio", Float),
    Column("sortino_ratio", Float),
    Column("max_drawdown", Float),
    Column("win_rate", Float),
    Column("total_trades", Integer),
    Column("profit_factor", Float),
    Column("calmar_ratio", Float),
)


def get_engine(db_path: str | None = None):
    path = db_path or settings.db_path
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{path}", echo=False)


def init_db(db_path: str | None = None):
    """Create all tables and indexes if they don't exist (idempotent)."""
    engine = get_engine(db_path)
    metadata.create_all(engine)

    # Create indexes for performance optimization
    with engine.begin() as conn:
        # OHLCV indexes
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS idx_ohlcv_ticker_date ON ohlcv(ticker, date)")
        )

        # Features indexes
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS idx_features_ticker_date ON features(ticker, date)")
        )

        # Trades indexes
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_trades_ticker ON trades(ticker)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)"))

        # Portfolio snapshots indexes
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp ON portfolio_snapshots(timestamp)"
            )
        )

        # Backtest results indexes
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS idx_backtest_ticker ON backtest_results(ticker)")
        )

    logger.info(f"Database initialized at {db_path or settings.db_path}")
    return engine


def save_ohlcv(df: pd.DataFrame, db_path: str | None = None):
    engine = get_engine(db_path)
    ticker = df["ticker"].iloc[0]

    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM ohlcv WHERE ticker = :ticker"),
            {"ticker": ticker},
        )

    df.to_sql("ohlcv", engine, if_exists="append", index=False)
    logger.info(f"Saved {len(df)} OHLCV rows for {ticker}")


def load_ohlcv(
    ticker: str,
    start: str | None = None,
    end: str | None = None,
    db_path: str | None = None,
) -> pd.DataFrame:
    engine = get_engine(db_path)
    query = "SELECT * FROM ohlcv WHERE ticker = :ticker"
    params = {"ticker": ticker}
    if start:
        query += " AND date >= :start"
        params["start"] = start
    if end:
        query += " AND date <= :end"
        params["end"] = end
    query += " ORDER BY date"
    return pd.read_sql(text(query), engine, params=params)


def save_features(df: pd.DataFrame, db_path: str | None = None):
    engine = get_engine(db_path)
    ticker = df["ticker"].iloc[0]

    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM features WHERE ticker = :ticker"),
            {"ticker": ticker},
        )

    # Select only columns that exist in the features table
    table_cols = [c.name for c in features_table.columns if c.name != "id"]
    save_cols = [c for c in table_cols if c in df.columns]
    df[save_cols].to_sql("features", engine, if_exists="append", index=False)
    logger.info(f"Saved {len(df)} feature rows for {ticker}")


def load_features(
    ticker: str,
    start: str | None = None,
    end: str | None = None,
    db_path: str | None = None,
) -> pd.DataFrame:
    engine = get_engine(db_path)
    query = "SELECT * FROM features WHERE ticker = :ticker"
    params = {"ticker": ticker}
    if start:
        query += " AND date >= :start"
        params["start"] = start
    if end:
        query += " AND date <= :end"
        params["end"] = end
    query += " ORDER BY date"
    return pd.read_sql(text(query), engine, params=params)


def save_trades(trades: pd.DataFrame, db_path: str | None = None):
    engine = get_engine(db_path)
    trades.to_sql("trades", engine, if_exists="append", index=False)


def load_trades(
    ticker: str | None = None,
    start: str | None = None,
    end: str | None = None,
    db_path: str | None = None,
) -> pd.DataFrame:
    engine = get_engine(db_path)
    query = "SELECT * FROM trades"
    conditions = []
    params = {}
    if ticker:
        conditions.append("ticker = :ticker")
        params["ticker"] = ticker
    if start:
        conditions.append("timestamp >= :start")
        params["start"] = start
    if end:
        conditions.append("timestamp <= :end")
        params["end"] = end
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY timestamp"
    return pd.read_sql(text(query), engine, params=params)


def save_portfolio_snapshot(snapshot: dict, db_path: str | None = None):
    engine = get_engine(db_path)
    pd.DataFrame([snapshot]).to_sql("portfolio_snapshots", engine, if_exists="append", index=False)


def save_backtest_result(result: dict, db_path: str | None = None):
    engine = get_engine(db_path)
    pd.DataFrame([result]).to_sql("backtest_results", engine, if_exists="append", index=False)
