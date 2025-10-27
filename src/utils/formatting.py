"""Utility functions for formatting numbers and data for API responses."""


def format_currency(value: float, precision: int = 2) -> str:
    """Format number as currency string."""
    return f"${value:,.{precision}f}"


def format_percentage(value: float, precision: int = 2) -> str:
    """Format decimal as percentage string."""
    return f"{value * 100:.{precision}f}%"


def format_price(value: float, precision: int = 2) -> str:
    """Format stock price."""
    return f"{value:.{precision}f}"


def round_portfolio_value(value: float) -> float:
    """Round portfolio value to nearest cent."""
    return round(value, 2)


def truncate_decimals(value: float, places: int = 2) -> float:
    """Truncate (not round) to specific decimal places."""
    multiplier = 10 ** places
    return int(value * multiplier) / multiplier
