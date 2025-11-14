"""Input validation and sanitization utilities."""
import re
from datetime import datetime


def validate_ticker(ticker: str) -> bool:
    """Validate stock ticker format. Must be 1-5 uppercase letters."""
    if not ticker or len(ticker) > 5:
        return False
    return bool(re.match(r"^[A-Z]+$", ticker))


def validate_date_format(date_str: str) -> bool:
    """Validate ISO date format (YYYY-MM-DD) with actual date validity."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validate_positive_number(value: float) -> bool:
    """Check if value is positive."""
    return isinstance(value, (int, float)) and value > 0


def validate_percentage(value: float) -> bool:
    """Check if value is valid percentage (0-1)."""
    return isinstance(value, (int, float)) and 0 <= value <= 1


def sanitize_ticker(ticker: str) -> str:
    """Convert ticker to uppercase and strip whitespace."""
    return ticker.strip().upper()


def sanitize_float(value) -> float:
    """Convert to float, return 0 on error."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0
