# QuantAI — ML Trading Dashboard

> **DISCLAIMER**: This project is for **educational purposes only**. All predictions, signals, and portfolio data are simulated. Nothing here constitutes financial advice.

An ML-powered trading dashboard that combines walk-forward backtesting, ensemble models, paper trading simulation, and portfolio optimization — built with FastAPI, Plotly Dash, and PyTorch.

---

## What It Does

The system downloads daily OHLCV data via yfinance, engineers 27+ technical features, trains a 4-model ensemble (Random Forest, XGBoost, LightGBM, LSTM) using walk-forward expanding windows, and generates next-day direction predictions. A paper trading loop executes simulated trades with Half-Kelly position sizing, and a dashboard visualizes everything in real time.

### Key Components

- **Ensemble model** — RF + XGBoost + LightGBM + LSTM with dynamic weighting (0.3/0.3/0.25/0.15). Walk-forward training ensures predictions at time `t` use only data before `t`.
- **Backtesting engine** — Walk-forward validation with risk metrics (Sharpe, Sortino, Calmar, max drawdown), benchmark comparison vs SPY, Monte Carlo confidence intervals, and CSV export.
- **Paper trading** — Async trading loop with Half-Kelly position sizing, max drawdown constraints, and Redis-cached price distribution.
- **Portfolio optimization** — Max Sharpe, min volatility, and HRP allocation via PyPortfolioOpt with efficient frontier visualization.
- **Dashboard** — Plotly Dash frontend with candlestick charts, signal display, equity curves, backtest runner, SIP calculator, and portfolio optimizer tabs.

---

## Architecture

```
yfinance + VIX/TNX → ingestion.py → features.py → SQLite
                                          ↓
                             walk_forward_train() + Optuna
                                   ↓         ↓
                             EnsembleModel   OOS predictions
                          (RF+XGB+LGB+LSTM)      ↓
                                          BacktestEngine
                                                ↓
                             BacktestReport + Monte Carlo
                                                ↓
FastAPI (/api/*) ← Redis cache ← PaperTrader loop
     ↓
Dash (/dashboard) — polling via dcc.Interval
     ↓
Optimizer tab → PyPortfolioOpt (EF, HRP, MinVol)
```

| Layer | Technology |
|-------|-----------|
| Data | yfinance, pandas, SQLite (SQLAlchemy + Alembic) |
| ML | scikit-learn, XGBoost, LightGBM, PyTorch (LSTM), Optuna, SHAP |
| Portfolio | PyPortfolioOpt (efficient frontier, HRP) |
| API | FastAPI, WebSocket, Prometheus metrics |
| Dashboard | Plotly Dash (mounted via WSGIMiddleware) |
| Cache | Redis |
| Observability | structlog, Prometheus, health checks |
| CI/CD | GitHub Actions (lint + test), pre-commit hooks |
| Infra | Docker Compose |

---

## Quick Start

```bash
# Docker (recommended)
docker compose up --build

# Or local development
uv venv .venv --python 3.11
source .venv/bin/activate
make setup      # install dependencies
make seed       # download market data + build features
make train      # walk-forward ensemble training
make backtest   # run backtest and save report
make run        # start server at localhost:8000
```

Dashboard: http://localhost:8000/dashboard
API docs: http://localhost:8000/api/docs
Health check: http://localhost:8000/api/health
Metrics: http://localhost:8000/api/metrics

---

## Design Decisions

**Why walk-forward expanding windows?**
Expanding windows use all available history for each training fold, which is more stable for tree-based models. The critical constraint: predictions at time `t` use only data before `t` — enforced by date-aligned joins with no lookahead.

**Why classification over regression?**
Direction prediction (up/down) maps cleanly to trading signals and produces calibrated probabilities for position sizing. Return magnitude prediction adds noise without actionable benefit at this frequency.

**Why Half-Kelly position sizing?**
Full Kelly is optimal but volatile. Half-Kelly provides ~75% of the growth rate with significantly lower drawdowns — a better risk/reward tradeoff, especially for a system where model calibration is imperfect.

**Why four ensemble members?**
RF and XGBoost capture different interaction patterns. LightGBM trains faster and handles categorical splits natively. LSTM adds temporal sequence signal that tree models miss. The weighting intentionally gives LSTM less weight since it's harder to calibrate on small financial datasets.

---

## Running Tests

```bash
make test
```

68 tests covering feature engineering, backtest metrics, SIP calculator, portfolio operations, signal generation, model drift detection, storage, and portfolio optimization.

---

## Limitations and Future Work

This section documents known limitations honestly — understanding where a system falls short matters more than the feature list.

### Model Performance
- **The ensemble likely does not beat buy-and-hold** on a risk-adjusted basis after transaction costs. This is consistent with the efficient market hypothesis for liquid US equities using publicly available technical features. The backtester's Sharpe ratio should be compared against SPY's, not against zero.
- **All 27 features are well-known technical indicators** already priced into markets by institutional quant desks. For genuine alpha, you'd need alternative data (sentiment, options flow, earnings transcripts) or higher-frequency signals.
- **The LSTM component may not add value** over tree models alone for daily bars. Sequence models shine with higher-frequency data where temporal patterns are stronger. I haven't run a rigorous ablation study to confirm this.

### Backtesting Realism
- **Survivorship bias** — the system only downloads data for tickers in the config. A proper backtest would include delisted companies and use a point-in-time universe.
- **Transaction costs are understated** — the 0.1% commission model doesn't capture spread costs, market impact, or the fact that small-cap fills are worse than modeled.
- **yfinance data quality** — adjusted close prices are retroactively modified for splits and dividends. This is fine for rough analysis but not research-grade. Professional backtesting uses point-in-time databases (e.g., CRSP, Norgate).
- **No slippage on volume** — the backtester assumes all orders fill at close price regardless of volume. For small-cap or volatile names, this is unrealistic.

### Infrastructure Gaps
- **No database migrations in production** — Alembic is set up but migrations should be validated in a staging environment before any real deployment.
- **Redis is optional but assumed** — the paper trader falls back gracefully, but some cache-dependent features will silently degrade.
- **No authentication in development** — API keys and RBAC exist but aren't enforced by default. Don't expose this to the internet without enabling them.

### What Would Make This Better
- **Alternative data integration** — earnings call sentiment (via NLP on SEC filings), options flow from CBOE, or social media sentiment would test whether non-price data adds signal.
- **Event-driven backtester** — replacing the vectorized backtest with tick-by-tick event processing would enable realistic fill simulation (slippage, partial fills, queue position).
- **Proper ablation studies** — systematically removing features and ensemble members to measure marginal contribution. SHAP values help but aren't a substitute for out-of-sample ablation.
- **Live data via WebSocket** — connecting to Alpaca or Polygon.io instead of polling yfinance would enable real-time signal generation.
- **Regime analysis** — measuring model performance separately in trending vs. mean-reverting vs. high-volatility regimes. Most ML models work well in trends and fail in chop.

---

## Project Structure

```
src/
├── config.py              # Pydantic Settings with validators
├── data/                  # Ingestion, features, storage, schemas
├── models/                # Ensemble, LSTM, training, drift detection
├── backtest/              # Walk-forward engine, metrics, reports
├── trading/               # Portfolio, signals, paper trader
├── advisor/               # Risk profiling, allocation, SIP calculator
├── api/                   # FastAPI routes, middleware, auth
├── dashboard/             # Plotly Dash layouts and callbacks
├── monitoring/            # Prometheus metrics, observability
├── health/                # Dependency health checks
└── resilience/            # Circuit breaker, retry with backoff
```

---

## License

MIT
