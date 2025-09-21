"""
PostgreSQL client for Nexios using asyncpg.

This module provides async PostgreSQL database connectivity for Nexios applications
with connection pooling, session management, and database utilities.
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Union, TypeVar, Generic

try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False

from pydantic import BaseModel
from nexios.exceptions import NexiosException

T = TypeVar('T')

logger = logging.getLogger(__name__)


class DatabaseError(NexiosException):
    """Database-related errors."""
    pass


class ConnectionError(DatabaseError):
    """Connection-related errors."""
    pass


class QueryError(DatabaseError):
    """Query execution errors."""
    pass


class DatabaseConfig(BaseModel):
    """Database configuration."""

    host: str = "localhost"
    port: int = 5432
    database: str = "nexios"
    user: str = "postgres"
    password: str = ""
    min_size: int = 5
    max_size: int = 20
    command_timeout: int = 60
    server_hostname: Optional[str] = None
    server_settings: Optional[Dict[str, str]] = None
    connection_class: Optional[Any] = None
    record_class: Optional[Any] = None

    def get_connection_string(self) -> str:
        """Generate connection string from config."""
        return (
            f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        )


class DatabaseClient:
    """
    Async PostgreSQL client with connection pooling for Nexios.

    Provides connection pooling, query execution, and database management utilities.
    """

    def __init__(self, config: DatabaseConfig):
        """Initialize database client with configuration."""
        if not ASYNCPG_AVAILABLE:
            raise ImportError(
                "asyncpg is required for PostgreSQL support. "
                "Install it with: pip install asyncpg"
            )

        self.config = config
        self._pool: Optional[asyncpg.Pool] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the database connection pool."""
        if self._initialized:
            return

        try:
            self._pool = await asyncpg.create_pool(
                self.config.get_connection_string(),
                min_size=self.config.min_size,
                max_size=self.config.max_size,
                command_timeout=self.config.command_timeout,
                server_hostname=self.config.server_hostname,
                server_settings=self.config.server_settings,
                connection_class=self.config.connection_class,
                record_class=self.config.record_class,
            )
            self._initialized = True
            logger.info(f"Database pool initialized: {self.config.database}")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise ConnectionError(f"Database initialization failed: {e}")

    async def close(self) -> None:
        """Close the database connection pool."""
        if self._pool:
            await self._pool.close()
            self._initialized = False
            logger.info("Database pool closed")

    async def acquire(self) -> asyncpg.Connection:
        """Acquire a connection from the pool."""
        if not self._pool:
            raise ConnectionError("Database pool not initialized")
        return await self._pool.acquire()

    @asynccontextmanager
    async def connection(self):
        """Context manager for database connections."""
        conn = None
        try:
            conn = await self.acquire()
            yield conn
        finally:
            if conn:
                await self._pool.release(conn)  # type: ignore

    async def execute(self, query: str, *args, timeout: Optional[float] = None) -> str:
        """Execute a query and return the result status."""
        async with self.connection() as conn:
            return await conn.execute(query, *args, timeout=timeout)

    async def fetch(self, query: str, *args, timeout: Optional[float] = None) -> List[asyncpg.Record]:
        """Execute a query and return all rows."""
        async with self.connection() as conn:
            return await conn.fetch(query, *args, timeout=timeout)

    async def fetchrow(self, query: str, *args, timeout: Optional[float] = None) -> Optional[asyncpg.Record]:
        """Execute a query and return the first row."""
        async with self.connection() as conn:
            return await conn.fetchrow(query, *args, timeout=timeout)

    async def fetchval(self, query: str, *args, column: int = 0, timeout: Optional[float] = None) -> Any:
        """Execute a query and return the first column of the first row."""
        async with self.connection() as conn:
            return await conn.fetchval(query, *args, column=column, timeout=timeout)

    async def executemany(self, query: str, args_list: List[tuple], timeout: Optional[float] = None) -> None:
        """Execute a query multiple times with different parameters."""
        async with self.connection() as conn:
            await conn.executemany(query, args_list, timeout=timeout)

    async def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            async with self.connection() as conn:
                await conn.fetchval("SELECT 1")
                return True
        except Exception:
            return False

    async def get_pool_info(self) -> Dict[str, Any]:
        """Get connection pool information."""
        if not self._pool:
            return {"status": "not_initialized"}

        return {
            "status": "initialized",
            "min_size": self.config.min_size,
            "max_size": self.config.max_size,
            "size": self._pool.get_size(),
            "free_size": self._pool.get_free_size(),
        }


class DatabaseManager:
    """
    High-level database manager for Nexios applications.

    Provides application-level database management with lifecycle support.
    """

    def __init__(self, config: DatabaseConfig):
        """Initialize database manager."""
        self.config = config
        self.client: Optional[DatabaseClient] = None

    async def __aenter__(self) -> DatabaseClient:
        """Async context manager entry."""
        await self.initialize()
        return self.client  # type: ignore

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

    async def initialize(self) -> DatabaseClient:
        """Initialize the database client."""
        if self.client is None:
            self.client = DatabaseClient(self.config)
            await self.client.initialize()
        return self.client

    async def close(self) -> None:
        """Close the database client."""
        if self.client:
            await self.client.close()
            self.client = None

    async def health_check(self) -> bool:
        """Check database health."""
        if self.client:
            return await self.client.health_check()
        return False

    def get_client(self) -> DatabaseClient:
        """Get the database client."""
        if self.client is None:
            raise ConnectionError("Database not initialized")
        return self.client


# Global database instance
_database_manager: Optional[DatabaseManager] = None


def get_database(config: Optional[DatabaseConfig] = None) -> DatabaseManager:
    """
    Get or create the global database manager instance.

    Args:
        config: Database configuration. If None, uses default config.

    Returns:
        DatabaseManager: The global database manager instance.
    """
    global _database_manager

    if _database_manager is None:
        if config is None:
            config = DatabaseConfig()
        _database_manager = DatabaseManager(config)

    return _database_manager


async def initialize_database(config: Optional[DatabaseConfig] = None) -> DatabaseClient:
    """
    Initialize the database and return the client.

    Args:
        config: Database configuration. If None, uses default config.

    Returns:
        DatabaseClient: The database client.
    """
    manager = get_database(config)
    return await manager.initialize()


async def close_database() -> None:
    """Close the global database connection."""
    global _database_manager
    if _database_manager:
        await _database_manager.close()
        _database_manager = None
