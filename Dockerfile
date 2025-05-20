# Multi-stage build for QuantAI Trading Dashboard

# ---- Builder ----
FROM python:3.11-slim AS builder

WORKDIR /app
COPY pyproject.toml .

RUN pip install --no-cache-dir hatchling && \
    pip install --no-cache-dir \
        yfinance pandas numpy scikit-learn xgboost torch \
        sqlalchemy fastapi uvicorn[standard] dash plotly \
        redis a2wsgi pydantic pydantic-settings joblib \
        websockets httpx dash-bootstrap-components

# ---- Runtime ----
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy source
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY .env.example .env

# Create data and model directories
RUN mkdir -p data/raw data/processed models/registry

EXPOSE 8000

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
