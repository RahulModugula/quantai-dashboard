"""Advanced position sizing strategies."""
import logging
import math

logger = logging.getLogger(__name__)


def kelly_criterion(win_rate: float, avg_win: float, avg_loss: float) -> float:
    """Calculate Kelly Criterion position size.

    Formula: (p * b - q) / b
    where p = win rate, q = loss rate, b = win/loss ratio

    Args:
        win_rate: Fraction of winning trades (0-1)
        avg_win: Average profit per win
        avg_loss: Average loss per loss (positive value)

    Returns:
        Fraction of bankroll to risk per trade (0-1)
    """
    if avg_loss == 0 or win_rate == 0:
        return 0.0

    loss_rate = 1 - win_rate
    ratio = avg_win / avg_loss

    kelly = (win_rate * ratio - loss_rate) / ratio

    # Fractional Kelly (more conservative)
    fractional = kelly * 0.25  # Use 25% of Kelly

    return max(0, min(0.2, fractional))  # Cap at 20%


def volatility_adjusted_position(
    portfolio_value: float,
    max_loss_pct: float,
    volatility: float,
) -> float:
    """Calculate position size based on volatility.

    More volatile stocks get smaller positions.

    Args:
        portfolio_value: Total portfolio value
        max_loss_pct: Maximum acceptable loss (e.g., 0.02 for 2%)
        volatility: Annualized volatility (0-1)

    Returns:
        Position size in dollars
    """
    if volatility == 0:
        return portfolio_value * max_loss_pct

    # Higher volatility → smaller position
    volatility_factor = 1 / (1 + volatility)
    position = portfolio_value * max_loss_pct * volatility_factor

    return position


def diversification_adjusted_size(
    portfolio_value: float,
    num_positions: int,
    target_correlation: float = 0.0,
) -> float:
    """Calculate position size based on diversification.

    More positions → smaller individual positions.

    Args:
        portfolio_value: Total portfolio value
        num_positions: Number of open positions
        target_correlation: Target average correlation

    Returns:
        Suggested position size per holding
    """
    if num_positions == 0:
        return 0

    base_size = portfolio_value / num_positions

    # Reduce if correlation is high
    correlation_penalty = 1 - (target_correlation * 0.5)  # Reduce by up to 50%

    return base_size * correlation_penalty


def pyramid_position_sizes(
    portfolio_value: float,
    num_tranches: int = 3,
    first_tranche_pct: float = 0.3,
) -> list[float]:
    """Generate pyramid position sizes (scale in gradually).

    Args:
        portfolio_value: Total portfolio value
        num_tranches: Number of purchase tranches
        first_tranche_pct: Size of first tranche as % of total

    Returns:
        List of position sizes for each tranche
    """
    sizes = []
    remaining_pct = first_tranche_pct

    for i in range(num_tranches):
        tranche_size = portfolio_value * remaining_pct
        sizes.append(tranche_size)
        remaining_pct *= 0.7  # Each subsequent tranche is 70% of previous

    return sizes
