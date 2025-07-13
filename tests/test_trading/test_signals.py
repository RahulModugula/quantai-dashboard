import pytest

from src.trading.signals import SignalType, generate_signal, kelly_fraction


def test_buy_signal_above_threshold():
    signal = generate_signal(
        ticker="AAPL", probability_up=0.75, portfolio_value=100_000,
        current_price=200, has_position=False, use_kelly=False,
    )
    assert signal.signal_type == SignalType.BUY
    assert signal.suggested_shares > 0


def test_sell_signal_below_threshold():
    signal = generate_signal(
        ticker="AAPL", probability_up=0.3, portfolio_value=100_000,
        current_price=200, has_position=True,
    )
    assert signal.signal_type == SignalType.SELL


def test_hold_signal_in_between():
    signal = generate_signal(
        ticker="AAPL", probability_up=0.55, portfolio_value=100_000,
        current_price=200, has_position=False,
    )
    assert signal.signal_type == SignalType.HOLD


def test_no_buy_when_already_holding():
    signal = generate_signal(
        ticker="AAPL", probability_up=0.8, portfolio_value=100_000,
        current_price=200, has_position=True,
    )
    assert signal.signal_type == SignalType.HOLD


def test_kelly_fraction_positive():
    frac = kelly_fraction(0.7, win_loss_ratio=1.5)
    assert frac > 0
    assert frac <= 0.5  # half-Kelly caps it


def test_kelly_fraction_zero_for_low_prob():
    frac = kelly_fraction(0.3, win_loss_ratio=1.0)
    assert frac == 0.0


def test_kelly_sizing_smaller_for_lower_prob():
    signal_high = generate_signal(
        ticker="AAPL", probability_up=0.85, portfolio_value=100_000,
        current_price=200, has_position=False, use_kelly=True,
    )
    signal_low = generate_signal(
        ticker="AAPL", probability_up=0.62, portfolio_value=100_000,
        current_price=200, has_position=False, use_kelly=True,
    )
    assert signal_high.suggested_shares >= signal_low.suggested_shares


def test_confidence_scale():
    signal = generate_signal(
        ticker="AAPL", probability_up=0.8, portfolio_value=100_000,
        current_price=200, has_position=False,
    )
    assert 0 <= signal.confidence <= 1.0
    assert signal.confidence == pytest.approx(0.6, abs=0.01)
