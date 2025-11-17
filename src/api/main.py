"""
QuantAI Trading Dashboard - FastAPI Application

Mounts:
  /api           - REST API (predictions, portfolio, backtest, advisor, sip)
  /ws/prices     - WebSocket real-time price feed
  /dashboard     - Plotly Dash interactive dashboard (WSGI-mounted)
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, Response

from src.api.middleware import RequestLoggingMiddleware
from src.monitoring.observability import get_prometheus_metrics, get_prometheus_content_type
from src.api.routes import backtest, portfolio, predictions
from src.api.websocket import price_feed_endpoint
from src.data.storage import init_db

logger = logging.getLogger(__name__)

VERSION = "0.2.0"

DISCLAIMER = (
    "DISCLAIMER: This application is for educational purposes only. "
    "All predictions, signals, and portfolio data are simulated and do NOT constitute financial advice. "
    "Backtested results are theoretical and do not guarantee future performance. "
    "Past performance is not indicative of future results."
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""
    # Startup
    init_db()
    logger.info("Database initialized")
    try:
        from src.api.dependencies import get_paper_trader
        trader = get_paper_trader()
        task = asyncio.create_task(trader.run())
        logger.info("Paper trader started")
    except Exception as e:
        logger.warning(f"Paper trader not started: {e}")
        task = None

    yield

    # Shutdown
    if task and not task.done():
        task.cancel()
        logger.info("Paper trader stopped")


def create_app() -> FastAPI:
    app = FastAPI(
        title="QuantAI - ML Trading Dashboard",
        description=f"Real-time ML trading dashboard with backtesting and paper trading.\n\n{DISCLAIMER}",
        version=VERSION,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=lifespan,
    )

    # Middleware — logging first so it wraps everything
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # REST routes
    app.include_router(predictions.router, prefix="/api")
    app.include_router(portfolio.router, prefix="/api")
    app.include_router(backtest.router, prefix="/api")

    try:
        from src.api.routes import data
        app.include_router(data.router, prefix="/api")
    except ImportError:
        logger.warning("Data validation routes not available")

    try:
        from src.api.routes import advisor, optimizer, sip, status, diagnostics, analysis, signals
        app.include_router(advisor.router, prefix="/api")
        app.include_router(sip.router, prefix="/api")
        app.include_router(optimizer.router, prefix="/api")
        app.include_router(status.router, prefix="/api")
        app.include_router(diagnostics.router, prefix="/api")
        app.include_router(analysis.router, prefix="/api")
        app.include_router(signals.router, prefix="/api")
    except ImportError:
        logger.warning("Some optional routes not yet available")

    # WebSocket
    @app.websocket("/ws/prices")
    async def ws_prices(websocket: WebSocket):
        await price_feed_endpoint(websocket)

    # Mount Dash dashboard
    try:
        from a2wsgi import WSGIMiddleware
        from src.dashboard.app import create_dash_app
        dash_app = create_dash_app()
        app.mount("/dashboard", WSGIMiddleware(dash_app.server))
        logger.info("Dash dashboard mounted at /dashboard")
    except Exception as e:
        logger.warning(f"Dashboard not mounted: {e}")

    @app.get("/", include_in_schema=False)
    def root():
        return RedirectResponse(url="/dashboard")

    @app.get("/api/health", tags=["meta"])
    def health_check() -> JSONResponse:
        """Liveness probe — returns 200 when the API is up."""
        return JSONResponse({
            "status": "healthy",
            "version": VERSION,
            "timestamp": datetime.now().isoformat(),
            "disclaimer": DISCLAIMER,
        })

    @app.get("/api/metrics/prometheus", tags=["meta"])
    def prometheus_metrics():
        """Prometheus-format metrics for scraping."""
        return Response(
            content=get_prometheus_metrics(),
            media_type=get_prometheus_content_type(),
        )

    return app


app = create_app()
