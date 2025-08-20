"""Market calendar and trading day utilities."""
from datetime import datetime, timedelta


class MarketCalendar:
    """US stock market trading calendar."""

    # US market holidays (simplified)
    HOLIDAYS = [
        "2025-01-01",  # New Year
        "2025-01-20",  # MLK Day
        "2025-02-17",  # Presidents Day
        "2025-03-17",  # Good Friday
        "2025-05-26",  # Memorial Day
        "2025-06-19",  # Juneteenth
        "2025-07-04",  # Independence Day
        "2025-09-01",  # Labor Day
        "2025-11-27",  # Thanksgiving
        "2025-12-25",  # Christmas
    ]

    @classmethod
    def is_trading_day(cls, date: str) -> bool:
        """Check if date is a US market trading day."""
        dt = datetime.strptime(date, "%Y-%m-%d")
        # Weekend check
        if dt.weekday() >= 5:
            return False
        # Holiday check
        return date not in cls.HOLIDAYS

    @classmethod
    def next_trading_day(cls, date: str) -> str:
        """Get next trading day after given date."""
        dt = datetime.strptime(date, "%Y-%m-%d")
        dt += timedelta(days=1)
        while not cls.is_trading_day(dt.strftime("%Y-%m-%d")):
            dt += timedelta(days=1)
        return dt.strftime("%Y-%m-%d")

    @classmethod
    def count_trading_days(cls, start: str, end: str) -> int:
        """Count trading days between two dates."""
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        end_dt = datetime.strptime(end, "%Y-%m-%d")
        count = 0
        current = start_dt
        while current <= end_dt:
            if cls.is_trading_day(current.strftime("%Y-%m-%d")):
                count += 1
            current += timedelta(days=1)
        return count
