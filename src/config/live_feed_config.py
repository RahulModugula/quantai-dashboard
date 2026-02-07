"""Configuration settings for the live data feed module."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class LiveFeedSettings(BaseSettings):
    """Pydantic Settings for the Alpaca / yfinance live feed.

    All fields can be overridden via environment variables (no prefix required)
    or a ``.env`` file in the project root.

    Example ``.env``::

        ALPACA_API_KEY=PKxxxxx
        ALPACA_SECRET_KEY=xxxxx
        ALPACA_FEED=sip
    """

    alpaca_api_key: str = ""
    alpaca_secret_key: str = ""
    alpaca_feed: str = "iex"
    live_feed_reconnect_delay: float = 5.0
    live_feed_max_retries: int = 10
    live_feed_queue_size: int = 100

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


live_feed_settings = LiveFeedSettings()
