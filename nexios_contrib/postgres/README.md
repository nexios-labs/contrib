<p align="center">
  <a href="https://github.com/nexios-labs">
    <img alt="Nexios Logo" height="220" src="https://nexios-docs.netlify.app/logo.png">
  </a>
</p>

<h1 align="center">PostgreSQL Client for Nexios</h1>

A comprehensive async PostgreSQL database client for the Nexios ASGI framework, built on asyncpg for high-performance database operations.

It provides:

- **Connection Pooling**: Efficient connection management with asyncpg
- **Session Management**: Database sessions with transaction support
- **ORM-like Models**: Pydantic-based model classes for database entities
- **Query Builder**: Fluent SQL query builder with parameter binding
- **Migration Support**: Database schema migration utilities
- **Type Safety**: Full type hints and validation
- **Error Handling**: Comprehensive error handling and logging

---

## Installation

```bash
pip install nexios_contrib
pip install asyncpg  # Required dependency
```

Or add to your project's `pyproject.toml`:

```toml
[dependencies]
nexios_contrib = "^1.0.0"
asyncpg = "^0.29.0"
```

---

## Quickstart

### Basic Setup

```python
from nexios import NexiosApp
from nexios_contrib.postgres import DatabaseConfig, get_database, initialize_database

app = NexiosApp()

# Configure database
db_config = DatabaseConfig(
    host="localhost",
    database="myapp",
    user="postgres",
    password="password",
    min_size=5,
    max_size=20
)

# Initialize database connection
@app.on_event("startup")
async def startup():
    db_client = await initialize_database(db_config)
    app.state.db = db_client

@app.on_event("shutdown")
async def shutdown():
    await close_database()

@app.get("/health")
async def health_check(request, response):
    db = app.state.db
    is_healthy = await db.health_check()

    return {
        "database": "healthy" if is_healthy else "unhealthy",
        "pool_info": await db.get_pool_info()
    }
```

### Using Models

```python
from nexios import NexiosApp
from nexios_contrib.postgres import DatabaseModel, IntegerField, StringField, DateTimeField
from nexios_contrib.postgres.session import get_db_session

class User(DatabaseModel):
    id: int = IntegerField(primary_key=True)
    name: str = StringField()
    email: str = StringField()
    created_at: datetime = DateTimeField()

app = NexiosApp()

@app.get("/users")
async def get_users(request, response):
    db = app.state.db

    async with get_db_session(db) as session:
        users = await User.get_all(session)
        return {"users": [user.to_dict() for user in users]}

@app.post("/users")
async def create_user(request, response):
    db = app.state.db
    user_data = request.json

    async with get_db_session(db) as session:
        user = User(**user_data)
        await user.save(session)
        return {"user": user.to_dict()}
```

---

## Configuration

### DatabaseConfig Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `host` | `str` | `"localhost"` | Database server hostname |
| `port` | `int` | `5432` | Database server port |
| `database` | `str` | `"nexios"` | Database name |
| `user` | `str` | `"postgres"` | Database username |
| `password` | `str` | `""` | Database password |
| `min_size` | `int` | `5` | Minimum connection pool size |
| `max_size` | `int` | `20` | Maximum connection pool size |
| `command_timeout` | `int` | `60` | Query timeout in seconds |
| `server_hostname` | `Optional[str]` | `None` | Server hostname for SSL |
| `server_settings` | `Optional[Dict[str, str]]` | `None` | Server configuration settings |

### Environment Variables

```python
import os
from nexios_contrib.postgres import DatabaseConfig

db_config = DatabaseConfig(
    host=os.getenv("DB_HOST", "localhost"),
    database=os.getenv("DB_NAME", "myapp"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", ""),
    min_size=int(os.getenv("DB_MIN_SIZE", "5")),
    max_size=int(os.getenv("DB_MAX_SIZE", "20"))
)
```

---

## Client Usage

### DatabaseClient

The `DatabaseClient` provides low-level database operations:

```python
from nexios_contrib.postgres import DatabaseClient, DatabaseConfig

db_config = DatabaseConfig(database="myapp")
client = DatabaseClient(db_config)
await client.initialize()

# Execute queries
result = await client.execute("SELECT * FROM users WHERE id = $1", user_id)
rows = await client.fetch("SELECT * FROM users")
row = await client.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
value = await client.fetchval("SELECT COUNT(*) FROM users")

# Health check
is_healthy = await client.health_check()
pool_info = await client.get_pool_info()

await client.close()
```

### Connection Management

