"""
Database models and utilities for Nexios PostgreSQL.

This module provides base model classes, field definitions, and model utilities
for working with PostgreSQL databases in Nexios applications.
"""
from __future__ import annotations

import uuid
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union, Type, TypeVar, get_origin, get_args
from enum import Enum

try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False

from pydantic import BaseModel, Field, validator
from .client import DatabaseError, QueryError
from .session import DatabaseSession

T = TypeVar('T', bound='DatabaseModel')

class FieldType(str, Enum):
    """Database field types."""
    INTEGER = "INTEGER"
    BIGINT = "BIGINT"
    SMALLINT = "SMALLINT"
    VARCHAR = "VARCHAR"
    TEXT = "TEXT"
    BOOLEAN = "BOOLEAN"
    DECIMAL = "DECIMAL"
    NUMERIC = "NUMERIC"
    TIMESTAMP = "TIMESTAMP"
    TIMESTAMPTZ = "TIMESTAMPTZ"
    DATE = "DATE"
    TIME = "TIME"
    UUID = "UUID"
    JSON = "JSON"
    JSONB = "JSONB"
    ARRAY = "ARRAY"
    SERIAL = "SERIAL"
    BIGSERIAL = "BIGSERIAL"


class FieldDefinition:
    """Database field definition."""

    def __init__(
        self,
        field_type: FieldType,
        nullable: bool = False,
        default: Any = None,
        primary_key: bool = False,
        unique: bool = False,
        index: bool = False,
        size: Optional[int] = None,
        precision: Optional[int] = None,
        scale: Optional[int] = None,
        **kwargs
    ):
        """Initialize field definition."""
        self.field_type = field_type
        self.nullable = nullable
        self.default = default
        self.primary_key = primary_key
        self.unique = unique
        self.index = index
        self.size = size
        self.precision = precision
        self.scale = scale
        self.kwargs = kwargs

    def to_sql(self, field_name: str) -> str:
        """Convert field definition to SQL."""
        sql_parts = [field_name, self.field_type.value]

        if self.size:
            sql_parts.append(f"({self.size})")
        elif self.precision and self.scale:
            sql_parts.append(f"({self.precision},{self.scale})")
        elif self.field_type == FieldType.DECIMAL and not self.precision:
            sql_parts.append("(10,2)")

        if not self.nullable:
            sql_parts.append("NOT NULL")

        if self.primary_key:
            sql_parts.append("PRIMARY KEY")

        if self.unique:
            sql_parts.append("UNIQUE")

        return " ".join(sql_parts)

    def get_python_type(self) -> Type:
        """Get the corresponding Python type."""
        type_mapping = {
            FieldType.INTEGER: int,
            FieldType.BIGINT: int,
            FieldType.SMALLINT: int,
            FieldType.VARCHAR: str,
            FieldType.TEXT: str,
            FieldType.BOOLEAN: bool,
            FieldType.DECIMAL: Decimal,
            FieldType.NUMERIC: Decimal,
            FieldType.TIMESTAMP: datetime,
            FieldType.TIMESTAMPTZ: datetime,
            FieldType.DATE: date,
            FieldType.TIME: time,
            FieldType.UUID: uuid.UUID,
            FieldType.JSON: dict,
            FieldType.JSONB: dict,
            FieldType.ARRAY: list,
        }
        return type_mapping.get(self.field_type, str)


