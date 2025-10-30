# Troubleshooting Guide

Common issues and solutions for QuantAI Trading Dashboard.

## Installation & Setup

### Issue: `ImportError: No module named 'quantai'`

**Cause:** Package not installed or virtual environment not activated.

**Solution:**
```bash
# Make sure you're in the project directory
cd profile-max

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

---

### Issue: `ModuleNotFoundError: No module named 'src.api'`

**Cause:** PYTHONPATH not set correctly.

**Solution:**
```bash
# Make sure you're running from project root
pwd  # Should end with /profile-max

# For development
python -m uvicorn src.api.main:app --reload

# For scripts
python -m scripts.train_model
```

---

### Issue: `RuntimeError: Failed to initialize database`

**Cause:** Database file is locked or permissions issue.

**Solution:**
```bash
# Check database exists
ls -la data/

# Delete and reinitialize
rm data/quantai.db
python -m scripts.init_db

# Or specify a different database path
export QUANTAI_DATA_DIR=/tmp/quantai-data
python -m scripts.init_db
```

---

## Data Issues

### Issue: "No feature data for AAPL"

**Cause:** `seed_data.py` hasn't been run for this ticker.

**Solution:**
```bash
# Run data seeding for specific ticker
python -m scripts.seed_data --ticker AAPL

# Run for all configured tickers
python -m scripts.seed_data

# Check data status
curl http://localhost:8000/api/status/data
```

---

### Issue: "Data is too stale (>7 days old)"

**Cause:** Market data hasn't been updated recently.

**Solution:**
```bash
# Refresh data
python -m scripts.seed_data --refresh

# Check how old your data is
curl http://localhost:8000/api/data/summary

# Validate specific ticker
curl -X POST http://localhost:8000/api/data/validate/AAPL
```

---

### Issue: "Missing rows: Expected 500, got 100"

**Cause:** Insufficient historical data available.

**Solution:**
```bash
# Check your data source configuration
cat .env | grep QUANTAI_DATA

# Try a different ticker with more data
# (e.g., well-established companies like AAPL, MSFT)

# Or extend the data collection period
export QUANTAI_MIN_SAMPLES=50  # Reduce minimum
python -m scripts.seed_data --ticker AAPL
```

---

## Model & Predictions

### Issue: "No trained model available"

**Cause:** Model hasn't been trained yet.

**Solution:**
```bash
# Train the model
python -m scripts.train_model

# This may take 5-30 minutes depending on data size

# Check if model file exists
ls -la models/

# Check readiness
curl http://localhost:8000/api/status/ready
```

---

### Issue: "Model predictions are always around 0.5"

**Cause:** Model isn't converging (random guessing).

**Solution:**
```bash
# Check feature quality
curl http://localhost:8000/api/diagnostics/feature-correlation

# Look for high correlation between features (>0.9)
# These should be removed or combined

# Retrain with cleaned features
python -m scripts.train_model --clean-features

# Check model performance
curl http://localhost:8000/api/diagnostics/model-features
```

---

### Issue: "Inconsistent prediction signals between API calls"

**Cause:** Model uses random features or non-deterministic components.

**Solution:**
```bash
# Ensure random seeds are set
export QUANTAI_RANDOM_SEED=42

# Retrain
python -m scripts.train_model

# Predictions should now be deterministic
```

---

## API Issues

### Issue: `ConnectionError: Failed to connect to Redis`

**Cause:** Redis is not running (optional but recommended).

**Solution:**
```bash
# Start Redis
redis-server

# Or disable Redis caching
export QUANTAI_REDIS_URL=""

# API will fall back to in-memory cache (slower)
```

---

### Issue: `500 Internal Server Error` on /portfolio endpoint

**Cause:** Portfolio object is corrupted or incomplete.

**Solution:**
```bash
# Check API logs
curl http://localhost:8000/api/health

# Reset portfolio (WARNING: loses trading history)
python -m scripts.reset_portfolio

# Restart API
# Kill existing process and start fresh
```

---

### Issue: "Rate limit exceeded (1000 req/hour)"

**Cause:** Too many API requests.

**Solution:**
```bash
# Increase rate limit in .env
export QUANTAI_RATE_LIMIT=2000

# Or cache responses on your client side
# Store responses for 5 minutes

# Check current limits
curl -I http://localhost:8000/api/portfolio
# Look for X-RateLimit-* headers
```

---

### Issue: Backtest endpoint returns `202 Accepted` indefinitely

**Cause:** Background task is hanging.

**Solution:**
```bash
# Check if backtest is actually running
curl http://localhost:8000/api/backtest/results

# Try a smaller backtest
# Reduce date range or initial capital

# If truly stuck, restart API
# Kill and restart the server

# Check logs for specific error
tail -f logs/api.log
```

---

## Performance Issues

### Issue: API response time >1 second for /portfolio

**Cause:** Large portfolio or slow database.

**Solution:**
```bash
# Enable caching (if using Redis)
export QUANTAI_REDIS_URL=redis://localhost:6379

# Reduce portfolio size (archive old trades)
python -m scripts.archive_trades --before 2025-01-01

# Add database indexes
python -m scripts.optimize_db
```

---

### Issue: Model training takes >1 hour

**Cause:** Large dataset or slow CPU.

**Solution:**
```bash
# Reduce training data window
export QUANTAI_TRAINING_WINDOW_DAYS=500  # Default: 1000

