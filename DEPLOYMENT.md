# Deployment Guide

This guide covers deploying QuantAI to production and scaling considerations.

## Prerequisites

- Python 3.11+
- PostgreSQL 13+ (for production)
- Redis 6+ (optional, for caching)
- 4GB+ RAM, 10GB+ disk space

## Local Development Setup

```bash
# Clone and setup
git clone https://github.com/RahulModugula/quantai-dashboard.git
cd quantai-dashboard
make setup    # installs deps + pre-commit hooks

# Configure
cp .env.example .env
# Edit .env with your settings

# Run database migrations
make migrate

# Seed initial data and train model
make seed
make train

# Start API
make run
```

Then open http://localhost:8000/dashboard

## Docker Deployment

### Build Image

```bash
docker build -t quantai:latest .
```

### Run Container

```bash
docker run -d \
  --name quantai \
  -p 8000:8000 \
  -v quantai-data:/app/data \
  -e QUANTAI_DB_URL=sqlite:///data/quantai.db \
  quantai:latest
```

## Cloud Deployment (AWS Example)

### 1. Prepare RDS Database

```bash
# Create RDS instance for PostgreSQL
aws rds create-db-instance \
  --db-instance-identifier quantai-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --allocated-storage 20
```

### 2. Deploy to ECS

```bash
# Push image to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <ECR_URI>
docker tag quantai:latest <ECR_URI>/quantai:latest
docker push <ECR_URI>/quantai:latest

# Create ECS task definition and service
# (See ECS console or use AWS CLI)
```

### 3. Set Environment Variables

```bash
# AWS Secrets Manager
aws secretsmanager create-secret \
  --name quantai/prod \
  --secret-string '{
    "QUANTAI_DB_URL": "postgresql://user:pass@rds-endpoint:5432/quantai",
    "QUANTAI_REDIS_URL": "redis://elasticache-endpoint:6379",
    "QUANTAI_API_KEY": "secret-api-key"
  }'
```

## Production Configuration

### Database

```env
# Use PostgreSQL, not SQLite
QUANTAI_DB_URL=postgresql://user:password@db.example.com:5432/quantai_prod

# Connection pool
QUANTAI_DB_POOL_SIZE=20
QUANTAI_DB_MAX_OVERFLOW=10
```

### Caching

```env
# Enable Redis for production caching
QUANTAI_REDIS_URL=redis://cache.example.com:6379/0
QUANTAI_CACHE_TTL=300  # 5 minutes
```

### API Security

```env
# Rate limiting
QUANTAI_RATE_LIMIT=1000  # per hour
QUANTAI_BURST_SIZE=50    # per minute

# CORS
QUANTAI_ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# API Key (optional authentication)
QUANTAI_API_KEY=long-random-secret-key
```

### Logging

```env
# Structured logging for production
QUANTAI_LOG_LEVEL=INFO
QUANTAI_LOG_FORMAT=json
QUANTAI_LOG_DESTINATION=cloudwatch  # or file, syslog
```

## Database Migrations

Schema changes are tracked with Alembic. Never modify tables directly in production.

```bash
# Create a new migration after changing src/data/storage.py
alembic revision --autogenerate -m "Add column to trades table"

# Review the generated migration
cat alembic/versions/<hash>_add_column_to_trades_table.py

# Apply in staging first
QUANTAI_DB_PATH=staging.db alembic upgrade head

# Then production (backup first)
cp data/trading.db data/trading.db.bak
alembic upgrade head

# Verify current version
alembic current
```

## Monitoring & Alerts

### Health Checks

```bash
# Kubernetes liveness probe
curl http://localhost:8000/api/health

# Readiness check
curl http://localhost:8000/api/status/ready
```

### Metrics to Monitor

```
- API response time (p50, p95, p99)
- Error rate (5xx errors)
- Model prediction latency
- Backtest execution time
- Cache hit rate
- Database query time
```

### Suggested Tools

- **Prometheus** — Scrape `/api/metrics/prometheus` for request latency, model inference time, prediction distribution
- **Grafana** — Dashboard visualization
- **structlog** — JSON-formatted logs in production (set `QUANTAI_ENV=production`)

## Performance Tuning

### Database

```python
# Add indexes for common queries
CREATE INDEX idx_trades_date ON trades(date);
CREATE INDEX idx_features_ticker ON features(ticker, date);
```

### Caching Strategy

```
- Cache predictions for 1 hour
- Cache portfolio history for 5 minutes
- Cache diagnostics for 30 minutes
- Invalidate on portfolio updates
```

### API Response Times

| Endpoint | Target | Method |
|----------|--------|--------|
| `/predictions/{ticker}` | <500ms | Cache (1h TTL) |
| `/portfolio` | <200ms | Cache (5m TTL) |
| `/backtest/run` | Async | Background task |
| `/analysis/sector-composition` | <1s | Cache (10m TTL) |

## Backup & Disaster Recovery

### Database Backup

```bash
# Daily automated backups
0 2 * * * pg_dump quantai_prod | gzip > /backups/quantai_$(date +\%Y\%m\%d).sql.gz
```

### Data Retention

- Market data: Keep last 2 years
- Trades: Keep last 5 years
- Backtest results: Keep last 1 year
- Predictions: Keep last 30 days

## Scaling Considerations

### Horizontal Scaling

```yaml
# Kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: quantai-api
spec:
  replicas: 3  # Scale to 3+ pods
  selector:
    matchLabels:
      app: quantai-api
  template:
    metadata:
      labels:
        app: quantai-api
    spec:
      containers:
      - name: quantai
        image: quantai:latest
        ports:
        - containerPort: 8000
```

### Load Balancing

- Use AWS ALB or nginx for load balancing
- Session affinity: Not needed (stateless API)
- Sticky sessions: Not needed

## Security Checklist

- [ ] HTTPS enabled (TLS 1.2+)
- [ ] API key authentication enabled
- [ ] CORS properly configured
- [ ] SQL injection protection (via ORM)
- [ ] Rate limiting enabled
- [ ] Secrets in environment variables (not code)
- [ ] Database encrypted at rest
- [ ] Database connections encrypted (SSL)
- [ ] API logs don't contain PII
- [ ] Regular dependency updates

## Troubleshooting

### High Memory Usage

```bash
# Check which endpoints are memory-intensive
# Solution: Add pagination, streaming for large results
```

### Slow Predictions

```bash
# Check model loading time
# Solution: Pre-load models, use model caching
```

### Database Connection Errors

```bash
# Increase connection pool
QUANTAI_DB_POOL_SIZE=30
QUANTAI_DB_MAX_OVERFLOW=20
```

## Cost Optimization

- Use spot instances for backtesting jobs
- Schedule data refresh during off-peak hours
- Archive old backtest results to S3
- Use CloudFront CDN for static assets

## Support

For deployment issues:
1. Check `/api/health` endpoint
2. Review logs: `docker logs quantai` or CloudWatch
3. Validate config: `GET /api/diagnostics/validate-config`
4. Check data freshness: `GET /api/status/data`