```python
# Context manager for connections
async with client.connection() as conn:
    result = await conn.fetch("SELECT * FROM users")
    # Connection is automatically returned to pool
```

### Batch Operations

```python
# Execute multiple queries
queries = [
    "INSERT INTO users (name) VALUES ($1)",
    "INSERT INTO logs (message) VALUES ($1)"
]
args_list = [
    [("Alice",), ("Bob",)],
    [("User created",), ("User logged in",)]
]

async with client.connection() as conn:
    await conn.executemany(queries[0], args_list[0])
    await conn.executemany(queries[1], args_list[1])
```

---

## Session Management

### DatabaseSession

The `DatabaseSession` provides transaction support and session-based operations:

```python
from nexios_contrib.postgres.session import DatabaseSession

async with DatabaseSession(client) as session:
    # Execute queries within session
    users = await session.fetch("SELECT * FROM users")

    # Use transactions
    async with session.transaction():
        await session.execute("INSERT INTO users (name) VALUES ($1)", "Alice")
        await session.execute("INSERT INTO users (name) VALUES ($1)", "Bob")
        # Transaction auto-commits on success
```

### Session Manager

```python
from nexios_contrib.postgres.session import SessionManager

session_manager = SessionManager(client)

@app.middleware
async def db_session_middleware(request, response, call_next):
    # Create session per request
    session = await session_manager.get_session("request_1")

    try:
        request.state.db_session = session
        return await call_next()
    finally:
        await session_manager.close_session("request_1")

@app.get("/users")
async def get_users(request, response):
    session = request.state.db_session
    users = await session.fetch("SELECT * FROM users")
    return {"users": users}
```

---

## Models and ORM

### Creating Models

```python
from datetime import datetime
from typing import Optional
from nexios_contrib.postgres import DatabaseModel, IntegerField, StringField, DateTimeField

class User(DatabaseModel):
    id: int = IntegerField(primary_key=True)
    name: str = StringField(nullable=False)
    email: str = StringField(nullable=False)
    age: Optional[int] = IntegerField()
    created_at: datetime = DateTimeField()

class Post(DatabaseModel):
    id: int = IntegerField(primary_key=True)
    user_id: int = IntegerField(nullable=False)
    title: str = StringField(nullable=False)
    content: str = StringField()
    published: bool = IntegerField(default=False)
    created_at: datetime = DateTimeField()
```

### Using Models

```python
@app.post("/users")
async def create_user(request, response):
    user_data = request.json

    async with get_db_session(client) as session:
        user = User(**user_data)
        await user.insert(session)  # Insert new user
        return {"user": user.to_dict()}

@app.get("/users/{user_id}")
async def get_user(request, response, user_id: int):
    async with get_db_session(client) as session:
        user = await User.get_by_id(session, user_id)
        if user:
            return {"user": user.to_dict()}
        else:
            response.status_code = 404
            return {"error": "User not found"}

@app.put("/users/{user_id}")
async def update_user(request, response, user_id: int):
    update_data = request.json

    async with get_db_session(client) as session:
        user = await User.get_by_id(session, user_id)
        if not user:
            response.status_code = 404
            return {"error": "User not found"}

        # Update fields
        for key, value in update_data.items():
            if hasattr(user, key):
                setattr(user, key, value)

        await user.update(session)  # Update user
        return {"user": user.to_dict()}

@app.delete("/users/{user_id}")
async def delete_user(request, response, user_id: int):
    async with get_db_session(client) as session:
        user = await User.get_by_id(session, user_id)
        if not user:
            response.status_code = 404
            return {"error": "User not found"}

        deleted = await user.delete(session)
        return {"deleted": deleted}
```

### Advanced Model Operations

```python
@app.get("/users/search")
async def search_users(request, response):
    query_params = request.query_params
    name_filter = query_params.get("name")

    async with get_db_session(client) as session:
        # Count users
        count = await User.count(session, "name ILIKE $1", f"%{name_filter}%")

        # Get users with pagination
        users = await session.fetch(
            "SELECT * FROM users WHERE name ILIKE $1 LIMIT $2 OFFSET $3",
            f"%{name_filter}%", 10, 0
        )

        # Check if users exist
        exists = await User.exists(session, "name = $1", "Alice")

        return {
            "count": count,
            "users": [User(**user).to_dict() for user in users],
            "exists": exists
        }
```

---

## Query Builder

### Basic Query Building

