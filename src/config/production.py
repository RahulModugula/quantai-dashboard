"""Production environment configuration."""
from pydantic_settings import BaseSettings


class ProductionSettings(BaseSettings):
    """Production-specific settings."""

    # Environment
    environment: str = "production"
    debug: bool = False
    log_level: str = "INFO"

    # Database
    db_url: str  # Must be set
    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_pool_recycle: int = 3600

    # API
    api_title: str = "QuantAI Trading Dashboard"
    api_version: str = "1.0.0"
    api_workers: int = 4

    # Security
    cors_origins: list[str] = ["https://yourdomain.com"]
    api_key_required: bool = True
    rate_limit: int = 1000  # per hour
    burst_size: int = 50    # per minute

    # Caching
    cache_ttl: int = 300
    redis_url: str = "redis://localhost:6379"

    # Monitoring
    enable_metrics: bool = True
    enable_logging: bool = True
    log_format: str = "json"

    class Config:
        env_file = ".env"
        env_prefix = "QUANTAI_"
        case_sensitive = False
