"""Date and time utilities for trading applications."""
from datetime import datetime, timedelta


def trading_days_between(start: str, end: str) -> int:
    """Count trading days between two dates (rough estimate).

    Excludes weekends but includes holidays (simplified).

    Args:
        start: Start date as YYYY-MM-DD
        end: End date as YYYY-MM-DD

    Returns:
        Number of trading days
    """
    start_date = datetime.strptime(start, "%Y-%m-%d")
    end_date = datetime.strptime(end, "%Y-%m-%d")

    days = 0
    current = start_date

    while current <= end_date:
        # 0=Monday, 6=Sunday
        if current.weekday() < 5:  # Monday-Friday
            days += 1
        current += timedelta(days=1)

    return days


def is_market_open(dt: datetime) -> bool:
    """Check if US market is open at given time (simplified).

    Assumes US market hours: 9:30 AM - 4:00 PM ET, Monday-Friday.

    Args:
        dt: Datetime to check

    Returns:
        True if market is open
    """
    if dt.weekday() >= 5:  # Weekend
        return False

    hour = dt.hour
    minute = dt.minute

    # 9:30 AM - 4:00 PM
    open_time = (9, 30)
    close_time = (16, 0)

    current_time = (hour, minute)

    return open_time <= current_time < close_time


def next_market_open(dt: datetime) -> datetime:
    """Calculate next market open time.

    Args:
        dt: Current datetime

    Returns:
        Next market open datetime
    """
    # Start from next day
    next_day = dt + timedelta(days=1)

    # Find next weekday
    while next_day.weekday() >= 5:
        next_day += timedelta(days=1)

    # Set to market open time (9:30 AM)
    return next_day.replace(hour=9, minute=30, second=0, microsecond=0)


def years_since(date_str: str) -> float:
    """Calculate years elapsed since a date.

    Args:
        date_str: Date as YYYY-MM-DD

    Returns:
        Years as float
    """
    past = datetime.strptime(date_str, "%Y-%m-%d")
    now = datetime.now()

    days = (now - past).days
    years = days / 365.25  # Account for leap years

    return years