```python
from nexios_contrib.postgres.utils import QueryBuilder

@app.get("/users/advanced-search")
async def advanced_user_search(request, response):
    query_params = request.query_params

    # Build query dynamically
    query = (QueryBuilder("users")
             .select("id", "name", "email")
             .where("active = $1", True))

    # Add optional filters
    if "name" in query_params:
        query.where_like("name", f"%{query_params['name']}%")

    if "min_age" in query_params:
        query.where_gte("age", int(query_params["min_age"]))

    # Add ordering and pagination
    query.order_by("name").limit(20).offset(0)

    sql, params = query.build()

    async with get_db_session(client) as session:
        users = await session.fetch(sql, *params)
        return {"users": users}
```

### Joins and Aggregations

```python
@app.get("/users/with-posts")
async def users_with_posts(request, response):
    query = (QueryBuilder("users")
             .select("users.id", "users.name", "COUNT(posts.id) as post_count")
             .join("posts", "posts.user_id = users.id", "LEFT")
             .group_by("users.id", "users.name")
             .having("COUNT(posts.id) > $1", 0)
             .order_by("post_count", "DESC")
             .limit(10))

    sql, params = query.build()

    async with get_db_session(client) as session:
        results = await session.fetch(sql, *params)
        return {"users": results}
```

### Insert and Update Queries

```python
@app.post("/bulk-users")
async def create_bulk_users(request, response):
    users_data = request.json["users"]

    # Build insert query
    insert_query = QueryBuilder("users")
    sql, params = insert_query.build_insert({
        "name": "John Doe",
        "email": "john@example.com",
        "active": True
    })

    # Build update query
    update_query = QueryBuilder("users")
    sql, params = update_query.build_update(
        {"name": "Jane Doe", "active": False},
        ["id = $1"]
    )

    async with get_db_session(client) as session:
        # Insert user
        await session.execute(sql, *params)

        # Update user
        await session.execute(sql, *params)
```

---

## Transactions

### Basic Transactions

```python
@app.post("/transfer-money")
async def transfer_money(request, response):
    data = request.json  # {"from_user": 1, "to_user": 2, "amount": 100}

    async with get_db_session(client) as session:
        async with session.transaction():
            # Check balances
            from_balance = await session.fetchval(
                "SELECT balance FROM accounts WHERE user_id = $1",
                data["from_user"]
            )

            to_balance = await session.fetchval(
                "SELECT balance FROM accounts WHERE user_id = $1",
                data["to_user"]
            )

            if from_balance < data["amount"]:
                response.status_code = 400
                return {"error": "Insufficient funds"}

            # Perform transfer
            await session.execute(
                "UPDATE accounts SET balance = balance - $1 WHERE user_id = $2",
                data["amount"], data["from_user"]
            )

            await session.execute(
                "UPDATE accounts SET balance = balance + $1 WHERE user_id = $2",
                data["amount"], data["to_user"]
            )

    return {"message": "Transfer completed"}
```

### Transaction Context Manager

```python
from nexios_contrib.postgres.session import TransactionContext

@app.post("/complex-operation")
async def complex_operation(request, response):
    async with get_db_session(client) as session:
        async with TransactionContext(session) as transaction_session:
            # All operations within this block are transactional
            await transaction_session.execute("INSERT INTO users (name) VALUES ($1)", "Alice")
            await transaction_session.execute("INSERT INTO users (name) VALUES ($1)", "Bob")

            # If an exception occurs, everything rolls back
            # If successful, everything commits
```

### Execute in Transaction

```python
from nexios_contrib.postgres.session import execute_in_transaction

async def create_user_with_profile(user_data, profile_data):
    async def operation(session):
        user = User(**user_data)
        await user.insert(session)

        profile = UserProfile(user_id=user.id, **profile_data)
        await profile.insert(session)

        return user

    user = await execute_in_transaction(client, operation)
    return user
```

---

## Database Utilities

### Data Mapping

```python
from nexios_contrib.postgres.utils import DataMapper

@app.get("/raw-data")
async def get_raw_data(request, response):
    async with get_db_session(client) as session:
        records = await session.fetch("SELECT * FROM users")

        # Convert to dictionaries
        users_dict = DataMapper.records_to_dicts(records)

        # Convert single record
        user_dict = DataMapper.record_to_dict(records[0])

        return {"users": users_dict, "first_user": user_dict}
```

### Database Administration