class DatabaseModel(BaseModel):
    """
    Base model class for database entities.

    Provides CRUD operations, serialization, and database utilities.
    """

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True

    @classmethod
    def get_table_name(cls) -> str:
        """Get the database table name for this model."""
        return cls.__name__.lower()

    @classmethod
    def get_fields(cls) -> Dict[str, FieldDefinition]:
        """Get field definitions for this model."""
        fields = {}

        for field_name, field_info in cls.__fields__.items():
            # Get field type from type annotation
            field_type = cls._get_field_type(field_info.type_)

            # Check for field constraints
            field_def = field_info.field_info.extra.get('field_def')
            if not field_def:
                # Create default field definition
                field_def = FieldDefinition(field_type)

            fields[field_name] = field_def

        return fields

    @classmethod
    def _get_field_type(cls, type_hint: Any) -> FieldType:
        """Convert Python type hint to FieldType."""
        if get_origin(type_hint) is Union:
            # Handle Optional types
            args = get_args(type_hint)
            if len(args) == 2 and type(None) in args:
                type_hint = next(arg for arg in args if arg is not type(None))

        type_mapping = {
            int: FieldType.INTEGER,
            str: FieldType.TEXT,
            bool: FieldType.BOOLEAN,
            float: FieldType.DECIMAL,
            Decimal: FieldType.DECIMAL,
            datetime: FieldType.TIMESTAMPTZ,
            date: FieldType.DATE,
            time: FieldType.TIME,
            uuid.UUID: FieldType.UUID,
            dict: FieldType.JSONB,
            list: FieldType.ARRAY,
        }

        return type_mapping.get(type_hint, FieldType.TEXT)

    @classmethod
    def create_table_sql(cls) -> str:
        """Generate CREATE TABLE SQL for this model."""
        fields = cls.get_fields()
        field_sqls = []

        for field_name, field_def in fields.items():
            field_sqls.append(field_def.to_sql(field_name))

        return f"CREATE TABLE IF NOT EXISTS {cls.get_table_name()} ({', '.join(field_sqls)});"

    @classmethod
    def drop_table_sql(cls) -> str:
        """Generate DROP TABLE SQL for this model."""
        return f"DROP TABLE IF EXISTS {cls.get_table_name()};"

    @classmethod
    async def create_table(cls, session: DatabaseSession) -> None:
        """Create the table for this model."""
        sql = cls.create_table_sql()
        await session.execute(sql)

    @classmethod
    async def drop_table(cls, session: DatabaseSession) -> None:
        """Drop the table for this model."""
        sql = cls.drop_table_sql()
        await session.execute(sql)

    def to_dict(self, exclude_none: bool = True, exclude_unset: bool = False) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return self.dict(exclude_none=exclude_none, exclude_unset=exclude_unset)

    def to_json(self, **kwargs) -> str:
        """Convert model to JSON string."""
        return self.json(**kwargs)

    async def save(self, session: DatabaseSession) -> DatabaseModel:
        """Save this model to the database (insert or update)."""
        fields = self.get_fields()
        field_names = list(fields.keys())

        # Check if primary key exists (for update vs insert)
        primary_keys = [name for name, field in fields.items() if field.primary_key]

        if primary_keys and all(getattr(self, pk, None) for pk in primary_keys):
            # Update
            return await self.update(session)
        else:
            # Insert
            return await self.insert(session)

    async def insert(self, session: DatabaseSession) -> DatabaseModel:
        """Insert this model into the database."""
        fields = self.get_fields()
        field_names = [name for name in fields.keys() if hasattr(self, name)]
        placeholders = ", ".join([f"${i+1}" for i in range(len(field_names))])

        columns = ", ".join(field_names)
        values = [getattr(self, name) for name in field_names]

        query = f"""
            INSERT INTO {self.get_table_name()} ({columns})
            VALUES ({placeholders})
        """

        # Add RETURNING clause for primary keys
        returning_fields = [name for name, field in fields.items() if field.primary_key]
        if returning_fields:
            query += f" RETURNING {', '.join(returning_fields)}"

        if returning_fields:
            result = await session.fetchrow(query, *values)
            if result:
                for field_name, value in result.items():
                    setattr(self, field_name, value)

        return self

    async def update(self, session: DatabaseSession) -> DatabaseModel:
        """Update this model in the database."""
        fields = self.get_fields()
        field_names = [name for name in fields.keys() if hasattr(self, name)]
        primary_keys = [name for name, field in fields.items() if field.primary_key]

        # Separate primary key fields from update fields
        update_fields = [name for name in field_names if name not in primary_keys]
        if not update_fields:
            return self

        set_clause = ", ".join([f"{name} = ${i+1}" for i, name in enumerate(update_fields)])
        param_index = len(update_fields)

        where_clause = " AND ".join([f"{name} = ${param_index + i + 1}" for i, name in enumerate(primary_keys)])
        param_index += len(primary_keys)

        values = [getattr(self, name) for name in update_fields]
        values.extend([getattr(self, name) for name in primary_keys])

        query = f"""
            UPDATE {self.get_table_name()}
            SET {set_clause}
            WHERE {where_clause}
        """

        await session.execute(query, *values)
        return self

    async def delete(self, session: DatabaseSession) -> bool:
        """Delete this model from the database."""
        fields = self.get_fields()
        primary_keys = [name for name, field in fields.items() if field.primary_key]

        if not primary_keys:
            raise QueryError("Cannot delete: no primary key defined")

        where_clause = " AND ".join([f"{name} = ${i+1}" for i, name in enumerate(primary_keys)])
        values = [getattr(self, name) for name in primary_keys]

        query = f"DELETE FROM {self.get_table_name()} WHERE {where_clause}"

        result = await session.execute(query, *values)
        return "DELETE" in result

    @classmethod
    async def get_by_id(cls: Type[T], session: DatabaseSession, id_value: Any) -> Optional[T]:
        """Get a model instance by primary key."""
        fields = cls.get_fields()
        primary_keys = [name for name, field in fields.items() if field.primary_key]

        if not primary_keys:
            raise QueryError("No primary key defined")

        if len(primary_keys) != 1:
            raise QueryError("get_by_id only supports single primary key")

        pk_field = primary_keys[0]
        query = f"SELECT * FROM {cls.get_table_name()} WHERE {pk_field} = $1"

        result = await session.fetchrow(query, id_value)
        if result:
            return cls(**result)
        return None

    @classmethod
    async def get_all(cls: Type[T], session: DatabaseSession) -> List[T]:
        """Get all model instances."""
        query = f"SELECT * FROM {cls.get_table_name()}"
        results = await session.fetch(query)
        return [cls(**result) for result in results]

    @classmethod
    async def count(cls, session: DatabaseSession, where_clause: str = "", *args) -> int:
        """Count records matching criteria."""
        query = f"SELECT COUNT(*) FROM {cls.get_table_name()}"
        if where_clause:
            query += f" WHERE {where_clause}"

        return await session.fetchval(query, *args)

    @classmethod
    async def exists(cls, session: DatabaseSession, where_clause: str = "", *args) -> bool:
        """Check if records matching criteria exist."""
        query = f"SELECT EXISTS(SELECT 1 FROM {cls.get_table_name()}"
        if where_clause:
            query += f" WHERE {where_clause}"
        query += ")"

        return await session.fetchval(query, *args)

    def __str__(self) -> str:
        """String representation of the model."""
        return f"{self.__class__.__name__}({self.to_dict()})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return self.__str__()


