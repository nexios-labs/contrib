"""
Database utilities for Nexios PostgreSQL.

This module provides query builders, data manipulation utilities, and
database management helpers for Nexios applications.
"""
from __future__ import annotations

import json
from datetime import datetime, date, time
from typing import Any, Dict, List, Optional, Union, Tuple, Type, get_type_hints
from enum import Enum

try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False

from .client import DatabaseError, QueryError
from .session import DatabaseSession
from .models import DatabaseModel, FieldDefinition, FieldType


class QueryBuilder:
    """
    SQL query builder for PostgreSQL.

    Provides a fluent interface for building SQL queries with parameter binding.
    """

    def __init__(self, table: str):
        """Initialize query builder."""
        self.table = table
        self._select_fields: List[str] = []
        self._where_conditions: List[str] = []
        self._order_by_fields: List[str] = []
        self._group_by_fields: List[str] = []
        self._having_conditions: List[str] = []
        self._join_clauses: List[str] = []
        self._limit_value: Optional[int] = None
        self._offset_value: Optional[int] = None
        self._params: List[Any] = []
        self._param_counter = 1

    def select(self, *fields: str) -> QueryBuilder:
        """Add SELECT fields."""
        if not fields:
            self._select_fields.append("*")
        else:
            self._select_fields.extend(fields)
        return self

    def where(self, condition: str, *args: Any) -> QueryBuilder:
        """Add WHERE condition."""
        self._where_conditions.append(condition)
        self._params.extend(args)
        return self

    def where_eq(self, field: str, value: Any) -> QueryBuilder:
        """Add WHERE field = value condition."""
        return self.where(f"{field} = ${self._param_counter}", value)

    def where_neq(self, field: str, value: Any) -> QueryBuilder:
        """Add WHERE field != value condition."""
        return self.where(f"{field} != ${self._param_counter}", value)

    def where_gt(self, field: str, value: Any) -> QueryBuilder:
        """Add WHERE field > value condition."""
        return self.where(f"{field} > ${self._param_counter}", value)

    def where_gte(self, field: str, value: Any) -> QueryBuilder:
        """Add WHERE field >= value condition."""
        return self.where(f"{field} >= ${self._param_counter}", value)

    def where_lt(self, field: str, value: Any) -> QueryBuilder:
        """Add WHERE field < value condition."""
        return self.where(f"{field} < ${self._param_counter}", value)

    def where_lte(self, field: str, value: Any) -> QueryBuilder:
        """Add WHERE field <= value condition."""
        return self.where(f"{field} <= ${self._param_counter}", value)

    def where_like(self, field: str, pattern: str) -> QueryBuilder:
        """Add WHERE field LIKE pattern condition."""
        return self.where(f"{field} LIKE ${self._param_counter}", pattern)

    def where_ilike(self, field: str, pattern: str) -> QueryBuilder:
        """Add WHERE field ILIKE pattern condition (case-insensitive)."""
        return self.where(f"{field} ILIKE ${self._param_counter}", pattern)

    def where_in(self, field: str, values: List[Any]) -> QueryBuilder:
        """Add WHERE field IN (values) condition."""
        placeholders = ", ".join([f"${self._param_counter + i}" for i in range(len(values))])
        return self.where(f"{field} IN ({placeholders})", *values)

    def where_is_null(self, field: str) -> QueryBuilder:
        """Add WHERE field IS NULL condition."""
        return self.where(f"{field} IS NULL")

    def where_is_not_null(self, field: str) -> QueryBuilder:
        """Add WHERE field IS NOT NULL condition."""
        return self.where(f"{field} IS NOT NULL")

    def order_by(self, field: str, direction: str = "ASC") -> QueryBuilder:
        """Add ORDER BY clause."""
        self._order_by_fields.append(f"{field} {direction.upper()}")
        return self

    def group_by(self, *fields: str) -> QueryBuilder:
        """Add GROUP BY clause."""
        self._group_by_fields.extend(fields)
        return self

    def having(self, condition: str, *args: Any) -> QueryBuilder:
        """Add HAVING condition."""
        self._having_conditions.append(condition)
        self._params.extend(args)
        return self

    def join(self, table: str, condition: str, join_type: str = "INNER") -> QueryBuilder:
        """Add JOIN clause."""
        self._join_clauses.append(f"{join_type} JOIN {table} ON {condition}")
        return self

    def left_join(self, table: str, condition: str) -> QueryBuilder:
        """Add LEFT JOIN clause."""
        return self.join(table, condition, "LEFT")

    def right_join(self, table: str, condition: str) -> QueryBuilder:
        """Add RIGHT JOIN clause."""
        return self.join(table, condition, "RIGHT")

    def limit(self, limit: int) -> QueryBuilder:
        """Add LIMIT clause."""
        self._limit_value = limit
        return self

    def offset(self, offset: int) -> QueryBuilder:
        """Add OFFSET clause."""
        self._offset_value = offset
        return self

    def build(self) -> Tuple[str, List[Any]]:
        """Build the SQL query and parameter list."""
        if not self._select_fields:
            self._select_fields.append("*")

        query_parts = [
            f"SELECT {', '.join(self._select_fields)}",
            f"FROM {self.table}"
        ]

        if self._join_clauses:
            query_parts.extend(self._join_clauses)

        if self._where_conditions:
            query_parts.append(f"WHERE {' AND '.join(self._where_conditions)}")

        if self._group_by_fields:
            query_parts.append(f"GROUP BY {', '.join(self._group_by_fields)}")

        if self._having_conditions:
            query_parts.append(f"HAVING {' AND '.join(self._having_conditions)}")

        if self._order_by_fields:
            query_parts.append(f"ORDER BY {', '.join(self._order_by_fields)}")

        if self._limit_value is not None:
            query_parts.append(f"LIMIT {self._limit_value}")

        if self._offset_value is not None:
            query_parts.append(f"OFFSET {self._offset_value}")

        return " ".join(query_parts), self._params

    def build_insert(self, data: Dict[str, Any], returning: Optional[List[str]] = None) -> Tuple[str, List[Any]]:
        """Build INSERT query."""
        if not data:
            raise QueryError("No data provided for INSERT")

        columns = list(data.keys())
        placeholders = ", ".join([f"${i+1}" for i in range(len(columns))])
        values = [data[col] for col in columns]

        query = f"INSERT INTO {self.table} ({', '.join(columns)}) VALUES ({placeholders})"

        if returning:
            query += f" RETURNING {', '.join(returning)}"

        return query, values

    def build_update(self, data: Dict[str, Any], where_conditions: List[str], returning: Optional[List[str]] = None) -> Tuple[str, List[Any]]:
        """Build UPDATE query."""
        if not data:
            raise QueryError("No data provided for UPDATE")

        set_clause = ", ".join([f"{col} = ${i+1}" for i, col in enumerate(data.keys())])
        values = list(data.values())

        query = f"UPDATE {self.table} SET {set_clause}"

        if where_conditions:
            query += f" WHERE {' AND '.join(where_conditions)}"

        if returning:
            query += f" RETURNING {', '.join(returning)}"

        return query, values


