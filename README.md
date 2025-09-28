# QuantAI — Real-Time ML Trading Dashboard

> **DISCLAIMER**: This project is for **educational purposes only**. All predictions, signals, and portfolio data are simulated. Nothing here constitutes financial advice. Backtested results are theoretical and do not guarantee future performance.

A full-stack ML trading dashboard combining data engineering, machine learning, walk-forward backtesting, paper trading simulation, portfolio optimization, and an interactive Plotly Dash frontend — all served through a single FastAPI server.

---

## Features

### ML Ensemble Model
- **Random Forest + XGBoost + LightGBM + LSTM** weighted ensemble
- Predicts next-day price direction (binary classification)
- Walk-forward training with expanding windows — no look-ahead bias
- Model versioning with joblib + metadata JSON
- **Optuna hyperparameter optimization** for strategy thresholds
- **Model drift detection** with rolling accuracy monitoring

### Feature Engineering (27+ features)
| Category | Features |
|----------|----------|
| Momentum | RSI-14, MACD (12/26/9), Rate of Change (5d, 20d), Lagged Returns (1-5d) |
| Volatility | Bollinger Bands (%B, bandwidth), ATR-14, Rolling std (5d, 20d) |
| Trend | ADX-14, Stochastic Oscillator (%K, %D), Price/SMA50, Price/SMA200, SMA50/SMA200 |
| Mean Reversion | Z-score vs 20-day rolling mean |
| Volume | Volume ratio vs 20d avg, OBV z-score |
| Macro | VIX close, VIX regime (above/below 20d MA) |

### Portfolio Optimization
- **Efficient Frontier** visualization (mean-variance optimization)
- **Max Sharpe Ratio** portfolio via PyPortfolioOpt
- **Minimum Volatility** portfolio
- **Hierarchical Risk Parity (HRP)** — no expected return estimates needed
- Cross-asset **correlation matrix** analysis

### Backtesting Engine
- Walk-forward validation with configurable window size
- **No look-ahead bias**: predictions[t] use only data before t
- Risk metrics: Sharpe, Sortino, Calmar, Max Drawdown, Win Rate, Profit Factor
- **Benchmark comparison** — alpha, beta vs SPY
- **Rolling Sharpe ratio** over trailing windows
- **Monte Carlo simulation** — confidence intervals on terminal value
- Monthly return heatmap, drawdown periods with duration tracking
- CSV export for trades and equity curve

### Paper Trading
- Asyncio-based virtual trading loop with async lock for concurrency safety
- **Half-Kelly criterion** position sizing (probability-weighted)
- **Max drawdown constraint** — reduces exposure when drawdown limit hit
- Signal thresholds (buy/sell) tunable per strategy
- Redis cache for real-time price distribution

### SIP Calculator
- Pre-tax corpus projection
- Post-tax (LTCG-aware) corpus
- Inflation-adjusted real value
- Annual step-up SIP support
- **Reverse SIP** — goal-based planning ("how much monthly for X target?")

### Financial Advisor
- Risk profiling: age, horizon, income stability, loss tolerance, emergency fund, debt ratio
- Asset allocation by risk category: Conservative / Moderate / Aggressive / Very Aggressive
- Portfolio rebalancing recommendations

### Dashboard (Plotly Dash)
- Live candlestick chart with 120-day history
- Model signal display (buy/sell/hold) with confidence
- Feature importance visualization
- Portfolio equity curve with holdings table
- Backtest runner with equity and drawdown charts
- SIP calculator with growth chart
- Advisor panel with allocation pie chart
- **Portfolio Optimizer** tab with efficient frontier + allocation pie
- **Dark mode toggle**

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

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Data | yfinance, pandas, SQLite (SQLAlchemy Core) |
| ML | scikit-learn, XGBoost, LightGBM, PyTorch (LSTM), Optuna |
| Portfolio | PyPortfolioOpt (efficient frontier, HRP) |
| API | FastAPI, WebSocket |
| Dashboard | Plotly Dash (mounted via WSGIMiddleware) |
| Cache | Redis |
| CI/CD | GitHub Actions (lint + test), pre-commit hooks |
| Infra | Docker Compose |

---

## Quick Start

### Option 1: Docker

```bash
docker compose up --build
```

