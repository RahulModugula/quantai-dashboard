"""Portfolio risk assessment and warnings for traders."""

import logging

logger = logging.getLogger(__name__)


def concentration_warning(positions: dict, threshold: float = 0.25) -> list[str]:
    """Warn if any single position exceeds concentration threshold.

    Args:
        positions: {ticker: Position} dict
        threshold: Max allowed position weight (default 25%)

    Returns:
        List of warning messages.
    """
    warnings = []
    if not positions:
        return warnings

    total_value = sum(p.cost_basis for p in positions.values())
    if total_value == 0:
        return warnings

    for ticker, pos in positions.items():
        weight = pos.cost_basis / total_value
        if weight > threshold:
            warnings.append(
                f"⚠️  {ticker} is {weight * 100:.1f}% of portfolio "
                f"(threshold: {threshold * 100:.0f}%). Consider taking profits or diversifying."
            )

    return warnings


def correlation_risk_warning(positions: dict, correlation_matrix: dict) -> list[str]:
    """Warn if portfolio holds highly correlated assets.

    Args:
        positions: {ticker: Position} dict
        correlation_matrix: {ticker: {ticker: corr}} from compute_correlation_matrix

    Returns:
        List of warning messages.
    """
    warnings = []
    if len(positions) < 2:
        return warnings

    held_tickers = list(positions.keys())
    for i, t1 in enumerate(held_tickers):
        for t2 in held_tickers[i + 1 :]:
            if t1 not in correlation_matrix or t2 not in correlation_matrix[t1]:
                continue

            corr = correlation_matrix[t1].get(t2, 0)
            if abs(corr) > 0.80:
                warnings.append(
                    f"⚠️  {t1} and {t2} are highly correlated ({corr:.2f}). "
                    f"This pair reduces diversification benefit."
                )

    return warnings


def drawdown_warning(current_dd: float, limit: float) -> list[str]:
    """Warn if approaching drawdown limit.

    Args:
        current_dd: Current drawdown (negative value, e.g., -0.15 for 15% DD)
        limit: Drawdown limit (e.g., 0.20 for 20%)

    Returns:
        List of warning messages.
    """
    warnings = []
    dd_pct = abs(current_dd) * 100
    limit_pct = limit * 100

    if dd_pct > limit_pct * 0.7:  # 70% of limit
        warnings.append(
            f"⚠️  Drawdown at {dd_pct:.1f}% (limit: {limit_pct:.0f}%). "
            f"Position sizing will reduce if limit is breached."
        )

    return warnings


def get_all_warnings(portfolio_obj, correlation_matrix: dict = None) -> dict:
    """Generate all risk warnings for a portfolio.

    Args:
        portfolio_obj: Portfolio instance
        correlation_matrix: Optional correlation dict

    Returns:
        {"concentration": [...], "correlation": [...], "drawdown": [...]}
    """
    warnings = {
        "concentration": concentration_warning(portfolio_obj.positions),
        "correlation": (
            correlation_risk_warning(portfolio_obj.positions, correlation_matrix)
            if correlation_matrix
            else []
        ),
        "drawdown": drawdown_warning(
            portfolio_obj.current_drawdown({}),
            portfolio_obj.max_drawdown_limit,
        ),
    }

    # Flatten for logging
    all_warnings = [w for ws in warnings.values() for w in ws]
    for w in all_warnings:
        logger.warning(w)

    return warnings
