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

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libomp-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy built wheel from builder
COPY --from=builder /app/dist/*.whl /tmp/

# Install the application
RUN pip install /tmp/*.whl && rm /tmp/*.whl

# Copy application code
COPY src/ src/
COPY .env.example .env

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run the application
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
