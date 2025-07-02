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


def kelly_fraction(win_prob: float, win_loss_ratio: float = 1.5, fraction: float = 0.5) -> float:
    """Half-Kelly position sizing.

    Args:
        win_prob: probability of winning trade
        win_loss_ratio: average win / average loss
        fraction: Kelly fraction (0.5 = half-Kelly for safety)
    """
    q = 1 - win_prob
    if win_loss_ratio <= 0:
        return 0.0
    kelly = (win_prob * win_loss_ratio - q) / win_loss_ratio
    return max(0.0, kelly * fraction)


def generate_signal(
    ticker: str,
    probability_up: float,
    portfolio_value: float,
    current_price: float,
    has_position: bool,
    buy_threshold: float = 0.6,
    sell_threshold: float = 0.4,
    max_position_pct: float = 0.10,
    use_kelly: bool = True,
) -> Signal:
    """
    Convert a model probability into a trading signal.

    Uses half-Kelly criterion for position sizing when use_kelly is True,
    falling back to fixed max_position_pct otherwise.

    Args:
        probability_up: Model's P(next day price up)
        has_position: Whether we currently hold this ticker
        buy_threshold: Minimum probability to trigger a buy
        sell_threshold: Maximum probability before triggering a sell
        max_position_pct: Max fraction of portfolio in a single position
        use_kelly: Whether to use Kelly criterion for sizing
    """
    confidence = round(abs(probability_up - 0.5) * 2, 4)  # Scale to [0, 1]

    if probability_up >= buy_threshold and not has_position:
        if use_kelly:
            position_pct = min(kelly_fraction(probability_up), max_position_pct)
        else:
            position_pct = max_position_pct
        target_value = portfolio_value * position_pct
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
