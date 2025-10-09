"""Tests for Portfolio computed properties."""
from datetime import datetime
import pytest

from src.trading.portfolio import Portfolio


@pytest.fixture
def portfolio():
    return Portfolio(initial_capital=100_000.0, commission_pct=0.001)


def test_realized_pnl_empty(portfolio):
    assert portfolio.realized_pnl_total == 0.0


def test_total_commissions_empty(portfolio):
    assert portfolio.total_commissions == 0.0


def test_total_trades_count_empty(portfolio):
    assert portfolio.total_trades_count == 0


def test_realized_pnl_after_round_trip(portfolio):
    portfolio.buy("AAPL", 10, 150.0, datetime(2023, 1, 1))
    portfolio.sell("AAPL", 10, 160.0, datetime(2023, 2, 1))
    # pnl = (160 - 150) * 10 - commission_on_sell
    assert portfolio.realized_pnl_total > 0
    assert portfolio.total_trades_count == 1


def test_total_commissions_accumulate(portfolio):
    portfolio.buy("AAPL", 10, 150.0, datetime(2023, 1, 1))
    portfolio.sell("AAPL", 10, 160.0, datetime(2023, 2, 1))
    portfolio.buy("MSFT", 5, 300.0, datetime(2023, 3, 1))
    # commission on all 3 trades
    assert portfolio.total_commissions > 0
    assert portfolio.total_commissions == pytest.approx(
        (10 * 150.0 * 0.001) + (10 * 160.0 * 0.001) + (5 * 300.0 * 0.001),
        rel=1e-4,
    )


def test_total_trades_count_only_sells(portfolio):
    portfolio.buy("AAPL", 10, 150.0)
    portfolio.buy("MSFT", 5, 200.0)
    assert portfolio.total_trades_count == 0  # No sells yet

    portfolio.sell("AAPL", 10, 160.0)
    assert portfolio.total_trades_count == 1
