# User Guide

A practical guide to using QuantAI Trading Dashboard for backtesting, analysis, and decision-making.

## Getting Started (5 minutes)

1. **Start the API**
   ```bash
   uvicorn src.api.main:app --reload
   ```

2. **Open the Dashboard**
   Navigate to http://localhost:8000/dashboard

3. **Check System Status**
   ```bash
   curl http://localhost:8000/api/health
   ```

---

## Core Workflows

### Workflow 1: Check Data Freshness

**Goal:** Ensure your market data is ready before making trading decisions.

```bash
# Check which tickers are ready
curl http://localhost:8000/api/status/data

# Response shows:
# - Last update date for each ticker
# - Number of data rows
# - "ready" status
```

**When to use:** Daily, before analyzing portfolios or running backtests

---

### Workflow 2: Get Trading Signals

**Goal:** Get ML-generated buy/sell signals for decision-making.

```bash
# Get signal for one ticker
curl http://localhost:8000/api/predictions/AAPL

# Response includes:
# - probability (0-1, higher = more bullish)
# - signal (STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL)
# - confidence score
```

**Interpreting Signals:**
- `STRONG_BUY`: Very high probability of upward movement (>0.75)
- `BUY`: Moderate confidence upward (0.65-0.75)
- `HOLD`: Neutral signal (0.45-0.55)
- `SELL`: Moderate downside risk (0.25-0.35)
- `STRONG_SELL`: High confidence downward (<0.25)

**Important:** Signals are ML-generated, not financial advice. Always do your own research.

---

### Workflow 3: Check Portfolio Health

**Goal:** Monitor your current portfolio and identify risks.

```bash
# Get current portfolio state
curl http://localhost:8000/api/portfolio

# Response shows:
# - Total portfolio value
# - Cash available
# - Current holdings and their values
# - Overall return percentage
```

**Action Items:**
- If `cash` is low, consider taking profits
- If `cumulative_return` is negative, review trading strategy
- Monitor holdings for concentration

---

### Workflow 4: Get Risk Warnings

**Goal:** Stay aware of portfolio risks before they become problems.

```bash
# Get risk warnings
curl http://localhost:8000/api/portfolio/warnings

# Response includes warnings about:
# - Concentration: Any position >25% of portfolio
# - Correlation: Holdings that move together
# - Drawdown: Current losses vs maximum tolerated
```

**Risk Levels:**
- **Concentration Warning** → Consider diversifying
- **Correlation Warning** → Holdings are redundant, sell one
- **Drawdown Warning** → Position sizing will reduce automatically

---

### Workflow 5: Analyze Sector Exposure

**Goal:** Ensure portfolio is properly diversified across sectors.

```bash
# Get sector breakdown
curl http://localhost:8000/api/analysis/sector-composition

# Response shows:
# - Percentage allocated to each sector
# - Diversification score (0-100)
# - Concentration level
```

**Good Diversification:**
- At least 4-5 different sectors
- No single sector >35% of portfolio
- Diversification score >60

---

### Workflow 6: Backtest a Strategy

**Goal:** Validate trading strategy performance on historical data.

```bash
# Start a backtest
curl -X POST http://localhost:8000/api/backtest/run \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "initial_capital": 100000,
    "buy_threshold": 0.6,
    "sell_threshold": 0.4
  }'

# Response: {"key": "AAPL_100000", "status": "started"}
```

**Wait for completion (1-10 minutes):**
```bash
# Check status
curl http://localhost:8000/api/backtest/result/AAPL_100000

# Once complete, review:
# - Total return
# - Sharpe ratio (risk-adjusted returns)
# - Max drawdown (worst peak-to-trough loss)
# - Win rate (% of profitable trades)
```

**Interpreting Results:**
- **Good Total Return:** >15% annualized
- **Good Sharpe Ratio:** >1.0 (better risk-adjusted performance)
- **Good Win Rate:** >50% (more wins than losses)
- **Good Max Drawdown:** <30% (acceptable risk tolerance)

---

### Workflow 7: Compare Two Strategies

**Goal:** Compare performance of different trading parameters.

```bash
# Run backtest 1
curl -X POST http://localhost:8000/api/backtest/run \
  -d '{"ticker": "AAPL", "buy_threshold": 0.6}'

# Run backtest 2
curl -X POST http://localhost:8000/api/backtest/run \
  -d '{"ticker": "AAPL", "buy_threshold": 0.7}'

# Compare results
curl -X POST "http://localhost:8000/api/backtest/compare?key_a=AAPL_100000&key_b=AAPL_100000_v2"
```

**Comparison shows:**
- Which strategy had better returns
- Which had more trades
- Risk-adjusted performance differences

---

### Workflow 8: Get Rebalancing Suggestions

**Goal:** Rebalance portfolio to target allocation.

```bash
# Get equal-weight rebalancing
curl -X POST http://localhost:8000/api/advisor/rebalance/equal-weight

# Response includes:
# - Which stocks to buy/sell
# - How many shares
# - Target vs current allocation
```

**Before Acting:**
1. Review tax implications (capital gains)
2. Check transaction costs
3. Ensure cash available for buys
4. Execute over multiple days to avoid slippage

---

### Workflow 9: Check Model Quality

**Goal:** Ensure ML model is working properly.

```bash
# Check model features and importance
curl http://localhost:8000/api/diagnostics/model-features

# Response shows:
# - Feature count
# - Feature importance scores
# - Model type being used
```

**Healthy Model Signs:**
- Feature count: 20-50 features
- Top features have significant importance (>5%)
- Importance scores vary (not all equal)

---

### Workflow 10: Export Data for External Analysis

**Goal:** Export backtest results for Excel/Python analysis.