# Common field definitions for convenience

def PrimaryKey() -> FieldDefinition:
    """Create a primary key field definition."""
    return FieldDefinition(
        FieldType.INTEGER,
        primary_key=True,
        nullable=False
    )

def UUIDPrimaryKey() -> FieldDefinition:
    """Create a UUID primary key field definition."""
    return FieldDefinition(
        FieldType.UUID,
        primary_key=True,
        nullable=False,
        default="uuid_generate_v4()"
    )

def StringField(size: Optional[int] = None, nullable: bool = False) -> FieldDefinition:
    """Create a string field definition."""
    return FieldDefinition(
        FieldType.VARCHAR if size else FieldType.TEXT,
        size=size,
        nullable=nullable
    )

def TextField(nullable: bool = False) -> FieldDefinition:
    """Create a text field definition."""
    return FieldDefinition(
        FieldType.TEXT,
        nullable=nullable
    )

def IntegerField(nullable: bool = False) -> FieldDefinition:
    """Create an integer field definition."""
    return FieldDefinition(
        FieldType.INTEGER,
        nullable=nullable
    )

def BooleanField(nullable: bool = False) -> FieldDefinition:
    """Create a boolean field definition."""
    return FieldDefinition(
        FieldType.BOOLEAN,
        nullable=nullable
    )

def DecimalField(precision: int = 10, scale: int = 2, nullable: bool = False) -> FieldDefinition:
    """Create a decimal field definition."""
    return FieldDefinition(
        FieldType.DECIMAL,
        precision=precision,
        scale=scale,
        nullable=nullable
    )

def DateTimeField(nullable: bool = False) -> FieldDefinition:
    """Create a datetime field definition."""
    return FieldDefinition(
        FieldType.TIMESTAMPTZ,
        nullable=nullable
    )

def DateField(nullable: bool = False) -> FieldDefinition:
    """Create a date field definition."""
    return FieldDefinition(
        FieldType.DATE,
        nullable=nullable
    )

def JSONField(nullable: bool = False) -> FieldDefinition:
    """Create a JSON field definition."""
    return FieldDefinition(
        FieldType.JSONB,
        nullable=nullable
    )

def UUIDField(nullable: bool = False) -> FieldDefinition:
    """Create a UUID field definition."""
    return FieldDefinition(
        FieldType.UUID,
        nullable=nullable,
        default="uuid_generate_v4()"
    )
