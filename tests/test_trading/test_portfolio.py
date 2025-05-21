from datetime import datetime

import pytest

from src.trading.portfolio import Portfolio


@pytest.fixture
def portfolio():
    return Portfolio(initial_capital=100_000.0, commission_pct=0.001)


def test_initial_state(portfolio):
    assert portfolio.cash == 100_000.0
    assert len(portfolio.positions) == 0
    assert len(portfolio.trade_history) == 0


def test_buy_reduces_cash(portfolio):
    portfolio.buy("AAPL", shares=10, price=200.0, timestamp=datetime.now())
    expected_cost = 10 * 200 * (1 + 0.001)
    assert portfolio.cash == pytest.approx(100_000 - expected_cost, rel=1e-5)


def test_buy_creates_position(portfolio):
    portfolio.buy("AAPL", shares=10, price=200.0)
    assert "AAPL" in portfolio.positions
    assert portfolio.positions["AAPL"].shares == 10.0


def test_sell_removes_position(portfolio):
    portfolio.buy("AAPL", shares=10, price=200.0)
    portfolio.sell("AAPL", shares=10, price=210.0)
    assert "AAPL" not in portfolio.positions


def test_sell_realizes_pnl(portfolio):
    portfolio.buy("AAPL", shares=10, price=200.0)
    trade = portfolio.sell("AAPL", shares=10, price=210.0)
    assert trade is not None
    assert trade.pnl > 0  # Sold higher than bought


def test_get_value(portfolio):
    portfolio.buy("AAPL", shares=10, price=200.0)
    value = portfolio.get_value({"AAPL": 220.0})
    assert value > portfolio.initial_capital  # Position has gained


def test_insufficient_cash(portfolio):
    result = portfolio.buy("AAPL", shares=1000, price=200.0)  # Would cost $200k
    assert result is None
    assert len(portfolio.positions) == 0


def test_snapshot(portfolio):
    snap = portfolio.snapshot({"AAPL": 200.0})
    assert "total_value" in snap
    assert snap["total_value"] == pytest.approx(100_000.0, rel=1e-5)


def test_sell_without_position(portfolio):
    result = portfolio.sell("AAPL", shares=5, price=200.0)
    assert result is None
