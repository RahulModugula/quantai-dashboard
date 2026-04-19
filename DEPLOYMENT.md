# Deployment

Local-first. This repo ships with a `docker-compose.yml` that builds the image
and wires up the dashboard, API, and (optionally) Redis. Cloud deployment is
out of scope for the public repo — the notes below cover the only paths that
are tested end-to-end.

## Prerequisites
- Python 3.11+
- Docker 24+ (if using compose)
- Redis 6+ (optional — caching falls back to in-memory)

## Local (no Docker)

```bash
uv venv .venv --python 3.11
source .venv/bin/activate
make setup      # installs deps + pre-commit hooks
cp .env.example .env
make seed       # downloads 5y OHLCV, builds features
make train      # walk-forward ensemble training
make run        # FastAPI + Dash at http://localhost:8000
```

## Docker Compose

```bash
docker compose up --build
```

Exposes `http://localhost:8000` with the same routes as local mode. Data and
models persist in named volumes so `docker compose down` does not wipe state.

## Database Migrations

Schema changes go through Alembic.

```bash
# After changing src/data/storage.py
alembic revision --autogenerate -m "what changed"
alembic upgrade head   # apply
alembic current        # verify
```

SQLite is the default; pointing `QUANTAI_DB_URL` at a Postgres URI works but is
not exercised in CI.

## Environment Variables

All settings are read via Pydantic with the `QUANTAI_` prefix. The full list is
in `src/config/__init__.py`. The ones that matter for deployment:

| Variable | Purpose |
|----------|---------|
| `QUANTAI_DB_URL` | SQLAlchemy URL. Default: `sqlite:///data/quantai.db` |
| `QUANTAI_REDIS_URL` | Optional. Empty → in-memory cache |
| `QUANTAI_LOG_LEVEL` | `INFO` / `DEBUG` |
| `QUANTAI_AGENT_MODEL` | LiteLLM model string (e.g. `anthropic/claude-3-5-sonnet-20241022`) |
| `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` | One is required for the agent layer |

## Health & Metrics

```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/api/metrics/prometheus
```

Prometheus metrics are exposed at `/api/metrics/prometheus` and cover request
latency and model inference time.

## Known Limitations

- No built-in auth. Do not expose the API publicly without a reverse proxy.
- SQLite is single-writer. For concurrent write load, move to Postgres.
- The agent layer makes outbound HTTPS calls to the LLM provider and to
  `efts.sec.gov`; both must be reachable from the runtime environment.
