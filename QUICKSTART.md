# QuantAI Quick Start Guide

Get trading predictions and portfolio analytics running in 10 minutes.

## Prerequisites
- Python 3.11+
- Redis (for price caching)
- SQLite (built-in)

## 1. Setup Environment

```bash
# Clone the repo
git clone <repo-url>
cd profile-max

# Create virtual environment
uv venv .venv --python 3.11
source .venv/bin/activate

# Install dependencies
make setup
```

## 2. Configure Settings

```bash
# Copy example config
cp .env.example .env

# Edit .env to customize:
# - QUANTAI_TICKERS: which stocks to track
# - QUANTAI_INITIAL_CAPITAL: starting paper trading amount
# - QUANTAI_BUY_THRESHOLD: prediction confidence threshold (0-1)
```

## 3. Download Data & Train

```bash
# Download 5 years of OHLCV + technical indicators
make seed

# Train walk-forward ensemble model
make train

# Optional: Run backtest to validate
make backtest
```

## 4. Start the API

```bash
make run
```

Visit http://localhost:8000/dashboard to see the interactive dashboard.

## 5. Make Your First API Call

```bash
# Get next-day prediction for AAPL
curl http://localhost:8000/api/predictions/AAPL

# Get portfolio status
curl http://localhost:8000/api/portfolio/

# Check system health
curl http://localhost:8000/api/health
curl http://localhost:8000/api/status/ready
```

## API Endpoints Quick Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/predictions/{ticker}` | GET | Get next-day prediction |
| `/api/predictions/batch` | POST | Batch predictions |
| `/api/portfolio/` | GET | Portfolio state |
| `/api/backtest/run` | POST | Run walk-forward backtest |
| `/api/optimizer/portfolio` | POST | Optimize weights |
| `/api/sip/calculate` | POST | SIP projection |
| `/api/status/data` | GET | Data freshness |
| `/api/diagnostics/validate-config` | POST | Check config |
| `/dashboard` | GET | Interactive dashboard |

## Troubleshooting

**"No trained model available"**
- Run `make train` to train the ensemble

**"No feature data for AAPL"**
- Run `make seed` to download market data
- Check `/api/status/data` to see which tickers have data

**Redis connection error**
- Start Redis: `redis-server`
- Or set `QUANTAI_REDIS_URL` to disable caching

## Next Steps

1. Explore the dashboard at http://localhost:8000/dashboard
2. Read README.md for architecture overview
3. Check tests/ for usage examples
4. Run `/api/docs` for interactive API documentation

---

**DISCLAIMER**: Educational purposes only. Not financial advice. Backtested results are theoretical.
