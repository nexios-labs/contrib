"""
PostgreSQL contrib module for Nexios.

This module provides async PostgreSQL database connectivity and utilities
for Nexios applications using asyncpg.
"""
from __future__ import annotations

from .client import (
    DatabaseError,
    ConnectionError,
    QueryError,
    DatabaseConfig,
    DatabaseClient,
    DatabaseManager,
    get_database,
    initialize_database,
    close_database,
)
from .session import (
    DatabaseSession,
    TransactionContext,
    SessionManager,
    get_db_session,
    get_transaction,
    execute_in_transaction,
    execute_batch,
    insert_batch,
)
from .models import (
    DatabaseModel,
    FieldDefinition,
    FieldType,
    PrimaryKey,
    UUIDPrimaryKey,
    StringField,
    TextField,
    IntegerField,
    BooleanField,
    DecimalField,
    DateTimeField,
    DateField,
    JSONField,
    UUIDField,
)
from .utils import (
    QueryBuilder,
    DataMapper,
    DatabaseUtils,
    MigrationManager,
)

__all__ = [
    # Client
    "DatabaseError",
    "ConnectionError",
    "QueryError",
    "DatabaseConfig",
    "DatabaseClient",
    "DatabaseManager",
    "get_database",
    "initialize_database",
    "close_database",
    # Session
    "DatabaseSession",
    "TransactionContext",
    "SessionManager",
    "get_db_session",
    "get_transaction",
    "execute_in_transaction",
    "execute_batch",
    "insert_batch",
    # Models
    "DatabaseModel",
    "FieldDefinition",
    "FieldType",
    "PrimaryKey",
    "UUIDPrimaryKey",
    "StringField",
    "TextField",
    "IntegerField",
    "BooleanField",
    "DecimalField",
    "DateTimeField",
    "DateField",
    "JSONField",
    "UUIDField",
    # Utils
    "QueryBuilder",
    "DataMapper",
    "DatabaseUtils",
    "MigrationManager",
]
