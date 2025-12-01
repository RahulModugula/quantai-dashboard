# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libomp-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY src/ src/

# Build wheels
RUN pip install build && python -m build --wheel

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install runtime dependencies (libomp for LightGBM, curl for healthcheck)
RUN apt-get update && apt-get install -y \
    libomp-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy built wheel from builder
COPY --from=builder /app/dist/*.whl /tmp/

# Install the application (wheel already contains src/)
RUN pip install /tmp/*.whl && rm /tmp/*.whl

# Copy scripts and config (not src/ — already installed via wheel)
COPY scripts/ scripts/
COPY alembic/ alembic/
COPY alembic.ini .

# Create data directory
RUN mkdir -p data models

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