class DataMapper:
    """
    Utility for mapping between database records and Python objects.

    Handles type conversion and data transformation between PostgreSQL and Python types.
    """

    @staticmethod
    def record_to_dict(record: asyncpg.Record) -> Dict[str, Any]:
        """Convert asyncpg Record to dictionary."""
        if not record:
            return {}

        result = {}
        for key in record.keys():
            value = record[key]
            result[key] = DataMapper._convert_value(value)
        return result

    @staticmethod
    def records_to_dicts(records: List[asyncpg.Record]) -> List[Dict[str, Any]]:
        """Convert list of asyncpg Records to list of dictionaries."""
        return [DataMapper.record_to_dict(record) for record in records]

    @staticmethod
    def _convert_value(value: Any) -> Any:
        """Convert database value to Python value."""
        if isinstance(value, (datetime, date, time)):
            return value.isoformat()
        elif isinstance(value, (list, tuple)):
            return [DataMapper._convert_value(item) for item in value]
        elif isinstance(value, dict):
            return {k: DataMapper._convert_value(v) for k, v in value.items()}
        elif hasattr(value, 'isoformat'):  # JSON serializable
            return value.isoformat()
        else:
            return value

    @staticmethod
    def dict_to_record(data: Dict[str, Any], field_types: Dict[str, FieldType]) -> Dict[str, Any]:
        """Convert dictionary to database record format."""
        result = {}
        for key, value in data.items():
            field_type = field_types.get(key)
            if field_type:
                result[key] = DataMapper._convert_to_db_type(value, field_type)
            else:
                result[key] = value
        return result

    @staticmethod
    def _convert_to_db_type(value: Any, field_type: FieldType) -> Any:
        """Convert Python value to database type."""
        if value is None:
            return None

        type_converters = {
            FieldType.INTEGER: lambda x: int(x),
            FieldType.BIGINT: lambda x: int(x),
            FieldType.SMALLINT: lambda x: int(x),
            FieldType.VARCHAR: lambda x: str(x),
            FieldType.TEXT: lambda x: str(x),
            FieldType.BOOLEAN: lambda x: bool(x),
            FieldType.DECIMAL: lambda x: float(x) if not isinstance(x, (int, float)) else x,
            FieldType.NUMERIC: lambda x: float(x) if not isinstance(x, (int, float)) else x,
            FieldType.TIMESTAMP: lambda x: x if isinstance(x, datetime) else datetime.fromisoformat(x),
            FieldType.TIMESTAMPTZ: lambda x: x if isinstance(x, datetime) else datetime.fromisoformat(x),
            FieldType.DATE: lambda x: x if isinstance(x, date) else date.fromisoformat(x),
            FieldType.TIME: lambda x: x if isinstance(x, time) else time.fromisoformat(x),
            FieldType.UUID: lambda x: x if isinstance(x, str) else str(x),
            FieldType.JSON: lambda x: x if isinstance(x, (dict, list)) else json.loads(x),
            FieldType.JSONB: lambda x: x if isinstance(x, (dict, list)) else json.loads(x),
            FieldType.ARRAY: lambda x: x if isinstance(x, list) else [x],
        }

        converter = type_converters.get(field_type)
        return converter(value) if converter else value


