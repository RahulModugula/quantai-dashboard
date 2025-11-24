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
    multiplier = 10**places
    return int(value * multiplier) / multiplier


def format_number(value: float, decimals: int = 2) -> str:
    """Format number with thousand separators."""
    return f"{value:,.{decimals}f}"


def format_file_size(bytes_size: int) -> str:
    """Format file size."""
    units = ["B", "KB", "MB", "GB", "TB"]

    size = float(bytes_size)
    unit_index = 0

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    return f"{size:.2f} {units[unit_index]}"


def format_time_delta(seconds: float) -> str:
    """Format time delta."""
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"

    if seconds < 60:
        return f"{seconds:.1f}s"

    if seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"

    hours = seconds / 3600
    return f"{hours:.1f}h"
