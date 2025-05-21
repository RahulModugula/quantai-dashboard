import numpy as np
import pandas as pd
import pytest

from src.backtest.metrics import (
    calmar_ratio,
    max_drawdown,
    profit_factor,
    sharpe_ratio,
    sortino_ratio,
    win_rate,
)


@pytest.fixture
def flat_returns():
    return pd.Series([0.001] * 252)


@pytest.fixture
def equity_up():
    return pd.Series([100 * (1.001 ** i) for i in range(252)])


@pytest.fixture
def equity_down():
    return pd.Series([100 * (0.999 ** i) for i in range(252)])


@pytest.fixture
def mixed_trades():
    return pd.DataFrame({
        "pnl": [100, -50, 200, -30, 150, -20, 80]
    })


def test_sharpe_positive_returns(flat_returns):
    sr = sharpe_ratio(flat_returns)
    assert sr > 0


def test_sharpe_zero_std():
    returns = pd.Series([0.0] * 100)
    assert sharpe_ratio(returns) == 0.0


def test_sortino_only_downside():
    returns = pd.Series([-0.01] * 50)
    sr = sortino_ratio(returns)
    assert sr < 0


def test_max_drawdown_no_loss(equity_up):
    mdd = max_drawdown(equity_up)
    assert mdd == pytest.approx(0.0, abs=1e-4)


def test_max_drawdown_all_loss(equity_down):
    mdd = max_drawdown(equity_down)
    assert mdd < 0


def test_max_drawdown_known_value():
    # Equity drops 20% from 100 to 80
    equity = pd.Series([100, 90, 80, 85, 95, 100])
    mdd = max_drawdown(equity)
    assert mdd == pytest.approx(-0.20, abs=0.01)


def test_win_rate(mixed_trades):
    wr = win_rate(mixed_trades)
    # 4 winners out of 7
    assert wr == pytest.approx(4 / 7, abs=0.01)


def test_win_rate_empty_trades():
    assert win_rate(pd.DataFrame()) == 0.0


def test_profit_factor(mixed_trades):
    pf = profit_factor(mixed_trades)
    gross_profit = 100 + 200 + 150 + 80
    gross_loss = 50 + 30 + 20
    assert pf == pytest.approx(gross_profit / gross_loss, abs=0.01)


def test_calmar_ratio(equity_up):
    returns = equity_up.pct_change().dropna()
    cr = calmar_ratio(returns, equity_up)
    # With consistently rising equity, calmar should be positive
    assert cr > 0