class DatabaseUtils:
    """
    Database utility functions for common operations.
    """

    @staticmethod
    async def table_exists(session: DatabaseSession, table_name: str) -> bool:
        """Check if a table exists."""
        query = """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = $1
            )
        """
        return await session.fetchval(query, table_name)

    @staticmethod
    async def get_table_info(session: DatabaseSession, table_name: str) -> List[Dict[str, Any]]:
        """Get information about a table's columns."""
        query = """
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = $1
            ORDER BY ordinal_position
        """
        records = await session.fetch(query, table_name)
        return DataMapper.records_to_dicts(records)

    @staticmethod
    async def get_table_indexes(session: DatabaseSession, table_name: str) -> List[Dict[str, Any]]:
        """Get information about a table's indexes."""
        query = """
            SELECT
                indexname,
                indexdef
            FROM pg_indexes
            WHERE tablename = $1
        """
        records = await session.fetch(query, table_name)
        return DataMapper.records_to_dicts(records)

    @staticmethod
    async def get_database_size(session: DatabaseSession, database_name: Optional[str] = None) -> Dict[str, Any]:
        """Get database size information."""
        if database_name is None:
            database_name = await session.fetchval("SELECT current_database()")

        query = """
            SELECT
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        """

        records = await session.fetch(query)
        return {
            "database": database_name,
            "tables": DataMapper.records_to_dicts(records)
        }

    @staticmethod
    async def vacuum_table(session: DatabaseSession, table_name: str, analyze: bool = True) -> None:
        """Run VACUUM on a table."""
        if analyze:
            query = f"VACUUM ANALYZE {table_name}"
        else:
            query = f"VACUUM {table_name}"
        await session.execute(query)

    @staticmethod
    async def reindex_table(session: DatabaseSession, table_name: str) -> None:
        """Rebuild indexes for a table."""
        query = f"REINDEX TABLE {table_name}"
        await session.execute(query)

    @staticmethod
    async def get_connection_count(session: DatabaseSession) -> int:
        """Get the number of active connections."""
        query = "SELECT count(*) FROM pg_stat_activity"
        return await session.fetchval(query)

    @staticmethod
    async def get_active_queries(session: DatabaseSession) -> List[Dict[str, Any]]:
        """Get information about active queries."""
        query = """
            SELECT
                pid,
                now() - pg_stat_activity.query_start AS duration,
                query,
                state,
                client_addr
            FROM pg_stat_activity
            WHERE (now() - pg_stat_activity.query_start) > interval '5 seconds'
            ORDER BY duration DESC
        """
        records = await session.fetch(query)
        return DataMapper.records_to_dicts(records)

    @staticmethod
    async def kill_connection(session: DatabaseSession, pid: int) -> None:
        """Kill a database connection."""
        query = "SELECT pg_terminate_backend($1)"
        await session.execute(query, pid)

    @staticmethod
    async def get_table_statistics(session: DatabaseSession, table_name: str) -> Dict[str, Any]:
        """Get table statistics."""
        query = """
            SELECT
                schemaname,
                tablename,
                n_tup_ins,
                n_tup_upd,
                n_tup_del,
                n_live_tup,
                n_dead_tup,
                last_autoanalyze,
                last_autovacuum
            FROM pg_stat_user_tables
            WHERE tablename = $1
        """
        record = await session.fetchrow(query, table_name)
        return DataMapper.record_to_dict(record) if record else {}


class MigrationManager:
    """
    Database migration manager.

    Provides utilities for managing database schema migrations.
    """

    def __init__(self, session: DatabaseSession, migrations_table: str = "schema_migrations"):
        """Initialize migration manager."""
        self.session = session
        self.migrations_table = migrations_table

    async def initialize(self) -> None:
        """Initialize migration system."""
        query = f"""
            CREATE TABLE IF NOT EXISTS {self.migrations_table} (
                version VARCHAR(50) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """
        await self.session.execute(query)

    async def get_applied_migrations(self) -> List[str]:
        """Get list of applied migrations."""
        query = f"SELECT version FROM {self.migrations_table} ORDER BY version"
        records = await self.session.fetch(query)
        return [record['version'] for record in records]

    async def apply_migration(self, version: str, name: str, sql: str) -> None:
        """Apply a migration."""
        async with self.session.transaction():
            await self.session.execute(sql)
            query = f"""
                INSERT INTO {self.migrations_table} (version, name)
                VALUES ($1, $2)
            """
            await self.session.execute(query, version, name)

    async def rollback_migration(self, version: str) -> None:
        """Rollback a migration (requires manual SQL)."""
        # This would need to be implemented based on specific migration needs
        query = f"DELETE FROM {self.migrations_table} WHERE version = $1"
        await self.session.execute(query, version)

    async def get_migration_status(self) -> Dict[str, Any]:
        """Get migration status information."""
        applied = await self.get_applied_migrations()
        return {
            "applied_migrations": applied,
            "total_applied": len(applied),
            "migrations_table": self.migrations_table
        }