```bash
# Export trades as CSV
curl http://localhost:8000/api/backtest/export/AAPL_100000/trades

# Export equity curve as CSV
curl http://localhost:8000/api/backtest/export/AAPL_100000/equity

# Save to file
> backtest_results.csv
```

**Use Cases:**
- Analyze trades in Excel
- Create custom charts
- Calculate custom metrics
- Share with analysts

---

## Daily Routine

### Morning (5 minutes)

```bash
# 1. Check if system is ready
curl http://localhost:8000/api/status/ready

# 2. Verify data freshness
curl http://localhost:8000/api/status/data

# 3. Check portfolio status
curl http://localhost:8000/api/portfolio

# 4. Review risk warnings
curl http://localhost:8000/api/portfolio/warnings
```

### During Market Hours (as needed)

```bash
# Get latest predictions
curl http://localhost:8000/api/predictions/AAPL
curl http://localhost:8000/api/predictions/GOOGL

# Monitor portfolio performance
curl http://localhost:8000/api/portfolio

# Check for new risk warnings
curl http://localhost:8000/api/portfolio/warnings
```

### End of Day (10 minutes)

```bash
# Review sector exposure
curl http://localhost:8000/api/analysis/sector-composition

# Check if rebalancing needed
curl -X POST http://localhost:8000/api/advisor/rebalance/reduce-risk

# Archive trade history
curl http://localhost:8000/api/portfolio/trades?limit=1000

# Export for record keeping
# Save equity curve and trades CSVs
```

---

## Common Questions

### Q: How often is data updated?

**A:** Data is refreshed daily using your configured data source. Check `/api/status/data` to see when each ticker was last updated.

---

### Q: Can I trust the signals?

**A:** Signals are ML-generated based on historical patterns. They're useful for identifying trends but shouldn't be the only basis for trading decisions. The model accuracy varies by market conditions.

**Typical accuracy:** 52-58% on daily predictions (better than random, but not guaranteed)

---

### Q: How do I know if my backtest results are realistic?

**A:** Check these assumptions:
- Commission: 0.1% (typical)
- Slippage: Not modeled (can impact real trading)
- Order filling: Assumes close price filled (may not execute)
- Data bias: Uses price data that's already known

For more realistic results, compare backtest performance against your actual paper trading returns.

---

### Q: What portfolio size should I start with?

**A:** For paper trading:
- Minimum: $10,000 (allows meaningful position sizing)
- Comfortable: $50,000 - $500,000 (enough for diversification)
- Advanced: $1M+ (can implement more strategies)

Size doesn't affect backtesting, but affects position sizing in live trading.

---

### Q: How often should I retrain the model?

**A:** Retrain monthly or when:
- Market regime changes significantly
- New features are added
- Prediction accuracy declines
- Data distribution shifts

```bash
# Retrain manually
python -m scripts.train_model

# Or use automated weekly retraining
0 2 * * 0 cd /path/to/project && python -m scripts.train_model
```

---

### Q: Can I use different prediction models?

**A:** Currently, the ensemble uses 4 models (RF, XGB, LightGBM, LSTM). You can adjust weights:

```bash
# Weighted ensemble
export QUANTAI_ENSEMBLE_WEIGHTS='{"rf": 0.5, "xgb": 0.5, "lgbm": 0, "lstm": 0}'

# Or use just LightGBM
export QUANTAI_ENSEMBLE_WEIGHTS='{"lgbm": 1.0, "rf": 0, "xgb": 0, "lstm": 0}'
```

---

### Q: How do I handle stock splits/dividends?

**A:** Currently, the dashboard uses raw price data. For adjusted prices:

1. Seed data with dividend-adjusted prices
2. Or adjust positions manually after splits

This is on the roadmap for future versions.

---

## Best Practices

### 1. Always Validate Before Trading

```bash
# Before putting real money:
# 1. Run backtest
# 2. Paper trade for 2+ weeks
# 3. Compare backtest vs real performance
# 4. Understand discrepancies
```

### 2. Diversify Across Sectors

```bash
# Check sector exposure
curl http://localhost:8000/api/analysis/sector-composition

# Target:
# - 5+ sectors represented
# - No sector > 35%
# - Diversification score > 60
```

### 3. Monitor Risk Daily

```bash
# Set up daily risk check
curl http://localhost:8000/api/portfolio/warnings

# Act on warnings:
# - Concentration: Sell concentrated position
# - Correlation: Sell correlated duplicate
# - Drawdown: Reduce position size
```

### 4. Track Transaction Costs

```bash
# Monitor commissions paid
curl http://localhost:8000/api/portfolio/trades

# Calculate total costs
# jq '.trades | map(.commission) | add' response.json
```

### 5. Avoid Overfitting

- Don't obsess over small improvements in backtest
- Test across multiple time periods
- Validate on recent data, not just historical
- Remember: "Past performance ≠ future results"

---

## Limitations & Disclaimers

1. **Educational Only**: This platform is for learning. Not intended for real trading.

2. **Simulation**: Paper trading results don't account for:
   - Slippage on entry/exit
   - Liquidity constraints
   - Psychological trading stress
   - Real-world market impact

3. **Model Risk**: ML models are:
   - Dependent on historical patterns
   - Poor at predicting regime changes
   - Subject to overfitting
   - Frequently need retraining

4. **Data Quality**: Results depend on:
   - Data accuracy
   - Historical completeness
   - Survivorship bias

5. **No Financial Advice**: Nothing here is financial advice. Consult a registered advisor before real investing.

---

## Getting Help

- **API Docs:** http://localhost:8000/api/docs
- **Status:** http://localhost:8000/api/status/ready
- **Troubleshooting:** See TROUBLESHOOTING.md
- **API Reference:** See API_REFERENCE.md