```python
from nexios_contrib.postgres.utils import DatabaseUtils

@app.get("/db-info")
async def database_info(request, response):
    async with get_db_session(client) as session:
        # Check if table exists
        table_exists = await DatabaseUtils.table_exists(session, "users")

        # Get table information
        table_info = await DatabaseUtils.get_table_info(session, "users")

        # Get table statistics
        stats = await DatabaseUtils.get_table_statistics(session, "users")

        # Get database size
        db_size = await DatabaseUtils.get_database_size(session)

        return {
            "table_exists": table_exists,
            "table_info": table_info,
            "statistics": stats,
            "database_size": db_size
        }
```

### Maintenance Operations

```python
@app.post("/db-maintenance")
async def database_maintenance(request, response):
    async with get_db_session(client) as session:
        # Vacuum table
        await DatabaseUtils.vacuum_table(session, "users", analyze=True)

        # Reindex table
        await DatabaseUtils.reindex_table(session, "users")

        # Get connection count
        connection_count = await DatabaseUtils.get_connection_count(session)

        # Get active queries
        active_queries = await DatabaseUtils.get_active_queries(session)

        return {
            "message": "Maintenance completed",
            "connection_count": connection_count,
            "active_queries": active_queries
        }
```

---

## Migrations

### Migration Manager

```python
from nexios_contrib.postgres.utils import MigrationManager

@app.post("/migrate")
async def run_migrations(request, response):
    async with get_db_session(client) as session:
        migration_manager = MigrationManager(session)

        # Initialize migration system
        await migration_manager.initialize()

        # Apply migration
        await migration_manager.apply_migration(
            version="20240101120000",
            name="create_users_table",
            sql="""
                CREATE TABLE users (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """
        )

        # Get migration status
        status = await migration_manager.get_migration_status()

        return {"status": status}
```

### Migration Status

```python
@app.get("/migrations")
async def migration_status(request, response):
    async with get_db_session(client) as session:
        migration_manager = MigrationManager(session)
        status = await migration_manager.get_migration_status()

        return {
            "applied_migrations": status["applied_migrations"],
            "total_applied": status["total_applied"]
        }
```

---

## Error Handling

### Custom Error Handling

```python
from nexios_contrib.postgres import DatabaseError, ConnectionError, QueryError

@app.exception_handler(DatabaseError)
async def database_error_handler(request, exc):
    return {
        "error": "Database Error",
        "message": str(exc),
        "type": exc.__class__.__name__
    }, 500

@app.exception_handler(ConnectionError)
async def connection_error_handler(request, exc):
    return {
        "error": "Connection Error",
        "message": "Database connection failed"
    }, 503
```

### Query Error Handling

```python
@app.post("/safe-operation")
async def safe_operation(request, response):
    try:
        async with get_db_session(client) as session:
            result = await session.fetch("SELECT * FROM non_existent_table")
            return {"result": result}
    except QueryError as e:
        response.status_code = 400
        return {"error": "Query failed", "message": str(e)}
    except ConnectionError as e:
        response.status_code = 503
        return {"error": "Database unavailable", "message": str(e)}
```

---

## Best Practices

### Connection Pool Management

```python
# Good: Use appropriate pool sizes
db_config = DatabaseConfig(
    min_size=5,      # Start with 5 connections
    max_size=50,     # Scale up to 50 connections
    command_timeout=30  # 30 second timeout
)

# Good: Initialize once at startup
@app.on_event("startup")
async def startup():
    global db_client
    db_client = await initialize_database(db_config)

# Good: Close pool at shutdown
@app.on_event("shutdown")
async def shutdown():
    await close_database()
```

### Session Per Request Pattern

```python
# Good: Use session per request pattern
@app.middleware
async def db_session_middleware(request, response, call_next):
    async with get_db_session(client) as session:
        request.state.db_session = session
        return await call_next()

@app.get("/users")
async def get_users(request, response):
    session = request.state.db_session
    users = await session.fetch("SELECT * FROM users")
    return {"users": users}
```

### Transaction Management

```python
# Good: Use transactions for related operations
@app.post("/user-with-posts")
async def create_user_with_posts(request, response):
    data = request.json

    async with get_db_session(client) as session:
        async with session.transaction():
            # Create user
            user = User(**data["user"])
            await user.insert(session)

            # Create posts
            for post_data in data["posts"]:
                post = Post(user_id=user.id, **post_data)
                await post.insert(session)

    return {"message": "User and posts created"}
```

### Model Validation

