import pytest

from src.data.schemas import BacktestRequestSchema


def test_backtest_request_schema_valid():
    """Test valid backtest request."""
    req = BacktestRequestSchema(
        ticker="AAPL",
        initial_capital=100_000.0,
        buy_threshold=0.6,
        sell_threshold=0.4,
    )
    assert req.ticker == "AAPL"
    assert req.initial_capital == 100_000.0
    assert req.buy_threshold == 0.6
    assert req.sell_threshold == 0.4


def test_backtest_request_schema_invalid_threshold():
    """Test invalid threshold values."""
    with pytest.raises(ValueError):
        BacktestRequestSchema(
            ticker="AAPL",
            initial_capital=100_000.0,
            buy_threshold=1.5,  # > 1.0
            sell_threshold=0.4,
        )

    with pytest.raises(ValueError):
        BacktestRequestSchema(
            ticker="AAPL",
            initial_capital=100_000.0,
            buy_threshold=0.6,
            sell_threshold=-0.1,  # < 0.0
        )


def test_backtest_request_schema_invalid_capital():
    """Test invalid capital values."""
    with pytest.raises(ValueError):
        BacktestRequestSchema(
            ticker="AAPL",
            initial_capital=-1000.0,  # Negative
            buy_threshold=0.6,
            sell_threshold=0.4,
        )

    with pytest.raises(ValueError):
        BacktestRequestSchema(
            ticker="AAPL",
            initial_capital=0.0,  # Zero
            buy_threshold=0.6,
            sell_threshold=0.4,
        )
