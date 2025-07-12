import pandas as pd
import pytest

from src.data.storage import (
    get_engine,
    init_db,
    load_ohlcv,
    load_trades,
    save_ohlcv,
    save_trades,
)


@pytest.fixture
def db_engine(tmp_db):
    engine = init_db(tmp_db)
    return engine


def test_save_and_load_ohlcv(tmp_db, sample_ohlcv):
    init_db(tmp_db)
    save_ohlcv(sample_ohlcv, db_path=tmp_db)
    loaded = load_ohlcv("TEST", db_path=tmp_db)
    assert len(loaded) == len(sample_ohlcv)
    assert loaded["ticker"].iloc[0] == "TEST"


def test_load_ohlcv_date_filter(tmp_db, sample_ohlcv):
    init_db(tmp_db)
    save_ohlcv(sample_ohlcv, db_path=tmp_db)
    loaded = load_ohlcv("TEST", start="2023-06-01", db_path=tmp_db)
    assert len(loaded) < len(sample_ohlcv)


def test_load_ohlcv_missing_ticker(tmp_db):
    init_db(tmp_db)
    loaded = load_ohlcv("MISSING", db_path=tmp_db)
    assert loaded.empty


def test_save_and_load_trades(tmp_db):
    init_db(tmp_db)
    trades = pd.DataFrame([{
        "timestamp": "2023-06-01 10:00:00",
        "ticker": "AAPL",
        "side": "buy",
        "shares": 10.0,
        "price": 185.0,
        "commission": 1.85,
        "pnl": None,
    }])
    save_trades(trades, db_path=tmp_db)
    loaded = load_trades(ticker="AAPL", db_path=tmp_db)
    assert len(loaded) == 1
    assert loaded["ticker"].iloc[0] == "AAPL"


def test_load_trades_no_filter(tmp_db):
    init_db(tmp_db)
    trades = pd.DataFrame([
        {"timestamp": "2023-06-01", "ticker": "AAPL", "side": "buy",
         "shares": 10, "price": 185, "commission": 1.85, "pnl": None},
        {"timestamp": "2023-06-02", "ticker": "MSFT", "side": "buy",
         "shares": 5, "price": 340, "commission": 1.70, "pnl": None},
    ])
    save_trades(trades, db_path=tmp_db)
    loaded = load_trades(db_path=tmp_db)
    assert len(loaded) == 2
