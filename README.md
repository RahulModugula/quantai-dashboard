# QuantAI — ML Trading Dashboard

[![CI/CD Pipeline](https://github.com/RahulModugula/quantai-dashboard/actions/workflows/ci.yml/badge.svg)](https://github.com/RahulModugula/quantai-dashboard/actions/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **DISCLAIMER**: This project is for **educational purposes only**. All predictions, signals, and portfolio data are simulated. Nothing here constitutes financial advice.

An ML-powered trading dashboard that combines walk-forward backtesting, ensemble models, paper trading simulation, and portfolio optimization — built with FastAPI, Plotly Dash, and PyTorch.

---

## What It Does

The system downloads daily OHLCV data via yfinance, engineers 27+ technical features, trains a 4-model ensemble (Random Forest, XGBoost, LightGBM, LSTM) using walk-forward expanding windows, and generates next-day direction predictions. A paper trading loop executes simulated trades with Half-Kelly position sizing, and a dashboard visualizes everything in real time.

### Key Components

- **Ensemble model** — RF + XGBoost + LightGBM + LSTM with dynamic weighting (0.3/0.3/0.25/0.15). Walk-forward training ensures predictions at time `t` use only data before `t`.
- **Backtesting engine** — Walk-forward validation with risk metrics (Sharpe, Sortino, Calmar, max drawdown), benchmark comparison vs SPY, Monte Carlo confidence intervals, and CSV export. Includes volume-weighted slippage (participation-rate and square-root impact models) for realistic fill simulation.
- **Paper trading** — Async trading loop with Half-Kelly position sizing, max drawdown constraints, and Redis-cached price distribution.
- **Portfolio optimization** — Max Sharpe, min volatility, and HRP allocation via PyPortfolioOpt with efficient frontier visualization.
- **AI Reasoning Layer (QuantAI Intel)** — Multi-agent LLM system that deliberates on every trade. Four specialized agents — QuantAgent, NewsAgent, RiskAgent, and PortfolioManagerAgent — debate each decision using real ML predictions, live news, and SEC EDGAR filings. Model-agnostic via LiteLLM (works with Claude, GPT-4, Ollama). Full reasoning traces stored to DB and visualized in the "AI Reasoning" dashboard tab. See [AI Reasoning](#ai-reasoning-quantai-intel) below.
- **Dashboard** — Plotly Dash frontend with candlestick charts, signal display, equity curves, backtest runner, SIP calculator, portfolio optimizer, SHAP explainability, and AI Reasoning tabs.
- **SHAP explainability** — TreeExplainer-based feature importance averaged across RF/XGB/LGB ensemble members. Dashboard tab shows top-15 feature bar chart and per-model breakdown. Normalize endpoint enables cross-ticker comparison.
- **Market regime detection** — Volatility-regime (low/normal/high) and trend-regime (trending up/down/sideways) classification. API exposes current regime, 252-day history, and performance-by-regime breakdown. `make ablation` quantifies marginal Sharpe contribution per ensemble member and per feature group.
- **Portfolio stress testing** — Monte Carlo simulation using block bootstrap (preserves autocorrelation) over configurable horizon. Historical scenario replay for COVID crash, 2022 rate hike, GFC, dotcom bust, and flash crash.
- **Live data feed** — Alpaca WebSocket integration with exponential-backoff reconnection and queue-based backpressure. Falls back to yfinance polling when API credentials are not configured.

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
| AI Agents | LiteLLM (model-agnostic), multi-agent debate, SEC EDGAR + news tools |
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

95+ tests covering feature engineering, backtest metrics, SIP calculator, portfolio operations, signal generation, model drift detection, storage, portfolio optimization, slippage models, SHAP explainability, regime detection, ablation study, live feed, and stress testing.

---

## AI Reasoning — QuantAI Intel

QuantAI Intel is a multi-agent LLM system that answers the question every quant asks: **"Why did the model do that?"**

Four specialized agents deliberate on every trade decision using a mix of quantitative signals and real-world data:

| Agent | Role | Data Sources |
|-------|------|--------------|
| **QuantAgent** | Reads ML predictions, SHAP importance, technical indicators | Internal model APIs |
| **NewsAgent** | Reads recent news and SEC EDGAR filings via tool use | yfinance news (free), SEC EDGAR (free) |
| **RiskAgent** | Devil's advocate — challenges every trade idea | Both agent briefs above |
| **PortfolioManagerAgent** | Synthesizes all three briefs, issues Buy/Sell/Hold + full reasoning | All three briefs |

### Setup

Set your LLM API key in `.env`:

```bash
ANTHROPIC_API_KEY=sk-ant-...      # For Claude (default model)
# Or use any LiteLLM-supported model:
QUANTAI_AGENT_MODEL=openai/gpt-4o
QUANTAI_AGENT_MODEL=ollama/llama3  # Local model, no API key needed
```

### Usage

```bash
# Trigger analysis via API
curl -X POST http://localhost:8000/api/agents/analyze/AAPL

# Poll for completion
curl http://localhost:8000/api/agents/status/{analysis_id}

# Read the full debate
curl http://localhost:8000/api/agents/debate/AAPL

# Check historical accuracy
curl http://localhost:8000/api/agents/accuracy
```

Or use the **"AI Reasoning" tab** in the dashboard — select a ticker, click "Analyze Now", and watch the agents deliberate in real time.

### Why This Is Novel

No existing open-source tool combines:
1. Walk-forward ML backtesting with LLM reasoning traces
2. Multi-agent debate with a devil's advocate risk agent
3. Free alternative data (news + SEC EDGAR, no API key needed)
4. Full audit trail stored in SQLite (decision, confidence, all briefs, accuracy outcome)
5. Model-agnostic LLM backend (Claude, GPT-4, or any local model via Ollama)

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
- **Event-driven backtester** — replacing the vectorized backtest with tick-by-tick event processing would enable realistic fill simulation (partial fills, queue position). The current slippage model is a step in this direction but still fills at a single price.
- **Live trading with Alpaca** — the WebSocket feed module is built; wiring it to the paper trader loop and replacing yfinance polling would close the gap to real-time operation.
- **Survivorship bias correction** — adding delisted tickers to the backtest universe using a point-in-time database (CRSP, Norgate) would produce more credible historical results.

---

## Project Structure

```
src/
├── config/                # Pydantic Settings, feature flags, production config
├── data/                  # yfinance ingestion, 27 technical features, SQLite storage
├── models/                # Ensemble (RF+XGB+LGB+LSTM), training, SHAP, drift detection
├── backtest/              # Walk-forward engine, risk metrics, Monte Carlo, reports
├── trading/               # Paper trader, portfolio, Half-Kelly signals
├── advisor/               # Risk profiling, allocation, SIP calculator
├── api/                   # FastAPI routes, middleware, structured logging
│   └── routes/            # predictions, portfolio, backtest, advisor, diagnostics
├── dashboard/             # Plotly Dash (6 tabs), layouts, callbacks
├── monitoring/            # Prometheus metrics (request latency, model inference)
├── health/                # Dependency health checks (DB, Redis, model, data)
└── resilience/            # Retry with exponential backoff
```

---

## License

MIT
