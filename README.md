# QuantAI — Real-Time ML Trading Dashboard

> ⚠️ **DISCLAIMER**: This project is for **educational purposes only**. All predictions, signals, and portfolio data are simulated. Nothing here constitutes financial advice. Backtested results are theoretical and do not guarantee future performance. Always consult a SEBI-registered financial advisor before investing.

A full-stack ML trading dashboard combining data engineering, machine learning, walk-forward backtesting, paper trading simulation, and an interactive Plotly Dash frontend — all served through a single FastAPI server.

---

## Features

### ML Ensemble Model
- **Random Forest + XGBoost + LSTM** weighted ensemble
- Predicts next-day price direction (binary classification)
- Walk-forward training with expanding windows — no look-ahead bias
- Model versioning with joblib + metadata JSON

### Feature Engineering
| Category | Features |
|----------|----------|
| Momentum | RSI-14, MACD (12/26/9), Rate of Change (5d, 20d) |
| Volatility | Bollinger Bands (%B, bandwidth), ATR-14, Rolling std (5d, 20d) |
| Mean Reversion | Z-score vs 20-day rolling mean |
| Volume | Volume ratio vs 20d avg, OBV z-score |

### Backtesting Engine
- Walk-forward validation with configurable window size
- **No look-ahead bias**: predictions[t] use only data before t
- Risk metrics: Sharpe, Sortino, Calmar, Max Drawdown, Win Rate, Profit Factor
- Monthly return heatmap, drawdown periods, equity curve

### Paper Trading
- Asyncio-based virtual trading loop
- Position sizing: fixed fraction of portfolio (configurable)
- Signal thresholds (buy/sell) tunable per strategy
- Redis cache for real-time price distribution

### SIP Calculator
- Pre-tax corpus projection
- Post-tax (LTCG-aware) corpus
- Inflation-adjusted real value
- Annual step-up SIP support
- Year-by-year breakdown

### Financial Advisor
- Risk profiling: age, horizon, income stability, loss tolerance, emergency fund, debt ratio
- Asset allocation by risk category: Conservative / Moderate / Aggressive / Very Aggressive
- Portfolio rebalancing recommendations

### Dashboard (Plotly Dash)
- Live candlestick chart with 120-day history
- Model signal display (buy/sell/hold) with confidence
- Feature importance visualization
- Portfolio equity curve
- Backtest runner with equity and drawdown charts
- SIP calculator with growth chart
- Advisor panel with allocation pie chart

---

## Architecture

```
yfinance → ingestion.py → features.py → SQLite
                                           ↓
                              walk_forward_train()
                                    ↓         ↓
                              EnsembleModel   OOS predictions
                             (RF+XGB+LSTM)        ↓
                                           BacktestEngine
                                                 ↓
                                           BacktestReport
                                                 ↓
FastAPI (/api/*) ← Redis cache ← PaperTrader loop
     ↓
Dash (/dashboard) — polling via dcc.Interval
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Data | yfinance, pandas, SQLite (SQLAlchemy Core) |
| ML | scikit-learn, XGBoost, PyTorch (LSTM) |
| API | FastAPI, WebSocket |
| Dashboard | Plotly Dash (mounted via WSGIMiddleware) |
| Cache | Redis |
| Infra | Docker Compose |

---

## Quick Start

### Option 1: One-command Docker

```bash
docker compose up --build
```

Then open [http://localhost:8000/dashboard](http://localhost:8000/dashboard)

### Option 2: Local Development

```bash
# Install dependencies
make setup

# Download market data and build features
make seed

# Train the ensemble model (walk-forward)
make train

# Run backtest and save report
make backtest

# Start the server
make run
```

---

## Design Decisions

### Why walk-forward expanding windows?
Expanding windows use all available historical data for each training fold, which is more stable for tree-based models. The key constraint is enforced strictly: predictions generated at time `t` use **only** data from before `t`. There is no future leakage.

### Why classification instead of regression?
Predicting direction (up/down) is more actionable for generating trading signals than predicting return magnitude. Direction classification also produces calibrated probabilities that map cleanly to position sizing via thresholds.

### Why static ensemble weights?
A stacking meta-learner requires an additional validation split, increasing overfitting risk with limited financial data. Fixed weights (0.4 RF, 0.4 XGB, 0.2 LSTM) are transparent, debuggable, and backed by interpretable feature importances from RF and XGB. The LSTM adds temporal sequence signal without dominating the ensemble.

### Why Dash-in-FastAPI (not separate)?
Single process deployment eliminates CORS complexity, simplifies Docker configuration, and allows the dashboard to share the same model instances and portfolio state as the API.

### Survivorship Bias
The current implementation downloads data for tickers specified in config. For a research-grade backtest, you would want to include delisted companies. This is documented as a limitation.

---

## Running Tests

```bash
make test
```

Tests cover:
- Feature engineering (RSI bounds, Bollinger ordering, no NaNs in matrix)
- Backtest metrics (known-value assertions for Sharpe, max drawdown, etc.)
- SIP calculator (mathematical correctness, step-up behavior)
- Portfolio operations (buy/sell/PnL/cash balance)

---

## Project Structure

```
src/
├── config.py              # Pydantic Settings
├── data/                  # Ingestion, feature engineering, SQLite storage
├── models/                # RF+XGB+LSTM ensemble, walk-forward training, registry
├── backtest/              # Walk-forward engine, risk metrics, report generation
├── trading/               # Paper trading, portfolio, signal generation
├── advisor/               # Risk profiling, asset allocation, SIP calculator
├── api/                   # FastAPI routes + WebSocket
└── dashboard/             # Plotly Dash layouts + callbacks
scripts/
├── seed_data.py           # Download and store market data
├── train_model.py         # Walk-forward training CLI
└── run_backtest.py        # Backtesting CLI
```
