from dataclasses import dataclass
from enum import Enum


class SignalType(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass
class Signal:
    ticker: str
    signal_type: SignalType
    probability_up: float
    confidence: float
    suggested_shares: float = 0.0


def generate_signal(
    ticker: str,
    probability_up: float,
    portfolio_value: float,
    current_price: float,
    has_position: bool,
    buy_threshold: float = 0.6,
    sell_threshold: float = 0.4,
    max_position_pct: float = 0.10,
) -> Signal:
    """
    Convert a model probability into a trading signal.

    Args:
        probability_up: Model's P(next day price up)
        has_position: Whether we currently hold this ticker
        buy_threshold: Minimum probability to trigger a buy
        sell_threshold: Maximum probability before triggering a sell
        max_position_pct: Max fraction of portfolio in a single position
    """
    confidence = abs(probability_up - 0.5) * 2  # Scale [0, 1]

    if probability_up >= buy_threshold and not has_position:
        target_value = portfolio_value * max_position_pct
        shares = target_value / current_price if current_price > 0 else 0
        return Signal(
            ticker=ticker,
            signal_type=SignalType.BUY,
            probability_up=probability_up,
            confidence=confidence,
            suggested_shares=shares,
        )
    elif probability_up <= sell_threshold and has_position:
        return Signal(
            ticker=ticker,
            signal_type=SignalType.SELL,
            probability_up=probability_up,
            confidence=confidence,
            suggested_shares=0.0,
        )
    else:
        return Signal(
            ticker=ticker,
            signal_type=SignalType.HOLD,
            probability_up=probability_up,
            confidence=confidence,
            suggested_shares=0.0,
        )
