from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class OHLCVRecord(BaseModel):
    date: datetime
    ticker: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    adj_close: float | None = None


class FeatureRecord(BaseModel):
    date: datetime
    ticker: str
    rsi_14: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    macd_hist: float | None = None
    bb_upper: float | None = None
    bb_middle: float | None = None
    bb_lower: float | None = None
    bb_pct_b: float | None = None
    bb_bandwidth: float | None = None
    atr_14: float | None = None
    volatility_5: float | None = None
    volatility_20: float | None = None
    momentum_5: float | None = None
    momentum_20: float | None = None
    mean_reversion_20: float | None = None
    volume_ratio: float | None = None
    obv: float | None = None
    target: int | None = None  # 1 = up, 0 = down


class TradeRecord(BaseModel):
    id: int | None = None
    timestamp: datetime
    ticker: str
    side: str  # "buy" or "sell"
    shares: float
    price: float
    commission: float
    pnl: float | None = None


class PortfolioSnapshot(BaseModel):
    timestamp: datetime
    total_value: float
    cash: float
    positions_value: float
    daily_return: float | None = None
    cumulative_return: float | None = None


class PredictionResponse(BaseModel):
    ticker: str
    timestamp: datetime
    probability_up: float
    signal: str  # "buy", "sell", "hold"
    confidence: float
    feature_importances: dict[str, float] = Field(default_factory=dict)
    disclaimer: str = "Educational purposes only. Not financial advice."


class BacktestResult(BaseModel):
    ticker: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_value: float
    total_return: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    profit_factor: float | None = None
    calmar_ratio: float | None = None


class SIPResult(BaseModel):
    monthly_amount: float
    duration_years: int
    expected_return: float
    total_invested: float
    pre_tax_corpus: float
    post_tax_corpus: float
    inflation_adjusted_value: float
    wealth_gain: float
    year_breakdown: list[dict] = Field(default_factory=list)


class RiskProfile(BaseModel):
    score: int
    category: str  # Conservative, Moderate, Aggressive, Very Aggressive
    description: str


class AllocationSuggestion(BaseModel):
    risk_category: str
    allocations: dict[str, float]  # asset_class -> percentage
    rationale: str


# Request schemas for API endpoints
class BacktestRequestSchema(BaseModel):
    ticker: str
    initial_capital: float = 100_000.0
    buy_threshold: float = 0.6
    sell_threshold: float = 0.4

    @field_validator("buy_threshold", "sell_threshold")
    @classmethod
    def validate_thresholds(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("Threshold must be between 0.0 and 1.0")
        return v

    @field_validator("initial_capital")
    @classmethod
    def validate_capital(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Initial capital must be positive")
        return v


class RiskProfileRequest(BaseModel):
    age: int
    investment_horizon_years: int
    annual_income: float
    monthly_savings: float
    has_emergency_fund: bool = True
    debt_ratio: float = 0.0

    @field_validator("age", "investment_horizon_years", "annual_income", "monthly_savings")
    @classmethod
    def validate_positive(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Value must be non-negative")
        return v

    @field_validator("debt_ratio")
    @classmethod
    def validate_debt_ratio(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("Debt ratio must be between 0 and 1")
        return v


class SIPRequest(BaseModel):
    monthly_amount: float
    duration_years: int
    expected_annual_return: float
    annual_step_up: float = 0.0

    @field_validator("monthly_amount")
    @classmethod
    def validate_monthly(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Monthly amount must be positive")
        return v

    @field_validator("duration_years")
    @classmethod
    def validate_years(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Duration must be positive")
        return v


class ReverseSIPRequest(BaseModel):
    target_corpus: float
    duration_years: int
    expected_annual_return: float
    annual_step_up: float = 0.0

    @field_validator("target_corpus")
    @classmethod
    def validate_corpus(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Target corpus must be positive")
        return v

    @field_validator("duration_years")
    @classmethod
    def validate_years(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Duration must be positive")
        return v


class OptimizerRequest(BaseModel):
    tickers: list[str]
    lookback_days: int = 252
    expected_return_type: str = "historical"  # "historical" or "equal_weight"

    @field_validator("tickers")
    @classmethod
    def validate_tickers(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("At least one ticker required")
        return v

    @field_validator("lookback_days")
    @classmethod
    def validate_lookback(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Lookback days must be positive")
        return v


# Response schemas for API consistency
class ErrorResponse(BaseModel):
    """Standard error response format."""

    error: str
    detail: str
    request_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str  # "healthy" or "degraded"
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str = "1.0.0"


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""

    data: list
    total: int
    offset: int = 0
    limit: int = 100


class LumpsumVsSIPResponse(BaseModel):
    """Response for lumpsum vs SIP comparison endpoint."""

    total_capital: float
    lumpsum: dict
    sip: dict
    winner: str
    disclaimer: str = "Educational purposes only."


class CorrelationResponse(BaseModel):
    """Response for correlation matrix endpoint."""

    tickers: list[str]
    matrix: list[list[float]]
    high_correlation_pairs: list[dict] = Field(default_factory=list)
