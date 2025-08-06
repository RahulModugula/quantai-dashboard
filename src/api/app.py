"""Main FastAPI application with production infrastructure."""
from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from src.api.exception_handlers import register_exception_handlers
from src.api.structured_logging import RequestLoggingMiddleware
from src.config.production import ProductionSettings
from src.health.checks import HealthChecker
from src.monitoring.observability import get_metrics_collector
from src.api.versioning import get_version_info

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("Starting QuantAI Dashboard application")
    health_checker = HealthChecker()
    startup_status = await health_checker.full_health_check()
    logger.info(f"Health check on startup: {startup_status}")

    yield

    # Shutdown
    logger.info("Shutting down QuantAI Dashboard application")
    metrics = get_metrics_collector()
    logger.info(f"Final metrics: {metrics.get_metrics()}")


def create_app(settings: ProductionSettings = None) -> FastAPI:
    """Create and configure FastAPI application."""
    if settings is None:
        settings = ProductionSettings()

    app = FastAPI(
        title="QuantAI Dashboard",
        description="Real-time ML trading dashboard with backtesting",
        version=get_version_info()["current"],
        lifespan=lifespan
    )

    # Add security middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add structured logging middleware
    app.add_middleware(RequestLoggingMiddleware)

    # Register exception handlers
    register_exception_handlers(app)

    # Health check endpoint
    @app.get("/api/health")
    async def health_check():
        """Health check endpoint."""
        health_checker = HealthChecker()
        return await health_checker.full_health_check()

    # Version endpoint
    @app.get("/api/version")
    async def version():
        """API version information."""
        return get_version_info()

    # Metrics endpoint
    @app.get("/api/metrics")
    async def metrics():
        """Application metrics."""
        collector = get_metrics_collector()
        return collector.get_metrics()

    return app
