import json
import logging
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    Text,
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

agent_decisions_table = Table(
    "agent_decisions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("ticker", String(10), nullable=False),
    Column("analysis_id", String(36), nullable=False),
    Column("triggered_at", DateTime, nullable=False),
    Column("completed_at", DateTime),
    Column("status", String(20), nullable=False),
    Column("decision", String(10)),
    Column("confidence", Float),
    Column("reasoning_summary", Text),
    Column("quant_brief", Text),
    Column("news_brief", Text),
    Column("risk_brief", Text),
    Column("pm_brief", Text),
    Column("price_at_decision", Float),
    Column("price_24h_later", Float),
    Column("price_7d_later", Float),
    Column("decision_correct_24h", Boolean),
    Column("decision_correct_7d", Boolean),
    Column("model_used", String(100)),
    Column("total_tokens", Integer),
    Column("error_message", Text),
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

        # Agent decisions indexes
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_agent_ticker ON agent_decisions(ticker)"))
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_agent_triggered_at ON agent_decisions(triggered_at)"
            )
        )
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_agent_analysis_id ON agent_decisions(analysis_id)"
            )
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


# ---------------------------------------------------------------------------
# Agent decision helpers
# ---------------------------------------------------------------------------


def save_agent_decision(record: dict, db_path: str | None = None) -> str:
    """Insert a new agent decision row. Returns the analysis_id."""
    engine = get_engine(db_path)
    analysis_id = record.get("analysis_id", str(uuid4()))
    row = {
        "ticker": record["ticker"],
        "analysis_id": analysis_id,
        "triggered_at": record.get("triggered_at", datetime.utcnow()),
        "completed_at": record.get("completed_at"),
        "status": record.get("status", "pending"),
        "decision": record.get("decision"),
        "confidence": record.get("confidence"),
        "reasoning_summary": record.get("reasoning_summary"),
        "quant_brief": json.dumps(record["quant_brief"]) if "quant_brief" in record else None,
        "news_brief": json.dumps(record["news_brief"]) if "news_brief" in record else None,
        "risk_brief": json.dumps(record["risk_brief"]) if "risk_brief" in record else None,
        "pm_brief": json.dumps(record["pm_brief"]) if "pm_brief" in record else None,
        "price_at_decision": record.get("price_at_decision"),
        "price_24h_later": record.get("price_24h_later"),
        "price_7d_later": record.get("price_7d_later"),
        "decision_correct_24h": record.get("decision_correct_24h"),
        "decision_correct_7d": record.get("decision_correct_7d"),
        "model_used": record.get("model_used"),
        "total_tokens": record.get("total_tokens"),
        "error_message": record.get("error_message"),
    }
    with engine.begin() as conn:
        conn.execute(agent_decisions_table.insert().values(**row))
    return analysis_id


def update_agent_decision(analysis_id: str, updates: dict, db_path: str | None = None) -> None:
    """Patch specific columns on an existing row by analysis_id."""
    engine = get_engine(db_path)
    # Serialize brief dicts to JSON
    for key in ("quant_brief", "news_brief", "risk_brief", "pm_brief"):
        if key in updates and isinstance(updates[key], dict):
            updates[key] = json.dumps(updates[key])
    with engine.begin() as conn:
        conn.execute(
            agent_decisions_table.update()
            .where(agent_decisions_table.c.analysis_id == analysis_id)
            .values(**updates)
        )


def load_agent_decision(analysis_id: str, db_path: str | None = None) -> dict | None:
    """Fetch a single decision by UUID."""
    engine = get_engine(db_path)
    with engine.connect() as conn:
        row = conn.execute(
            agent_decisions_table.select().where(agent_decisions_table.c.analysis_id == analysis_id)
        ).fetchone()
    if row is None:
        return None
    result = dict(row._mapping)
    for key in ("quant_brief", "news_brief", "risk_brief", "pm_brief"):
        if result.get(key):
            try:
                result[key] = json.loads(result[key])
            except (json.JSONDecodeError, TypeError):
                pass
    return result


def load_agent_decisions(ticker: str, limit: int = 50, db_path: str | None = None) -> list[dict]:
    """Fetch recent decisions for a ticker, newest first."""
    engine = get_engine(db_path)
    with engine.connect() as conn:
        rows = conn.execute(
            agent_decisions_table.select()
            .where(agent_decisions_table.c.ticker == ticker.upper())
            .order_by(agent_decisions_table.c.triggered_at.desc())
            .limit(limit)
        ).fetchall()
    results = []
    for row in rows:
        d = dict(row._mapping)
        for key in ("quant_brief", "news_brief", "risk_brief", "pm_brief"):
            if d.get(key):
                try:
                    d[key] = json.loads(d[key])
                except (json.JSONDecodeError, TypeError):
                    pass
        results.append(d)
    return results


def load_agent_accuracy(db_path: str | None = None) -> dict:
    """Aggregate accuracy metrics for completed decisions."""
    engine = get_engine(db_path)
    query = text("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN decision_correct_24h = 1 THEN 1 ELSE 0 END) AS correct_24h,
            SUM(CASE WHEN decision_correct_24h IS NOT NULL THEN 1 ELSE 0 END) AS evaluated_24h,
            SUM(CASE WHEN decision_correct_7d = 1 THEN 1 ELSE 0 END) AS correct_7d,
            SUM(CASE WHEN decision_correct_7d IS NOT NULL THEN 1 ELSE 0 END) AS evaluated_7d,
            SUM(CASE WHEN decision = 'BUY' THEN 1 ELSE 0 END) AS buy_count,
            SUM(CASE WHEN decision = 'SELL' THEN 1 ELSE 0 END) AS sell_count,
            SUM(CASE WHEN decision = 'HOLD' THEN 1 ELSE 0 END) AS hold_count
        FROM agent_decisions
        WHERE status = 'complete'
    """)
    with engine.connect() as conn:
        row = conn.execute(query).fetchone()
    if row is None:
        return {}
    d = dict(row._mapping)
    ev24 = d.get("evaluated_24h") or 0
    ev7 = d.get("evaluated_7d") or 0
    return {
        "total_decisions": d.get("total", 0),
        "accuracy_24h": round(d["correct_24h"] / ev24, 3) if ev24 else None,
        "accuracy_7d": round(d["correct_7d"] / ev7, 3) if ev7 else None,
        "evaluated_24h": ev24,
        "evaluated_7d": ev7,
        "decision_distribution": {
            "buy": d.get("buy_count", 0),
            "sell": d.get("sell_count", 0),
            "hold": d.get("hold_count", 0),
        },
    }
