# QuantAI — AI Credit Committee & ML Trading Platform

[![CI/CD Pipeline](https://github.com/RahulModugula/quantai-dashboard/actions/workflows/ci.yml/badge.svg)](https://github.com/RahulModugula/quantai-dashboard/actions/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![LiteLLM](https://img.shields.io/badge/LLM-LiteLLM%20%7C%20Claude%20%7C%20GPT--4%20%7C%20Ollama-blueviolet)](https://github.com/BerriAI/litellm)
[![Demo Ready](https://img.shields.io/badge/demo-no%20API%20key%20required-brightgreen.svg)](examples/distressed/demo.py)

> A 4-agent AI investment committee that debates every trade — then writes the memo.
> Built to show that the same agentic architecture works across equities **and** distressed credit.

---

## 🚀 Quick Demo (no API key required)

> **See the 4-agent credit committee in action — pre-rendered output, zero dependencies**

```bash
git clone https://github.com/RahulModugula/quantai-dashboard.git
cd profile-max
python -m examples.distressed.demo
```

**What you'll see:**
- 📊 **QUICK SUMMARY** — Trade entry, thesis, and realized outcome
- 🤖 **Agent Pipeline** — Visual architecture of the 4-agent system
- 📝 **Full IC Memo** — Complete committee output with colored sections:
  - **CapStructureAgent brief** — leverage, coverage, fulcrum security, recovery analysis
  - **SituationAgent brief** — timeline, catalysts, structural vs. noise events
  - **CreditRiskAgent brief** — devil's advocate: tail risks, challenges to recovery math
  - **Committee memo** — RECOMMENDATION: BUY, with instrument, sizing, catalyst
- ✅ **KEY TAKEAWAYS** — 6 bullet points summarizing the analysis
- 🎯 **Outcome** — Knighthead/Marathon $523.3M take-private confirmed the thesis

This demo shows the **pre-rendered output** of a 4-agent credit committee debate on ATI Physical Therapy's April 2023 Transaction Support Agreement — the loan-to-own entry that Knighthead Capital and Marathon Asset Management used to build the equity position that closed as a **$523.3M take-private in August 2025 (~11.2x LTM Adj EBITDA)**. The committee's base/bull thesis was confirmed.

**To run the live version** (generates fresh output via LLM):
```bash
export ANTHROPIC_API_KEY=sk-ant-...        # or OPENAI_API_KEY, or use Ollama
python -m examples.distressed.ati_2023
```

---

## What This Is

Two systems sharing one agentic architecture:

**1. Distressed Credit Committee** (`examples/distressed/`) — 4 agents debate a restructuring situation and write an IC-style memo:
- **CapStructureAgent** — leverage, coverage, fulcrum security, waterfall recovery (base/bear/bull)
- **SituationAgent** — docket timeline, upcoming catalysts, structural vs. noise events
- **CreditRiskAgent** — devil's advocate: stresses every assumption, enumerates tail risks
- **CreditCommitteeAgent** — writes the vote memo: instrument, sizing, thesis, downside, conditions

**2. Equity Trading System** (`src/`) — live signals, walk-forward ML backtesting, paper trading:
- Ensemble model (RF + XGB + LightGBM + LSTM) with no lookahead bias
- SHAP explainability on every prediction
- 296 tests, production Docker stack, Prometheus metrics, FastAPI + Dash

---

## 💡 Why This Matters

The ATI Physical Therapy demo isn't just a sample — it's a **real-world validation** of the agentic approach:

| Aspect | Detail |
|---------|---------|
| **Real Trade** | Knighthead Capital & Marathon Asset Management actually executed this trade |
| **Entry Point** | April 2023 TSA (2L PIK convertible, loan-to-own structure) |
| **Exit** | August 2025 take-private at $523.3M (~11.2x LTM Adj EBITDA) |
| **Thesis** | PT wage normalization → EBITDA recovery |
| **Outcome** | Base thesis **CONFIRMED** | Bull thesis **CONFIRMED** |

The 4-agent committee correctly identified the fulcrum security, quantified asymmetric upside (250-320c par bull case), bounded downside (55-70c par bear case), and recommended BUY with conditions. The same agentic architecture that analyzed this distressed credit situation can analyze equities, restructurings, or any other investment thesis — just swap the system prompts and tools.

| Feature | Distressed Credit | Equity Trading |
|---------|------------------|----------------|
| **Agents** | 4 (CapStructure, Situation, CreditRisk, CreditCommittee) | 4 (Quant, News, Risk, PortfolioManager) |
| **Output** | IC-style memo with vote | BUY/SELL/HOLD signals with reasoning |
| **Data** | Capital structures, dockets, recovery analysis | OHLCV, news, SEC filings, ML predictions |
| **Use Case** | Restructuring, loan-to-own, fulcrum securities | Daily trading, portfolio optimization |
| **Shared** | `BaseAgent` class, LiteLLM integration, tool framework | `BaseAgent` class, LiteLLM integration, tool framework |

The two systems share one 50-line `BaseAgent` class. Swapping system prompts and tools is all it takes to go from equity analysis to credit committee.

---

## System Overview

```
                        ┌─────────────────────────────────────┐
                        │         QuantAI Intel Layer          │
                        │                                      │
  yfinance news ──────► │  QuantAgent   NewsAgent              │
  SEC EDGAR ──────────► │       │           │                  │
  ML Predictions ─────► │       └─────┬─────┘                 │
                        │         RiskAgent                    │
                        │             │                        │
                        │     PortfolioManagerAgent            │
                        │     BUY / SELL / HOLD + reasoning    │
                        └──────────────┬──────────────────────┘
                                       │
yfinance + VIX/TNX                     ▼
     │              ┌──────────────────────────────────┐
     ▼              │  FastAPI  /api/*                  │
ingestion.py        │  • /agents/analyze/{ticker}       │
     │              │  • /agents/debate/{ticker}        │
     ▼              │  • /predictions, /portfolio       │
features.py ──────► │  • /backtest, /optimizer         │
     │              │  • /regime, /stress-test, /shap  │
     ▼              └──────────────┬───────────────────┘
walk_forward_train()               │
     │                             ▼
EnsembleModel              Plotly Dash /dashboard
RF+XGB+LGB+LSTM            ┌─────────────────────┐
     │                     │ Live Trading         │
     ▼                     │ Portfolio            │
BacktestEngine             │ Backtesting          │
Monte Carlo CI             │ AI Reasoning  ◄──────┼── NEW
     │                     │ Explainability (SHAP)│
     ▼                     │ Optimizer            │
PaperTrader loop           │ Advisor + SIP        │
Half-Kelly sizing          └─────────────────────┘
```

---

## Stack

| Layer | Technology |
|-------|-----------|
| Data | yfinance, pandas, SQLite (SQLAlchemy + Alembic) |
| ML | scikit-learn, XGBoost, LightGBM, PyTorch (LSTM), Optuna, SHAP |
| **AI Agents** | **LiteLLM, multi-agent debate, SEC EDGAR + news tool use** |
| Portfolio | PyPortfolioOpt (efficient frontier, HRP, min-vol) |
| API | FastAPI, WebSocket, Prometheus metrics |
| Dashboard | Plotly Dash (8 tabs, mounted via WSGIMiddleware) |
| Cache | Redis |
| Observability | structlog, Prometheus, health checks |
| CI/CD | GitHub Actions, pre-commit hooks |
| Infra | Docker Compose |

---

## Quick Start

```bash
# Docker (recommended — no setup required)
docker compose up --build
```

```bash
# Local development
uv venv .venv --python 3.11
source .venv/bin/activate
make setup      # install dependencies
make seed       # download 5y of OHLCV + build features
make train      # walk-forward ensemble training (~5 min)
make backtest   # run backtest, save report
make run        # start at http://localhost:8000
```

| Endpoint | URL |
|----------|-----|
| Dashboard | http://localhost:8000/dashboard |
| API docs | http://localhost:8000/api/docs |
| Health | http://localhost:8000/api/health |
| Metrics | http://localhost:8000/api/metrics/prometheus |

---

## QuantAI Intel — Multi-Agent AI Reasoning

Each analysis run goes through a structured debate between four LLM agents. The agents produce a human-readable memo — BUY / SELL / HOLD with confidence and reasoning — which is stored in SQLite and surfaced in the **"AI Reasoning"** dashboard tab. The live paper-trading loop runs independently off the ML ensemble; the agent layer is an **advisory memo generator**, not an autonomous execution agent.

### The Four Agents

| Agent | Role | Tools |
|-------|------|-------|
| **QuantAgent** | Reads the ML ensemble prediction, top SHAP features, and technical indicator snapshot | `get_ml_prediction`, `get_shap_importance`, `get_technical_signals` |
| **NewsAgent** | Fetches recent headlines and SEC EDGAR 8-K/10-Q filings via tool use | `get_recent_news` (yfinance), `get_sec_filings` (EDGAR free API) |
| **RiskAgent** | Devil's advocate — challenges both analysts, raises tail risks, issues AGREE/CAUTION/DISAGREE verdict | *(reads prior briefs)* |
| **PortfolioManagerAgent** | Weighs all three briefs against current position, issues final BUY/SELL/HOLD with confidence score and reasoning bullets | *(reads all briefs)* |

### How the Debate Works

```
Step 1  QuantAgent + NewsAgent run in parallel
           ↓                  ↓
        Quant Brief       Research Brief
           └──────────┬──────────┘
Step 2            RiskAgent
              challenges both
                    ↓
                Risk Brief
           ┌────────┴──────────────┐
Step 3  PortfolioManagerAgent
        final BUY / SELL / HOLD
        + confidence + reasoning
                    ↓
          Stored in SQLite
          Shown in dashboard
```

### Setup

```bash
# .env — set one of these:
ANTHROPIC_API_KEY=sk-ant-...            # Claude (default)
# OPENAI_API_KEY=sk-...                 # GPT-4
# QUANTAI_AGENT_MODEL=ollama/llama3     # Local, no key needed
```

### API

```bash
# Trigger analysis (returns immediately with analysis_id)
curl -X POST http://localhost:8000/api/agents/analyze/AAPL

# Poll status
curl http://localhost:8000/api/agents/status/{analysis_id}

# Read full debate transcript
curl http://localhost:8000/api/agents/debate/AAPL

# Latest decision
curl http://localhost:8000/api/agents/decision/AAPL

# Historical decisions + accuracy
curl http://localhost:8000/api/agents/history/AAPL
curl http://localhost:8000/api/agents/accuracy
```

---

---

## Retargeting to Distressed Credit

The four agents are orchestrated over a data-agnostic context dict — the pattern has nothing hard-coded to equities. Swap the system prompts, swap the tool bindings, and the same loop becomes a credit committee.

`examples/distressed/` contains a worked example on **ATI Physical Therapy** — Knighthead Capital and Marathon Asset Management took the company private on August 1, 2025 at $2.85/share after a 2023 Chapter 11 restructuring in which they converted debt to equity. The four equity-analyst agents are re-subclassed as a credit committee:

| Equity agent | → | Credit agent |
|--------------|---|--------------|
| QuantAgent | → | CapStructureAgent — leverage, coverage, recovery per tranche |
| NewsAgent | → | SituationAgent — docket events, 8-K cadence, management changes |
| RiskAgent | → | CreditRiskAgent — covenant headroom, liquidation value, catalyst delay |
| PortfolioManagerAgent | → | CreditCommitteeAgent — IC-style memo: thesis, sizing, catalysts, exit |

Run it: `python -m examples.distressed.ati_2023` (requires an LLM API key). A pre-rendered sample memo is checked in at [`examples/distressed/ati_2023_memo.md`](examples/distressed/ati_2023_memo.md) for readers without a key. The decision point analyzed is the **April 11, 2023 TSA** — the loan-to-own entry via 2L PIK convertibles — not the August 2025 take-private, which is the *outcome* of the 2023 decision (TEV $523M, ~11.2x LTM EBITDA).

---

## ML Pipeline

### Ensemble Model

Four models with intentional diversity — each captures different signal types:

| Model | Weight | Contribution |
|-------|--------|-------------|
| Random Forest | 0.30 | Bootstrap diversity, handles nonlinear interactions |
| XGBoost | 0.30 | Gradient boosting, strong on tabular patterns |
| LightGBM | 0.25 | Leaf-wise splits, fast retraining |
| LSTM | 0.15 | Temporal sequence context (lower weight — harder to calibrate on daily data) |

### Walk-Forward Training

Predictions at time `t` use only data before `t`. No lookahead bias.

```
┌────────────────────────────────────────────────────────────┐
│  Fold 1: Train [0, 252) → Predict [252, 315)               │
│  Fold 2: Train [0, 315) → Predict [315, 378)               │
│  Fold 3: Train [0, 378) → Predict [378, 441)               │
│  ...                                                        │
└────────────────────────────────────────────────────────────┘
```

### Features (27+)

RSI-14, MACD, MACD signal, Bollinger Bands (%, bandwidth), ATR-14, Stochastic (K, D), ADX-14, SMA50/SMA200 ratios, return lags (1/2/3/5d), volatility (5/20d), momentum (5/20d), mean reversion (20d), volume ratio, OBV, VIX, Treasury yield.

---

## Backtesting

- **Walk-forward validation** — realistic OOS performance, no in-sample bias
- **Slippage models** — participation-rate and square-root market impact
- **Monte Carlo confidence intervals** — block bootstrap (preserves autocorrelation)
- **Benchmark comparison** — all metrics reported vs SPY
- **Risk metrics** — Sharpe, Sortino, Calmar, max drawdown, win rate, profit factor
- **Scenario stress tests** — GFC, dotcom, COVID crash, 2022 rate hikes, flash crash
- **CSV export** — full trade log downloadable

---

## Dashboard Tabs

| Tab | What You Get |
|-----|-------------|
| **Live Trading** | Real-time candlestick, ML signal overlay, live trade log |
| **Portfolio** | Equity curve, drawdown chart, cumulative returns |
| **Backtesting** | Run backtest, view metrics, export trades |
| **AI Reasoning** | Multi-agent debate, final decision, historical accuracy |
| **Explainability** | SHAP feature importance (top-15 bar + per-model breakdown) |
| **Optimizer** | Efficient frontier, HRP, min-vol weights |
| **Advisor** | Risk profiling questionnaire + allocation recommendation |
| **SIP Calculator** | Forward projection + reverse (goal → monthly amount) |

---

## API Reference

<details>
<summary>All endpoints</summary>

**Agent Intel**
```
POST /api/agents/analyze/{ticker}     trigger async analysis
GET  /api/agents/status/{id}          poll progress
GET  /api/agents/debate/{ticker}      full 4-agent transcript
GET  /api/agents/decision/{ticker}    latest decision
GET  /api/agents/history/{ticker}     decision history
GET  /api/agents/accuracy             win rate across all decisions
```

**Predictions & Signals**
```
GET /api/predictions/{ticker}         next-day ML probability + signal
GET /api/signals/latest/{ticker}      signal with strength
GET /api/signals/consensus            cross-ticker consensus
```

**Portfolio**
```
GET /api/portfolio                    positions, cash, total value
GET /api/portfolio/history            equity curve
GET /api/portfolio/trades             trade log
GET /api/portfolio/correlation        correlation matrix
```

**Backtesting**
```
POST /api/backtest/run                async trigger
GET  /api/backtest/result/{key}       retrieve cached result
GET  /api/backtest/export/{key}/trades  CSV download
```

**Analysis**
```
GET /api/shap/importance/{ticker}     SHAP feature importance
GET /api/regime/{ticker}              current market regime
GET /api/regime/{ticker}/history      252-day regime history
GET /api/stress-test/monte-carlo/{ticker}
GET /api/stress-test/scenarios/{ticker}
GET /api/analysis/sector-composition
GET /api/analysis/performance-summary
```

**Optimizer & Advisor**
```
POST /api/optimizer/portfolio         max-Sharpe / min-vol / HRP weights
POST /api/optimizer/frontier          efficient frontier
POST /api/advisor/risk-profile        score risk questionnaire
GET  /api/advisor/allocation/{category}
POST /api/sip/calculate               forward SIP projection
POST /api/sip/reverse                 goal-based SIP
```

**Meta**
```
GET /api/health
GET /api/metrics/prometheus
GET /api/diagnostics/validate-config
GET /api/diagnostics/data-freshness
```
</details>

---

## Design Decisions

**Walk-forward expanding windows over rolling windows**
Expanding windows use all available history per fold — more stable for tree-based models. The hard constraint: features are joined strictly by date so predictions at `t` never touch data from `t` onwards.

**Classification over regression**
Direction prediction (up/down) maps cleanly to trading signals and produces calibrated probabilities for Half-Kelly sizing. Return magnitude prediction adds noise without actionable benefit at daily frequency.

**Half-Kelly position sizing**
Full Kelly maximizes expected log growth but creates drawdowns that are hard to stomach in practice. Half-Kelly gives ~75% of the growth rate at materially lower volatility — a better tradeoff given imperfect model calibration.

**LiteLLM as the agent backbone**
Model-agnostic by design. Swap `QUANTAI_AGENT_MODEL=ollama/llama3` for fully local, offline inference with no API costs. The same agent code runs against Claude, GPT-4, Mistral, or any 100+ supported models.

**Free alternative data only**
`yfinance.Ticker.news` and the SEC EDGAR full-text search API both require zero authentication. This keeps the project genuinely reproducible — no paid data subscriptions, no rate-limited keys to manage.

---

## Tests

```bash
make test
```

296 tests across: feature engineering, backtest engine, risk metrics, SIP calculator, portfolio operations, signal generation, model drift detection, storage, portfolio optimization, slippage models, SHAP explainability, regime detection, ablation study, live feed, stress testing, multi-agent loop, tool dispatch, agent prompts, orchestrator, and agent storage.

---

## Project Structure

```
src/
├── agents/                # QuantAI Intel — multi-agent LLM layer
│   ├── base_agent.py      # LiteLLM agentic tool-call loop
│   ├── quant_agent.py     # ML signals + SHAP + technicals
│   ├── news_agent.py      # yfinance news + SEC EDGAR via tool use
│   ├── risk_agent.py      # devil's advocate risk analysis
│   ├── orchestrator.py    # 4-agent pipeline + DB persistence
│   └── tools/             # quant_tools, news_tools, sec_tools
├── config/                # Pydantic settings, feature flags
├── data/                  # yfinance ingestion, 27 features, SQLite storage
├── models/                # Ensemble, walk-forward training, SHAP, drift detection
├── backtest/              # Engine, risk metrics, Monte Carlo, report generation
├── trading/               # Paper trader, portfolio, Half-Kelly signals, stress tests
├── advisor/               # Risk profiling, allocation, rebalancing, SIP calculator
├── api/                   # FastAPI routes, middleware, WebSocket
│   └── routes/            # agents, predictions, portfolio, backtest, shap, regime, …
├── dashboard/             # Plotly Dash (8 tabs), layouts, callbacks
├── monitoring/            # Prometheus metrics
├── health/                # DB / Redis / model / data freshness checks
└── resilience/            # Retry with exponential backoff
```

---

## Limitations

Documented honestly — this matters more than any feature list.

**Model performance** — The ensemble likely does not beat buy-and-hold after costs. Public technical indicators are already priced in by institutional desks. This is expected and consistent with the efficient market hypothesis for liquid US equities.

**Backtesting realism** — No survivorship bias correction (delisted tickers excluded). Commission model understates spread and impact costs. yfinance adjusted prices are retroactively modified, which is fine for exploration but not research-grade.

**LLM agents** — Agent decisions are constrained by LLM knowledge cutoffs and available free data. Agents can hallucinate or miss context not present in recent news. Treat agent reasoning as a structured prompt-to-think framework, not an oracle.

**Infrastructure** — Redis is optional but some features degrade gracefully without it. No authentication enforced by default — don't expose publicly without enabling API keys.

---

## License

MIT
