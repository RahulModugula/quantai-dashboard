from datetime import datetime

from pydantic import BaseModel, Field


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
