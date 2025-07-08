from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Data
    tickers: list[str] = ["AAPL", "MSFT", "GOOGL", "AMZN", "SPY"]
    lookback_years: int = 5
    db_path: str = "data/trading.db"

    # Model
    walk_forward_window: int = 252
    retrain_interval: int = 63
    ensemble_weights: dict = {"rf": 0.3, "xgb": 0.3, "lgbm": 0.25, "lstm": 0.15}
    sequence_length: int = 20

    # Trading
    initial_capital: float = 100_000.0
    max_position_pct: float = 0.10
    commission_pct: float = 0.001
    buy_threshold: float = 0.6
    sell_threshold: float = 0.4

    # API
    redis_url: str = "redis://localhost:6379"
    ws_update_interval: float = 2.0
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # SIP / Advisor defaults
    default_inflation_rate: float = 0.06
    default_tax_rate: float = 0.30

    @field_validator("buy_threshold")
    @classmethod
    def buy_threshold_range(cls, v):
        if not 0.5 <= v <= 1.0:
            raise ValueError("buy_threshold must be between 0.5 and 1.0")
        return v

    @field_validator("sell_threshold")
    @classmethod
    def sell_threshold_range(cls, v):
        if not 0.0 <= v <= 0.5:
            raise ValueError("sell_threshold must be between 0.0 and 0.5")
        return v

    @field_validator("max_position_pct")
    @classmethod
    def position_pct_range(cls, v):
        if not 0.01 <= v <= 1.0:
            raise ValueError("max_position_pct must be between 0.01 and 1.0")
        return v

    @field_validator("initial_capital")
    @classmethod
    def capital_positive(cls, v):
        if v <= 0:
            raise ValueError("initial_capital must be positive")
        return v

    # Pydantic-settings config
    model_config = {"env_prefix": "QUANTAI_", "env_file": ".env", "extra": "ignore"}


settings = Settings()
