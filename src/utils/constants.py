"""Application constants and configuration values."""

# Trading constants
MIN_POSITION_SIZE = 100  # Minimum dollar amount per position
MAX_POSITION_SIZE = 1000000  # Maximum dollar amount per position
MIN_CASH_BUFFER = 1000  # Minimum cash to maintain

# Signal thresholds
BUY_SIGNAL_THRESHOLD = 0.60
SELL_SIGNAL_THRESHOLD = 0.40
STRONG_SIGNAL_THRESHOLD = 0.75

# Risk management
DEFAULT_MAX_DRAWDOWN = 0.20  # 20%
DEFAULT_MAX_POSITION_PCT = 0.30  # 30% of portfolio
KELLY_FRACTION = 0.25  # Use 25% of Kelly criterion

# Time constants
TRADING_DAYS_PER_YEAR = 252
TRADING_HOURS_PER_DAY = 6.5
MARKET_OPEN_HOUR = 9
MARKET_CLOSE_HOUR = 16

# Data constants
MIN_LOOKBACK_DAYS = 252  # Minimum 1 year of data
DEFAULT_LOOKBACK_DAYS = 500
FEATURE_WINDOW_DAYS = 20

# Cache constants
DEFAULT_CACHE_TTL = 300  # 5 minutes
LONG_CACHE_TTL = 3600  # 1 hour

# API constants
DEFAULT_PAGE_SIZE = 100
MAX_PAGE_SIZE = 1000
DEFAULT_RATE_LIMIT = 1000  # per hour
