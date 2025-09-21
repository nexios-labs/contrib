"""
Database session and transaction management for Nexios PostgreSQL.

This module provides database sessions, transactions, and session-based operations
for Nexios applications using asyncpg.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Union, TypeVar, Generic, Callable, Awaitable

try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False

from .client import DatabaseClient, DatabaseError, ConnectionError, QueryError

T = TypeVar('T')

logger = logging.getLogger(__name__)


class DatabaseSession:
    """
    Database session for managing transactions and queries.

    Provides transaction management, query execution, and session lifecycle.
    """

    def __init__(self, client: DatabaseClient):
        """Initialize database session."""
        self.client = client
        self._connection: Optional[asyncpg.Connection] = None
        self._transaction: Optional[asyncpg.Transaction] = None
        self._in_transaction = False

    async def __aenter__(self) -> DatabaseSession:
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

    async def start(self) -> None:
        """Start the session by acquiring a connection."""
        if self._connection is not None:
            return

        self._connection = await self.client.acquire()
        logger.debug("Database session started")

    async def close(self) -> None:
        """Close the session and release the connection."""
        if self._transaction:
            if self._in_transaction:
                try:
                    await self._transaction.rollback()
                except Exception:
                    pass
            self._transaction = None

        if self._connection:
            await self.client._pool.release(self._connection)  # type: ignore
            self._connection = None

        logger.debug("Database session closed")

    async def execute(self, query: str, *args, timeout: Optional[float] = None) -> str:
        """Execute a query within the session."""
        if self._connection is None:
            await self.start()

        try:
            return await self._connection.execute(query, *args, timeout=timeout)  # type: ignore
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise QueryError(f"Query execution failed: {e}")

    async def fetch(self, query: str, *args, timeout: Optional[float] = None) -> List[asyncpg.Record]:
        """Execute a query and return all rows."""
        if self._connection is None:
            await self.start()

        try:
            return await self._connection.fetch(query, *args, timeout=timeout)  # type: ignore
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise QueryError(f"Query execution failed: {e}")

    async def fetchrow(self, query: str, *args, timeout: Optional[float] = None) -> Optional[asyncpg.Record]:
        """Execute a query and return the first row."""
        if self._connection is None:
            await self.start()

        try:
            return await self._connection.fetchrow(query, *args, timeout=timeout)  # type: ignore
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise QueryError(f"Query execution failed: {e}")

    async def fetchval(self, query: str, *args, column: int = 0, timeout: Optional[float] = None) -> Any:
        """Execute a query and return the first column of the first row."""
        if self._connection is None:
            await self.start()

        try:
            return await self._connection.fetchval(query, *args, column=column, timeout=timeout)  # type: ignore
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise QueryError(f"Query execution failed: {e}")

    async def executemany(self, query: str, args_list: List[tuple], timeout: Optional[float] = None) -> None:
        """Execute a query multiple times with different parameters."""
        if self._connection is None:
            await self.start()

        try:
            await self._connection.executemany(query, args_list, timeout=timeout)  # type: ignore
        except Exception as e:
            logger.error(f"Batch query execution failed: {e}")
            raise QueryError(f"Batch query execution failed: {e}")

    @asynccontextmanager
    async def transaction(self):
        """Context manager for database transactions."""
        if self._connection is None:
            await self.start()

        transaction = self._connection.transaction()  # type: ignore
        self._transaction = transaction
        self._in_transaction = False

        try:
            await transaction.start()
            self._in_transaction = True
            logger.debug("Transaction started")
            yield self
        except Exception as e:
            if self._in_transaction:
                await transaction.rollback()
                logger.debug("Transaction rolled back due to exception")
            raise
        else:
            await transaction.commit()
            logger.debug("Transaction committed")
        finally:
            self._transaction = None
            self._in_transaction = False

    async def commit(self) -> None:
        """Commit the current transaction."""
        if self._transaction and self._in_transaction:
            await self._transaction.commit()
            self._in_transaction = False
            logger.debug("Transaction committed")

    async def rollback(self) -> None:
        """Rollback the current transaction."""
        if self._transaction and self._in_transaction:
            await self._transaction.rollback()
            self._in_transaction = False
            logger.debug("Transaction rolled back")

    def is_in_transaction(self) -> bool:
        """Check if currently in a transaction."""
        return self._in_transaction


class TransactionContext:
    """
    Context manager for database transactions.

    Provides a convenient way to handle transactions with automatic rollback
    on exceptions and commit on success.
    """

    def __init__(self, session: DatabaseSession):
        """Initialize transaction context."""
        self.session = session
        self._transaction_active = False

    async def __aenter__(self) -> DatabaseSession:
        """Enter transaction context."""
        self.session = await self.session.transaction().__aenter__()
        self._transaction_active = True
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit transaction context."""
        await self.session.transaction().__aexit__(exc_type, exc_val, exc_tb)


