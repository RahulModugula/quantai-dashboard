"""Input validation and sanitization for API requests."""
import logging
import re
from typing import Any, Optional, List
from pydantic import BaseModel, field_validator, ValidationInfo

logger = logging.getLogger(__name__)


class InputValidator:
    """Validate and sanitize input data."""

    @staticmethod
    def validate_ticker(ticker: str) -> str:
        """Validate stock ticker symbol."""
        ticker = ticker.strip().upper()
        if not re.match(r"^[A-Z0-9]{1,5}$", ticker):
            raise ValueError(f"Invalid ticker symbol: {ticker}")
        return ticker

    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email address."""
        email = email.strip().lower()
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, email):
            raise ValueError(f"Invalid email address: {email}")
        return email

    @staticmethod
    def validate_date_range(start: str, end: str) -> tuple:
        """Validate date range."""
        if start >= end:
            raise ValueError("Start date must be before end date")
        return start, end

    @staticmethod
    def validate_percentage(value: float, min_val: float = 0, max_val: float = 100) -> float:
        """Validate percentage value."""
        if not (min_val <= value <= max_val):
            raise ValueError(f"Percentage must be between {min_val} and {max_val}")
        return value

    @staticmethod
    def sanitize_string(text: str, max_length: int = 1000) -> str:
        """Sanitize string input."""
        text = text.strip()
        if len(text) > max_length:
            raise ValueError(f"String exceeds maximum length of {max_length}")
        # Remove potentially dangerous characters
        dangerous_chars = r"[<>\"'%;()&+]"
        text = re.sub(dangerous_chars, "", text)
        return text


class TickerInput(BaseModel):
    """Validated ticker input."""

    ticker: str

    @field_validator("ticker")
    @classmethod
    def validate_ticker_field(cls, v: str) -> str:
        return InputValidator.validate_ticker(v)


class DateRangeInput(BaseModel):
    """Validated date range input."""

    start_date: str
    end_date: str

    @field_validator("end_date")
    @classmethod
    def validate_date_range_field(cls, v: str, info: ValidationInfo) -> str:
        start = info.data.get("start_date")
        if start and v <= start:
            raise ValueError("End date must be after start date")
        return v


class PortfolioInput(BaseModel):
    """Validated portfolio input."""

    tickers: List[str]
    weights: List[float]

    @field_validator("tickers")
    @classmethod
    def validate_tickers(cls, v: List[str]) -> List[str]:
        return [InputValidator.validate_ticker(t) for t in v]

    @field_validator("weights")
    @classmethod
    def validate_weights(cls, v: List[float]) -> List[float]:
        total = sum(v)
        if not (0.99 <= total <= 1.01):  # Allow small rounding error
            raise ValueError(f"Weights must sum to 1.0, got {total}")
        return [InputValidator.validate_percentage(w) for w in v]


class QueryInput(BaseModel):
    """Validated query input with sanitization."""

    query: str
    limit: int = 100
    offset: int = 0

    @field_validator("query")
    @classmethod
    def sanitize_query(cls, v: str) -> str:
        return InputValidator.sanitize_string(v, max_length=500)

    @field_validator("limit")
    @classmethod
    def validate_limit(cls, v: int) -> int:
        if not (1 <= v <= 1000):
            raise ValueError("Limit must be between 1 and 1000")
        return v

    @field_validator("offset")
    @classmethod
    def validate_offset(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Offset must be non-negative")
        return v


def validate_request_body(model_class: type, data: dict) -> Any:
    """Validate request body against model."""
    try:
        return model_class(**data)
    except Exception as e:
        logger.warning(f"Request validation failed: {e}")
        raise ValueError(f"Invalid request: {str(e)}")