Then open [http://localhost:8000/dashboard](http://localhost:8000/dashboard)

### Option 2: Local Development

```bash
# Create virtual environment
uv venv .venv --python 3.11
source .venv/bin/activate

# Install dependencies
make setup

# Download market data and build features (includes VIX/Treasury)
make seed

# Train the ensemble model (walk-forward)
make train

# Run backtest and save report
make backtest

# Start the server
make run
```

### API Docs

Once running, visit [http://localhost:8000/api/docs](http://localhost:8000/api/docs) for interactive Swagger documentation.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/predictions/{ticker}` | Latest model prediction |
| GET | `/api/portfolio/` | Current portfolio state |
| GET | `/api/portfolio/trades` | Trade history |
| POST | `/api/backtest/run` | Trigger walk-forward backtest |
| POST | `/api/advisor/risk-profile` | Score risk profile |
| GET | `/api/advisor/allocation/{category}` | Get allocation suggestion |
| POST | `/api/sip/calculate` | SIP projection |
| POST | `/api/sip/reverse` | Reverse SIP (goal-based) |
| POST | `/api/optimizer/portfolio` | Optimize portfolio weights |
| POST | `/api/optimizer/frontier` | Compute efficient frontier |
| POST | `/api/optimizer/tune` | Optuna threshold optimization |

---

## Design Decisions

### Why walk-forward expanding windows?
Expanding windows use all available historical data for each training fold, which is more stable for tree-based models. The key constraint is enforced strictly: predictions generated at time `t` use **only** data from before `t`.

### Why classification instead of regression?
Predicting direction (up/down) is more actionable for generating trading signals than predicting return magnitude. Direction classification also produces calibrated probabilities that map cleanly to position sizing.

### Why four ensemble members?
RF and XGBoost capture different interaction patterns. LightGBM trains faster and often outperforms XGBoost on financial data due to leaf-wise growth. LSTM adds temporal sequence signal. Dynamic weighting (0.3/0.3/0.25/0.15) reduces reliance on any single model.

### Why Half-Kelly position sizing?
Full Kelly criterion is optimal but volatile. Half-Kelly provides ~75% of the growth rate with significantly lower drawdowns — a better risk/reward tradeoff for simulated trading.

### Survivorship Bias
The current implementation downloads data for tickers specified in config. For a research-grade backtest, you would want to include delisted companies. This is documented as a limitation.

---

## Running Tests

```bash
make test
```

68 tests covering:
- Feature engineering (RSI bounds, Bollinger ordering, stochastic, ADX, SMA ratios)
- Backtest metrics (Sharpe, max drawdown, Monte Carlo, monthly heatmap)
- SIP calculator (forward + reverse, step-up behavior)
- Portfolio operations (buy/sell/PnL/drawdown constraint)
- Signal generation (Kelly criterion, threshold behavior)
- Model drift detection (degradation alerts)
- Storage module (parameterized queries)
- Portfolio optimizer (weight cleaning)

---

## Project Structure

```
src/
├── config.py              # Pydantic Settings with validators
├── data/
│   ├── ingestion.py       # Data providers, yfinance, macro features
│   ├── features.py        # 27+ technical indicators
│   ├── storage.py         # SQLite with parameterized queries
│   ├── correlation.py     # Cross-asset correlation matrix
│   └── schemas.py         # Pydantic data models
├── models/
│   ├── ensemble.py        # RF + XGB + LightGBM + LSTM
│   ├── lstm.py            # PyTorch LSTM with gradient clipping
│   ├── training.py        # Walk-forward training pipeline
│   ├── tuning.py          # Optuna hyperparameter optimization
│   ├── drift.py           # Model performance monitoring
│   └── registry.py        # Model versioning (joblib)
├── backtest/
│   ├── engine.py          # Walk-forward backtester
│   ├── metrics.py         # Risk metrics + benchmark comparison
│   └── report.py          # Monte Carlo, heatmaps, CSV export
├── trading/
│   ├── portfolio.py       # Virtual portfolio with drawdown limits
│   ├── signals.py         # Kelly criterion position sizing
│   └── paper_trader.py    # Async trading loop with concurrency lock
├── advisor/
│   ├── risk_profile.py    # Risk scoring
│   ├── allocation.py      # Static allocation templates
│   ├── optimizer.py       # PyPortfolioOpt (EF, HRP, MinVol)
│   ├── sip.py             # Forward + reverse SIP calculator
│   └── recommendations.py # Rebalancing suggestions
├── api/
│   ├── main.py            # FastAPI app factory
│   ├── routes/            # REST endpoints
│   └── websocket.py       # Real-time price feed
└── dashboard/
    ├── app.py             # Dash app with 6 tabs + dark mode
    ├── layouts/           # UI components
    └── callbacks/         # Interactive behavior
```

---

## License

MIT
