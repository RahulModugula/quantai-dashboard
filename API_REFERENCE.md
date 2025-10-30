# API Reference

Complete REST API documentation for QuantAI Trading Dashboard.

**Base URL:** `/api`

## Table of Contents

1. [Health & Status](#health--status)
2. [Predictions](#predictions)
3. [Portfolio](#portfolio)
4. [Backtest](#backtest)
5. [Advisor](#advisor)
6. [Analysis](#analysis)
7. [Diagnostics](#diagnostics)
8. [Data Validation](#data-validation)

---

## Health & Status

### Health Check

```
GET /health
```

Returns system health status and version.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.2.0",
  "timestamp": "2025-10-29T15:30:00",
  "disclaimer": "..."
}
```

**Status Codes:** `200 OK`

---

### Data Status

```
GET /status/data
```

Check data freshness and availability for all tickers.

**Response:**
```json
{
  "tickers": {
    "AAPL": {
      "last_date": "2025-10-28",
      "rows": 500,
      "days_old": 1,
      "ready": true
    }
  },
  "summary": {
    "tickers_ready": 8,
    "tickers_missing": 2
  }
}
```

**Status Codes:** `200 OK`

---

### Readiness Check

```
GET /status/ready
```

Check if system is ready for trading (model trained, data loaded).

**Response:**
```json
{
  "ready": true,
  "details": {
    "model": "ready",
    "data": "ready",
    "cache": "ready"
  }
}
```

**Status Codes:** `200 OK` | `503 Service Unavailable`

---

## Predictions

### Get Prediction for Ticker

```
GET /predictions/{ticker}
```

Get latest ML prediction and trading signal for a ticker.

**Parameters:**
- `ticker` (path, required): Stock ticker symbol (e.g., "AAPL")

**Response:**
```json
{
  "ticker": "AAPL",
  "probability": 0.72,
  "signal": "STRONG_BUY",
  "confidence": 0.95,
  "datetime": "2025-10-28T15:30:00",
  "disclaimer": "..."
}
```

**Status Codes:**
- `200 OK` - Prediction available
- `404 Not Found` - No data for ticker
- `503 Service Unavailable` - Model not trained

---

### Batch Predictions

```
POST /predictions/batch
Content-Type: application/json

{
  "tickers": ["AAPL", "GOOGL", "MSFT"]
}
```

Get predictions for multiple tickers in one request.

**Request Body:**
```json
{
  "tickers": ["AAPL", "GOOGL", "MSFT"]
}
```

**Response:**
```json
{
  "predictions": [
    {"ticker": "AAPL", "probability": 0.72, "signal": "BUY"},
    {"ticker": "GOOGL", "probability": 0.65, "signal": "HOLD"}
  ],
  "success_count": 2,
  "error_count": 1,
  "errors": {
    "MSFT": "No feature data available"
  }
}
```

**Status Codes:** `200 OK` | `503 Service Unavailable`

---

## Portfolio

### Get Current Portfolio

```
GET /portfolio
```

Get current portfolio state, holdings, and performance.

**Response:**
```json
{
  "total_value": 125000.50,
  "cash": 25000.00,
  "positions_value": 100000.50,
  "initial_capital": 100000,
  "cumulative_return": 0.25,
  "holdings": [
    {
      "ticker": "AAPL",
      "shares": 100,
      "avg_price": 500.00,
      "current_value": 50000,
      "pnl": 5000
    }
  ],
  "disclaimer": "..."
}
```

**Status Codes:** `200 OK`

---

### Portfolio History

```
GET /portfolio/history?limit=200
```

Get portfolio equity curve history for charting.

**Parameters:**
- `limit` (query, optional): Number of snapshots to return (default: 200)

**Response:**
```json
{
  "snapshots": [
    {"date": "2025-10-01", "value": 100000},
    {"date": "2025-10-02", "value": 101500}
  ],
  "count": 29,
  "disclaimer": "..."
}
```

**Status Codes:** `200 OK`

---

### Portfolio Risk Warnings

```
GET /portfolio/warnings
```

Get risk warnings about concentration, correlation, and drawdown.

**Response:**
```json
{
  "has_warnings": true,
  "warnings": {
    "concentration": [
      "⚠️ AAPL is 40.0% of portfolio (threshold: 25%). Consider taking profits."
    ],
    "correlation": [
      "⚠️ AAPL and MSFT are highly correlated (0.85)..."
    ],
    "drawdown": []
  },
  "portfolio_value": 125000.50,
  "position_count": 5
}
```

**Status Codes:** `200 OK`

---

### Get Trades

```
GET /portfolio/trades?ticker=AAPL&limit=100
```

Get trade history with optional ticker filter.

**Parameters:**
- `ticker` (query, optional): Filter by ticker
- `limit` (query, optional): Number of trades (default: 100)

**Response:**
```json
{
  "trades": [
    {
      "date": "2025-10-15",
      "ticker": "AAPL",
      "side": "BUY",
      "shares": 100,
      "price": 500.00,
      "commission": 1.00,
      "pnl": null
    }
  ],
  "count": 45
}
```

**Status Codes:** `200 OK`

---

## Backtest

### Run Backtest

```
POST /backtest/run
Content-Type: application/json

{
  "ticker": "AAPL",
  "initial_capital": 100000,
  "buy_threshold": 0.6,
  "sell_threshold": 0.4
}
```

Trigger a backtest (runs in background).

**Request Body:**
```json
{
  "ticker": "AAPL",
  "initial_capital": 100000,
  "buy_threshold": 0.6,
  "sell_threshold": 0.4
}
```

**Response:**
```json
{
  "status": "started",
  "key": "AAPL_100000",
  "ticker": "AAPL"
}
```

**Status Codes:** `200 OK`

---

### Get Backtest Result

```
GET /backtest/result/{key}
```

Get completed backtest result.

**Parameters:**
- `key` (path, required): Backtest cache key from run response

**Response:**
```json
{
  "status": "complete",
  "result": {
    "metrics": {
      "total_return": 0.45,
      "sharpe_ratio": 1.25,
      "max_drawdown": -0.15,
      "win_rate": 0.52
    },
    "trades": [...],
    "equity_curve": [...]
  }
}
```

**Status Codes:**
- `200 OK` - Result available
- `404 Not Found` - Key not found
- `202 Accepted` - Still running

---

### List Backtests

```
GET /backtest/results
```

List all cached backtest results.

**Response:**
```json
{
  "AAPL_100000": {
    "status": "complete",
    "ticker": "AAPL"
  },
  "GOOGL_100000": {
    "status": "running",
    "ticker": "GOOGL"
  }
}
```

**Status Codes:** `200 OK`

---

### Compare Backtests

```
POST /backtest/compare?key_a=AAPL_100000&key_b=GOOGL_100000
```

Compare two backtest results side-by-side.

**Parameters:**
- `key_a` (query, required): First backtest key
- `key_b` (query, required): Second backtest key

**Response:**
```json
{
  "comparison": {
    "comparison": "AAPL_100000 vs GOOGL_100000",
    "total_return_diff_pct": 5.2,
    "sharpe_diff": 0.35,
    "max_drawdown_diff_pct": 2.5,
    "win_rate_diff_pct": 3.1,
    "trade_count_diff": -5
  }
}
```

**Status Codes:** `200 OK` | `404 Not Found`

---

### Export Trades CSV

```
GET /backtest/export/{key}/trades
```

Export backtest trades as CSV.

**Response:**
```json
{
  "csv": "date,ticker,side,...\n...",
  "filename": "AAPL_trades_AAPL_100000.csv"
}
```

---

### Export Equity CSV

```
GET /backtest/export/{key}/equity
```

Export equity curve as CSV.

---

## Advisor

### Lumpsum vs SIP

```
POST /advisor/lumpsum-vs-sip
Content-Type: application/json

{
  "investment": 100000,
  "months": 12,
  "annual_return_pct": 10,
  "ticker": "AAPL"
}
```

Compare lumpsum vs SIP strategies.

**Response:**
```json
{
  "lumpsum": {
    "initial_investment": 100000,
    "final_value": 110000,
    "total_return_pct": 10
  },
  "sip": {
    "monthly_amount": 8333,
    "total_invested": 100000,
    "final_value": 108500,
    "total_return_pct": 8.5
  }
}
```

---

### Risk Profile

```
POST /advisor/risk-profile
Content-Type: application/json

{
  "age": 35,
  "investment_horizon_years": 25,
  "annual_income": 80000,
  "monthly_savings": 2000,
  "has_emergency_fund": true,
  "debt_ratio": 0.2
}
```

Get recommended asset allocation based on risk profile.

---

### Suggest Equal Weight Rebalance

```
POST /advisor/rebalance/equal-weight
```

Suggest rebalancing to equal weight.

**Response:**
```json
{
  "actions": [
    {
      "ticker": "AAPL",
      "action": "SELL",
      "current_pct": 40.0,
      "target_pct": 25.0,
      "shares_to_trade": 50,
      "estimated_value": 25000,
      "reason": "Align AAPL from 40.0% to 25.0%"
    }
  ],
  "total_trades": 2
}
```

---

### Suggest Risk Reduction

```
POST /advisor/rebalance/reduce-risk?max_position_pct=0.30
```

Suggest selling oversized positions.

---

## Analysis

### Sector Composition

```
GET /analysis/sector-composition
```

Get portfolio breakdown by sector.

**Response:**
```json
{
  "composition": {
    "sectors": {
      "Technology": 45.0,
      "Healthcare": 25.0,
      "Financials": 20.0
    },
    "sector_count": 3,
    "concentration_pct": 35.5,
    "diversification_score": 72.3,
    "concentration_level": "Moderate"
  }
}
```

---

### Check Sector Gaps

```
GET /analysis/sector-gaps?target_sectors=Technology,Healthcare,Financials
```

Identify missing sectors.

---

### Sector Examples

```
GET /analysis/sector-examples/{sector}
```

Get example stocks in a sector.

---

## Diagnostics

### Model Features

```
GET /diagnostics/model-features
```

Inspect model features and importance.

---

### Feature Correlation

```
GET /diagnostics/feature-correlation
```

Analyze feature correlations for multicollinearity.

---

### Validate Config

```
POST /diagnostics/validate-config
```

Validate configuration consistency.

---

## Data Validation

### Validate Ticker

```
POST /data/validate/{ticker}
```

Validate data quality for a ticker.

---

### Data Quality Summary

```
GET /data/summary
```

Overall data health across all tickers.

---

### Missing Tickers

```
GET /data/missing-tickers
```

Identify tickers that haven't been seeded.

---

## Error Responses

All errors return JSON with helpful hints:

```json
{
  "detail": "No trained model available",
  "hints": [
    "1. Run: python -m scripts.train_model",
    "2. Check QUANTAI_DATA_DIR for feature files",
    "3. Ensure seed_data.py has been run first"
  ],
  "doc": "https://github.com/example/profile-max#training"
}
```

**Common Status Codes:**
- `200` - Success
- `202` - Accepted (async processing)
- `400` - Bad request (invalid params)
- `404` - Not found
- `500` - Server error
- `503` - Service unavailable (model/data missing)

---

## Rate Limiting

Default rate limits (can be configured):
- 1,000 requests per hour per IP
- 50 requests per minute per IP

Headers returned with rate limit info:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 2025-10-29T16:30:00Z
```

---

## WebSocket

### Real-time Price Feed

```
WS /ws/prices
```

Stream real-time price updates (when available).

---

## Disclaimer

This API is for educational purposes only. All predictions and signals are simulated and do NOT constitute financial advice. Paper trading results are theoretical and do not guarantee future performance.
