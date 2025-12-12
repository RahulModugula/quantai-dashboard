"""Unit tests for volume-weighted slippage models."""

import numpy as np
import pandas as pd

from src.backtest.slippage import NoSlippage, ParticipationRateSlippage, SquareRootImpact
from src.backtest.engine import WalkForwardBacktester


def test_no_slippage_returns_price():
    model = NoSlippage()
    price = 150.0
    assert model.apply(price, 10_000.0, 1_000_000.0, "buy") == price
    assert model.apply(price, 10_000.0, 1_000_000.0, "sell") == price


def test_participation_rate_buy_increases_price():
    model = ParticipationRateSlippage(participation_rate=0.1, impact_per_pct=0.002)
    price = 100.0
    fill = model.apply(price, 50_000.0, 500_000.0, "buy")
    assert fill > price, "Buy fill price should be higher than market price"


def test_participation_rate_sell_decreases_price():
    model = ParticipationRateSlippage(participation_rate=0.1, impact_per_pct=0.002)
    price = 100.0
    fill = model.apply(price, 50_000.0, 500_000.0, "sell")
    assert fill < price, "Sell fill price should be lower than market price"


def test_slippage_clamped_at_max():
    # Use a very large order relative to ADV to trigger the clamp
    model = ParticipationRateSlippage(
        participation_rate=100.0, impact_per_pct=1.0, max_slippage_bps=50.0
    )
    price = 100.0
    fill = model.apply(price, 1_000_000_000.0, 1_000.0, "buy")
    max_allowed = price * (1.0 + 50.0 / 10_000.0)
    assert fill <= max_allowed + 1e-9, f"Slippage not clamped: fill={fill}, max={max_allowed}"


def test_square_root_impact_buy():
    model = SquareRootImpact(volatility=0.02, impact_coeff=0.1)
    price = 200.0
    fill = model.apply(price, 100_000.0, 2_000_000.0, "buy")
    assert fill > price, "SquareRootImpact buy fill should exceed market price"
    # Slippage should be bounded by 50bps
    assert fill <= price * 1.0051


def test_backtester_accepts_slippage_model():
    """WalkForwardBacktester should run end-to-end with a slippage model."""
    np.random.seed(0)
    n = 60
    dates = pd.date_range("2023-01-02", periods=n, freq="B")
    close = 100 * (1 + np.random.randn(n) * 0.01).cumprod()

    prices = pd.DataFrame({"date": dates, "ticker": "TEST", "close": close})

    # Predictions: alternate buy/sell signals
    prob_up = np.where(np.arange(n) % 10 < 5, 0.7, 0.3)
    predictions = pd.DataFrame({"date": dates, "ticker": "TEST", "probability_up": prob_up})

    slippage = ParticipationRateSlippage(participation_rate=0.1, impact_per_pct=0.002)
    bt = WalkForwardBacktester(initial_capital=100_000.0, slippage_model=slippage)
    result = bt.run(predictions, prices)

    assert result.ticker == "TEST"
    assert result.total_slippage_cost >= 0.0
    assert result.final_value > 0
