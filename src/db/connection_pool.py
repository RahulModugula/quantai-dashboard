"""Database connection pooling configuration."""
import logging
from typing import Optional
from sqlalchemy import create_engine, event
from sqlalchemy.pool import QueuePool, NullPool
from sqlalchemy.orm import sessionmaker, Session

logger = logging.getLogger(__name__)


class DatabaseConnectionPool:
    """Manage database connection pooling."""

    def __init__(
        self,
        database_url: str,
        pool_size: int = 20,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        echo: bool = False,
    ):
        """Initialize connection pool.

        Args:
            database_url: Database connection URL
            pool_size: Number of connections to keep in pool
            max_overflow: Maximum overflow connections
            pool_timeout: Timeout for getting connection from pool
            pool_recycle: Recycle connections older than this (seconds)
            echo: Whether to log SQL statements
        """
        self.database_url = database_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle

        self.engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
            echo=echo,
        )

        self.session_factory = sessionmaker(bind=self.engine)
        self._setup_event_listeners()
        logger.info(
            f"Database connection pool initialized: "
            f"pool_size={pool_size}, max_overflow={max_overflow}"
        )

    def _setup_event_listeners(self):
        """Setup event listeners for pool management."""

        @event.listens_for(self.engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            logger.debug("New database connection established")

        @event.listens_for(self.engine, "close")
        def receive_close(dbapi_conn, connection_record):
            logger.debug("Database connection closed")

        @event.listens_for(self.engine, "detach")
        def receive_detach(dbapi_conn, connection_record):
            logger.debug("Database connection detached from pool")

    def get_session(self) -> Session:
        """Get a session from the pool."""
        return self.session_factory()

    def get_pool_status(self) -> dict:
        """Get current pool status."""
        pool = self.engine.pool
        return {
            "size": pool.size(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "total": pool.size() + pool.overflow(),
        }

    def close_all(self):
        """Close all connections in pool."""
        self.engine.dispose()
        logger.info("All database connections closed")


# Global connection pool instance
_pool: Optional[DatabaseConnectionPool] = None


def init_pool(
    database_url: str,
    pool_size: int = 20,
    max_overflow: int = 10,
    **kwargs
) -> DatabaseConnectionPool:
    """Initialize global connection pool."""
    global _pool
    _pool = DatabaseConnectionPool(
        database_url, pool_size=pool_size, max_overflow=max_overflow, **kwargs
    )
    return _pool


def get_pool() -> DatabaseConnectionPool:
    """Get global connection pool."""
    if _pool is None:
        raise RuntimeError("Database pool not initialized. Call init_pool first.")
    return _pool


def get_session() -> Session:
    """Get database session from global pool."""
    pool = get_pool()
    return pool.get_session()