# Reduce number of features
# Edit feature engineering in data/features.py

# Use faster model
export QUANTAI_ENSEMBLE_WEIGHTS='{"lgbm": 1.0}'  # Just LightGBM

# Retrain
python -m scripts.train_model
```

---

### Issue: Backtest takes >30 minutes

**Cause:** Long date range or frequent trades.

**Solution:**
```bash
# Reduce backtest date range
# Use POST /api/backtest/run with specific dates

# Reduce number of trades (increase thresholds)
curl -X POST http://localhost:8000/api/backtest/run \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "buy_threshold": 0.7,
    "sell_threshold": 0.3
  }'

# Run in background and check progress
# Status endpoint should show progress
```

---

## Database Issues

### Issue: `sqlite3.OperationalError: database is locked`

**Cause:** Multiple processes writing to SQLite simultaneously.

**Solution:**
```bash
# SQLite doesn't handle concurrency well

# Option 1: Use single-threaded mode
export QUANTAI_DB_URL=sqlite:///data/quantai.db?check_same_thread=false

# Option 2: Switch to PostgreSQL (recommended for production)
# Install PostgreSQL
# Update QUANTAI_DB_URL to postgresql://user:pass@localhost/quantai
```

---

### Issue: "Disk space full" error

**Cause:** Database or logs are too large.

**Solution:**
```bash
# Check disk usage
df -h

# Archive old trades (to CSV)
curl -X GET http://localhost:8000/api/backtest/export/{key}/trades

# Clean up old backtest results
python -m scripts.cleanup_old_backtests --days 30

# Compress logs
gzip logs/*.log

# Shrink database
python -m scripts.vacuum_db
```

---

## Configuration Issues

### Issue: "ensemble_weights don't sum to 1.0"

**Cause:** Weight configuration is invalid.

**Solution:**
```bash
# Check current config
curl -X POST http://localhost:8000/api/diagnostics/validate-config

# Fix weights in .env
# They should sum to 1.0
export QUANTAI_ENSEMBLE_WEIGHTS='{"rf": 0.3, "xgb": 0.3, "lgbm": 0.25, "lstm": 0.15}'

# Verify
curl -X POST http://localhost:8000/api/diagnostics/validate-config
```

---

### Issue: "buy_threshold must be > sell_threshold"

**Cause:** Threshold values are in wrong order.

**Solution:**
```bash
# Fix in .env
export QUANTAI_BUY_THRESHOLD=0.65   # Higher (more bullish)
export QUANTAI_SELL_THRESHOLD=0.35  # Lower (more bearish)

# Verify
curl -X POST http://localhost:8000/api/diagnostics/validate-config
```

---

## Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test

```bash
pytest tests/test_api/test_integration_workflows.py::TestDataStatusWorkflow -v
```

### Run with Coverage

```bash
pytest tests/ --cov=src --cov-report=html
# Open htmlcov/index.html
```

---

## Logs

### Enable Debug Logging

```bash
export QUANTAI_LOG_LEVEL=DEBUG
python -m uvicorn src.api.main:app --reload
```

### Check Logs

```bash
# API logs
tail -f logs/api.log | grep ERROR

# Training logs
tail -f logs/training.log

# System logs (macOS)
log stream --predicate 'process == "python"'
```

---

## Debugging

### Enable Print Debugging

```python
# In your code
import sys
print("Debug value:", variable, file=sys.stderr)

# In terminal
python script.py 2>&1 | grep "Debug"
```

### Use Python Debugger

```bash
# Add breakpoint in code
# breakpoint()  # Python 3.7+
# Or: import pdb; pdb.set_trace()

# Run with debugger
python -m pdb script.py
```

### Check API Response Details

```bash
# Verbose curl
curl -v http://localhost:8000/api/portfolio

# Pretty print JSON
curl http://localhost:8000/api/portfolio | python -m json.tool

# Save to file for inspection
curl http://localhost:8000/api/portfolio > response.json
```

---

## Getting Help

1. **Check status endpoints first**
   ```bash
   curl http://localhost:8000/api/health
   curl http://localhost:8000/api/status/ready
   curl http://localhost:8000/api/status/data
   ```

2. **Validate configuration**
   ```bash
   curl -X POST http://localhost:8000/api/diagnostics/validate-config
   ```

3. **Check logs**
   ```bash
   tail -f logs/*.log
   ```

4. **Reproduce with minimal example**
   - Use a single ticker
   - Use recent data
   - Check with curl before Python client

5. **Search existing issues**
   - GitHub issues
   - Stack Overflow
   - Project documentation

---

## Still Stuck?

Try these systematic steps:

1. **Isolate:** Is it API, model, data, or config?
2. **Verify:** Check all related status endpoints
3. **Validate:** Run diagnostic endpoints
4. **Reset:** Clean and reinitialize if needed
5. **Retry:** Test with a minimal example

**Emergency Reset:**
```bash
# This will start fresh (loses all data)
rm -rf data/ models/ logs/
python -m scripts.init_db
python -m scripts.seed_data
python -m scripts.train_model
```

---

## Performance Checklist

- [ ] Redis is running (if enabled)
- [ ] Database indexes are created
- [ ] Data is recent (<7 days old)
- [ ] Model is trained and ready
- [ ] Configuration is validated
- [ ] No hanging background tasks
- [ ] Disk space available (>1GB free)
- [ ] Memory usage normal (<2GB)
