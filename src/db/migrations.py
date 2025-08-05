"""Database schema migrations."""
import logging

logger = logging.getLogger(__name__)


class MigrationManager:
    """Manage database migrations."""

    def __init__(self, engine):
        self.engine = engine
        self.migrations = {}

    def register_migration(self, version: str, migration_func):
        """Register a migration."""
        self.migrations[version] = migration_func
        logger.info(f"Registered migration: {version}")

    def run_migrations(self):
        """Run pending migrations."""
        from sqlalchemy import text

        with self.engine.connect() as conn:
            # Create migrations table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(50) PRIMARY KEY
                )
            """))
            conn.commit()

            # Get applied migrations
            result = conn.execute(text("SELECT version FROM schema_migrations"))
            applied = {row[0] for row in result}

            # Run pending migrations
            for version in sorted(self.migrations.keys()):
                if version not in applied:
                    logger.info(f"Running migration: {version}")
                    self.migrations[version](conn)
                    conn.execute(text(f"INSERT INTO schema_migrations (version) VALUES ('{version}')"))
                    conn.commit()
                    logger.info(f"Completed migration: {version}")

    def get_applied_migrations(self) -> list:
        """Get list of applied migrations."""
        from sqlalchemy import text

        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT version FROM schema_migrations ORDER BY version"))
            return [row[0] for row in result]
