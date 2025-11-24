"""Graceful shutdown handlers for application termination."""

import logging
import asyncio
import signal
from typing import Callable, List
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class GracefulShutdownManager:
    """Manage graceful application shutdown."""

    def __init__(self, timeout: int = 30):
        """Initialize shutdown manager.

        Args:
            timeout: Seconds to wait for in-flight requests before force shutdown
        """
        self.timeout = timeout
        self.shutdown_handlers: List[Callable] = []
        self.shutdown_event = asyncio.Event()
        self.in_flight_requests = 0

    def register_handler(self, handler: Callable):
        """Register a shutdown handler.

        Args:
            handler: Async function to call on shutdown
        """
        self.shutdown_handlers.append(handler)
        logger.info(f"Registered shutdown handler: {handler.__name__}")

    async def execute_shutdown(self):
        """Execute all registered shutdown handlers."""
        logger.info("Starting graceful shutdown sequence")

        # Wait for in-flight requests to complete (with timeout)
        try:
            await asyncio.wait_for(self._wait_for_requests(), timeout=self.timeout)
        except asyncio.TimeoutError:
            logger.warning(
                f"Timeout waiting for in-flight requests. "
                f"{self.in_flight_requests} requests still pending."
            )

        # Run shutdown handlers
        for handler in self.shutdown_handlers:
            try:
                await handler()
                logger.info(f"Shutdown handler completed: {handler.__name__}")
            except Exception as e:
                logger.error(f"Error in shutdown handler {handler.__name__}: {e}")

        logger.info("Graceful shutdown completed")
        self.shutdown_event.set()

    async def _wait_for_requests(self):
        """Wait for all in-flight requests to complete."""
        while self.in_flight_requests > 0:
            await asyncio.sleep(0.1)

    def increment_requests(self):
        """Increment in-flight request counter."""
        self.in_flight_requests += 1

    def decrement_requests(self):
        """Decrement in-flight request counter."""
        self.in_flight_requests = max(0, self.in_flight_requests - 1)

    def trigger_shutdown(self):
        """Trigger shutdown sequence."""
        asyncio.create_task(self.execute_shutdown())


# Global shutdown manager
_shutdown_manager = GracefulShutdownManager()


def get_shutdown_manager() -> GracefulShutdownManager:
    """Get global shutdown manager."""
    return _shutdown_manager


@asynccontextmanager
async def track_request():
    """Context manager to track in-flight request."""
    manager = get_shutdown_manager()
    manager.increment_requests()
    try:
        yield
    finally:
        manager.decrement_requests()


def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown."""
    manager = get_shutdown_manager()

    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}. Initiating graceful shutdown.")
        manager.trigger_shutdown()

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    logger.info("Signal handlers registered for graceful shutdown")