class SessionManager:
    """
    Session manager for handling database sessions in Nexios applications.

    Provides session-per-request pattern and session lifecycle management.
    """

    def __init__(self, client: DatabaseClient):
        """Initialize session manager."""
        self.client = client
        self._sessions: Dict[str, DatabaseSession] = {}

    async def get_session(self, session_id: Optional[str] = None) -> DatabaseSession:
        """
        Get or create a database session.

        Args:
            session_id: Optional session identifier.

        Returns:
            DatabaseSession: The database session.
        """
        if session_id is None:
            session_id = "default"

        if session_id not in self._sessions:
            self._sessions[session_id] = DatabaseSession(self.client)

        return self._sessions[session_id]

    async def close_session(self, session_id: Optional[str] = None) -> None:
        """
        Close and remove a session.

        Args:
            session_id: Session identifier. If None, closes all sessions.
        """
        if session_id is None:
            for session in self._sessions.values():
                await session.close()
            self._sessions.clear()
        else:
            if session_id in self._sessions:
                await self._sessions[session_id].close()
                del self._sessions[session_id]

    async def close_all(self) -> None:
        """Close all sessions."""
        await self.close_session(None)

    def get_session_count(self) -> int:
        """Get the number of active sessions."""
        return len(self._sessions)

    def list_sessions(self) -> List[str]:
        """List all active session IDs."""
        return list(self._sessions.keys())


# Utility functions for session management

@asynccontextmanager
async def get_db_session(client: DatabaseClient, session_id: Optional[str] = None):
    """
    Context manager for database sessions.

    Args:
        client: Database client instance.
        session_id: Optional session identifier.

    Yields:
        DatabaseSession: The database session.
    """
    session = DatabaseSession(client)
    try:
        async with session:
            yield session
    finally:
        await session.close()


@asynccontextmanager
async def get_transaction(session: DatabaseSession):
    """
    Context manager for database transactions.

    Args:
        session: Database session instance.

    Yields:
        DatabaseSession: The session in transaction mode.
    """
    async with session.transaction():
        yield session


async def execute_in_transaction(
    client: DatabaseClient,
    operation: Callable[[DatabaseSession], Awaitable[T]],
    session_id: Optional[str] = None
) -> T:
    """
    Execute an operation within a transaction.

    Args:
        client: Database client instance.
        operation: Async function that takes a session and returns a value.
        session_id: Optional session identifier.

    Returns:
        T: The result of the operation.
    """
    session_manager = SessionManager(client)
    session = await session_manager.get_session(session_id)

    async with session.transaction():
        return await operation(session)


# Batch operations

async def execute_batch(
    session: DatabaseSession,
    queries: List[str],
    args_list: Optional[List[List[Any]]] = None
) -> List[Any]:
    """
    Execute multiple queries in a batch.

    Args:
        session: Database session.
        queries: List of SQL queries.
        args_list: Optional list of argument lists for each query.

    Returns:
        List[Any]: Results from each query.
    """
    results = []

    for i, query in enumerate(queries):
        args = args_list[i] if args_list and i < len(args_list) else []
        try:
            result = await session.execute(query, *args)
            results.append(result)
        except Exception as e:
            logger.error(f"Batch query {i} failed: {e}")
            raise QueryError(f"Batch query {i} failed: {e}")

    return results


async def insert_batch(
    session: DatabaseSession,
    table: str,
    records: List[Dict[str, Any]],
    returning: Optional[str] = None
) -> List[asyncpg.Record]:
    """
    Insert multiple records in a batch.

    Args:
        session: Database session.
        table: Table name.
        records: List of record dictionaries.
        returning: Optional column to return.

    Returns:
        List[asyncpg.Record]: Inserted records if returning specified.
    """
    if not records:
        return []

    # Get column names from first record
    columns = list(records[0].keys())
    values_template = ", ".join([f"${i+1}" for i in range(len(columns))])

    query = f"""
        INSERT INTO {table} ({', '.join(columns)})
        VALUES ({values_template})
    """

    if returning:
        query += f" RETURNING {returning}"

    # Prepare arguments
    args_list = []
    for record in records:
        args = [record[col] for col in columns]
        args_list.append(tuple(args))

    if returning:
        return await session.fetch(query, *args_list)
    else:
        await session.executemany(query, args_list)
        return []