```python
# Good: Use Pydantic validation
class User(DatabaseModel):
    name: str = StringField(nullable=False)
    email: str = StringField(nullable=False)
    age: Optional[int] = IntegerField()

    @validator('email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email')
        return v

# Good: Handle validation errors
@app.post("/users")
async def create_user(request, response):
    try:
        user_data = request.json
        user = User(**user_data)
        await user.save(session)
        return {"user": user.to_dict()}
    except ValidationError as e:
        response.status_code = 400
        return {"error": "Validation failed", "details": e.errors()}
```

### Performance Optimization

```python
# Good: Use efficient queries
@app.get("/users/count")
async def get_user_count(request, response):
    # Use fetchval for single values
    count = await session.fetchval("SELECT COUNT(*) FROM users")
    return {"count": count}

@app.get("/users/paginated")
async def get_paginated_users(request, response):
    page = int(request.query_params.get("page", 1))
    per_page = int(request.query_params.get("per_page", 10))
    offset = (page - 1) * per_page

    # Use LIMIT and OFFSET for pagination
    users = await session.fetch(
        "SELECT * FROM users ORDER BY id LIMIT $1 OFFSET $2",
        per_page, offset
    )
    return {"users": users, "page": page, "per_page": per_page}
```

---

## Advanced Features

### Custom Field Types

```python
from nexios_contrib.postgres import FieldDefinition, FieldType

class CustomField:
    @staticmethod
    def JSONField(nullable: bool = False) -> FieldDefinition:
        return FieldDefinition(
            FieldType.JSONB,
            nullable=nullable,
            default={}
        )

    @staticmethod
    def ArrayField(item_type: FieldType, nullable: bool = False) -> FieldDefinition:
        return FieldDefinition(
            FieldType.ARRAY,
            nullable=nullable
        )

class Product(DatabaseModel):
    id: int = IntegerField(primary_key=True)
    name: str = StringField(nullable=False)
    tags: list = CustomField.ArrayField(FieldType.TEXT)
    metadata: dict = CustomField.JSONField()
```

### Custom Query Builder

```python
from nexios_contrib.postgres.utils import QueryBuilder

class UserQueryBuilder(QueryBuilder):
    def __init__(self):
        super().__init__("users")

    def active_users(self):
        return self.where("active = $1", True)

    def by_role(self, role: str):
        return self.where("role = $1", role)

    def search_by_name(self, name: str):
        return self.where("name ILIKE $1", f"%{name}%")

# Usage
@app.get("/users/search")
async def search_users(request, response):
    name = request.query_params.get("name")

    query = UserQueryBuilder().active_users().search_by_name(name)
    sql, params = query.build()

    async with get_db_session(client) as session:
        users = await session.fetch(sql, *params)
        return {"users": users}
```

### Database Monitoring

```python
from nexios_contrib.postgres.utils import DatabaseUtils

@app.get("/db/metrics")
async def database_metrics(request, response):
    async with get_db_session(client) as session:
        # Get connection statistics
        connection_count = await DatabaseUtils.get_connection_count(session)

        # Get active queries
        active_queries = await DatabaseUtils.get_active_queries(session)

        # Get table statistics
        user_stats = await DatabaseUtils.get_table_statistics(session, "users")
        post_stats = await DatabaseUtils.get_table_statistics(session, "posts")

        return {
            "connections": {
                "active": connection_count,
                "queries": active_queries
            },
            "tables": {
                "users": user_stats,
                "posts": post_stats
            }
        }
```

---

## Troubleshooting

### Common Issues

1. **Connection Pool Exhaustion**
   ```python
   # Check pool size
   pool_info = await client.get_pool_info()
   print(f"Pool size: {pool_info['size']}, Free: {pool_info['free_size']}")
   ```

2. **Slow Queries**
   ```python
   # Use EXPLAIN ANALYZE
   query = "EXPLAIN ANALYZE SELECT * FROM users WHERE name = $1"
   result = await session.fetch(query, "John")
   ```

3. **Transaction Deadlocks**
   ```python
   # Use proper transaction ordering
   async with session.transaction():
       await session.execute("UPDATE table1 SET ...")
       await session.execute("UPDATE table2 SET ...")
   ```

4. **Memory Issues with Large Result Sets**
   ```python
   # Use server-side cursors for large datasets
   async with client.connection() as conn:
       cursor = await conn.execute("DECLARE cursor CURSOR FOR SELECT * FROM large_table")
       while True:
           records = await conn.fetch("FETCH 100 FROM cursor")
           if not records:
               break
           # Process records in batches
   ```

---

## Contributing

Contributions are welcome! Please see the main Nexios contrib repository for contribution guidelines.

---

## License

This module is part of the Nexios contrib package and follows the same license as the main Nexios framework.
