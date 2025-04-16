from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Data
    tickers: list[str] = ["AAPL", "MSFT", "GOOGL", "AMZN", "SPY"]
    lookback_years: int = 5
    db_path: str = "data/trading.db"

    # Model
    walk_forward_window: int = 252
    retrain_interval: int = 63
    ensemble_weights: dict = {"rf": 0.4, "xgb": 0.4, "lstm": 0.2}
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

    # Pydantic-settings config
    model_config = {"env_prefix": "QUANTAI_", "env_file": ".env", "extra": "ignore"}


settings = Settings()
