# Nexios Tortoise ORM Integration

A comprehensive Tortoise ORM integration for the Nexios web framework, providing seamless database connectivity, automatic connection management, and robust exception handling.

## Features

- 🚀 **Easy Setup**: Simple initialization with minimal configuration
- 🔄 **Lifecycle Management**: Automatic startup and shutdown handling
- 🛡️ **Exception Handling**: Built-in handlers for common database exceptions
- 🎯 **Simple Access**: Direct client access without complex DI
- 🏗️ **Schema Management**: Optional automatic schema generation
- 🔗 **Multiple Databases**: Support for multiple database connections
- 📝 **Type Safety**: Full type hints and IDE support

## Installation

```bash
pip install tortoise-orm
```

## Quick Start

### Basic Setup

```python
from nexios import NexiosApp
from nexios_contrib.tortoise import init_tortoise

app = NexiosApp()

# Initialize Tortoise ORM
init_tortoise(
    app,
    db_url="sqlite://db.sqlite3",
    modules={"models": ["app.models"]},
    generate_schemas=True
)
```

### Define Models

```python
# app/models.py
from tortoise.models import Model
from tortoise import fields

class User(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100)
    email = fields.CharField(max_length=255, unique=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "users"

class Post(Model):
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=200)
    content = fields.TextField()
    author = fields.ForeignKeyField("models.User", related_name="posts")
    created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "posts"
```

### Use in Route Handlers

```python
from nexios_contrib.tortoise import get_tortoise_client
from app.models import User, Post

@app.get("/users")
async def list_users(request, response):
    users = await User.all()
    return response.json([
        {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
        for user in users
    ])

@app.get("/users/{user_id}")
async def get_user(request, response):
    user_id = request.path_params["user_id"]
    try:
        user = await User.get(id=user_id)
        return response.json({
            "id": user.id,
            "name": user.name,
            "email": user.email
        })
    except User.DoesNotExist:
        return response.status(404).json({"error": "User not found"})

@app.post("/users")
async def create_user(request, response):
    data = await request.json()
    try:
        user = await User.create(
            name=data["name"],
            email=data["email"]
        )
        return response.status(201).json({
            "id": user.id,
            "name": user.name,
            "email": user.email
        })
    except Exception as e:
        return response.status(400).json({"error": str(e)})
```

## Configuration

### Environment Variables

```python
from nexios_contrib.tortoise import TortoiseConfig

# Load from environment variables
config = TortoiseConfig.from_env()
init_tortoise(app, **config.dict())
```

Set these environment variables:
```bash
TORTOISE_DB_URL=postgresql://user:password@localhost:5432/mydb
TORTOISE_GENERATE_SCHEMAS=true
TORTOISE_USE_TZ=true
TORTOISE_MODULES='{"models": ["app.models", "app.user_models"]}'
```

### Multiple Databases

```python
init_tortoise(
    app,
    db_url="sqlite://main.db",
    modules={
        "models": ["app.models"],
        "users": ["app.user_models"],
        "analytics": ["app.analytics_models"]
    },
    connections={
        "default": "sqlite://main.db",
        "users_db": "postgresql://user:pass@localhost/users",
        "analytics_db": "postgresql://user:pass@localhost/analytics"
    }
)
```

## Exception Handling

The integration automatically handles common Tortoise ORM exceptions:

### Built-in Exception Handlers

- **IntegrityError** → 400 Bad Request
- **DoesNotExist** → 404 Not Found  
- **ValidationError** → 422 Unprocessable Entity
- **ConnectionError** → 503 Service Unavailable
- **TransactionError** → 500 Internal Server Error

### Custom Exception Handlers

```python
from nexios_contrib.tortoise.exceptions import create_custom_exception_handler

# Create custom handler
custom_handler = create_custom_exception_handler(
    status_code=409,
    error_message="Resource already exists",
    error_type="duplicate_error"
)

@app.exception_handler(MyCustomError)
async def handle_custom_error(request, response, exc):
    return await custom_handler(request, response, exc)
```

### Disable Exception Handlers

```python
init_tortoise(
    app,
    db_url="sqlite://db.sqlite3",
    modules={"models": ["app.models"]},
    add_exception_handlers=False  # Disable automatic exception handling
)
```

## Client Access

### Direct Client Access

```python
from nexios_contrib.tortoise import get_tortoise_client

@app.get("/users")
async def list_users(request, response):
    # Get the Tortoise client directly
    tortoise = get_tortoise_client()
    # Use tortoise client for raw queries if needed
    pass

@app.get("/raw-query")
async def raw_query(request, response):
    tortoise = get_tortoise_client()
    result = await tortoise.execute_query("SELECT COUNT(*) FROM users")
    return response.json(result)
```

### Transaction Support

```python
from tortoise.transactions import in_transaction

@app.post("/transfer")
async def transfer_funds(request, response):
    data = await request.json()
    
    async with in_transaction():
        # All operations in this block are transactional
        sender = await User.get(id=data["sender_id"])
        receiver = await User.get(id=data["receiver_id"])
        
        sender.balance -= data["amount"]
        receiver.balance += data["amount"]
        
        await sender.save()
        await receiver.save()
        
        return response.json({"status": "success"})
```

## Advanced Usage

### Raw SQL Queries

```python
@app.get("/stats")
async def get_stats(request, response):
    tortoise = get_tortoise_client()
    result = await tortoise.execute_query(
        "SELECT COUNT(*) as user_count, AVG(age) as avg_age FROM users WHERE active = ?",
        True
    )
    return response.json(result[0])
```

### Schema Management

```python
# Generate schemas programmatically
@app.post("/admin/generate-schemas")
async def generate_schemas(request, response):
    tortoise = get_tortoise_client()
    await tortoise.generate_schemas(safe=False)  # Drop existing tables
    return response.json({"status": "schemas generated"})
```

### Health Checks

```python
@app.get("/health/db")
async def db_health_check(request, response):
    try:
        tortoise = get_tortoise_client()
        # Simple query to test connection
        await tortoise.execute_query("SELECT 1")
        return response.json({"status": "healthy"})
    except Exception as e:
        return response.status(503).json({"status": "unhealthy", "error": str(e)})
```

## Supported Databases

- **SQLite**: `sqlite://path/to/db.sqlite3`
- **PostgreSQL**: `postgres://user:password@host:port/database`
- **MySQL**: `mysql://user:password@host:port/database`
- **AsyncPG**: `asyncpg://user:password@host:port/database`
- **AioMySQL**: `aiomysql://user:password@host:port/database`

## Best Practices

1. **Always use transactions** for operations that modify multiple records
2. **Handle exceptions gracefully** with proper HTTP status codes
3. **Use connection pooling** for production deployments
4. **Validate input data** before database operations
5. **Use indexes** on frequently queried fields
6. **Monitor database performance** in production

## Error Handling Examples

```python
from tortoise.exceptions import IntegrityError, DoesNotExist

@app.post("/users")
async def create_user(request, response):
    data = await request.json()
    
    try:
        user = await User.create(**data)
        return response.status(201).json(await user.to_dict())
    
    except IntegrityError as e:
        # Handled automatically by exception handlers
        # Returns 400 with proper error message
        raise e
    
    except DoesNotExist:
        # Handled automatically by exception handlers  
        # Returns 404 with proper error message
        raise e
```

## Migration from FastAPI

If you're migrating from FastAPI's Tortoise integration:

```python
# FastAPI style
from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise

app = FastAPI()
register_tortoise(
    app,
    db_url="sqlite://db.sqlite3",
    modules={"models": ["app.models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)

# Nexios style  
from nexios import NexiosApp
from nexios_contrib.tortoise import init_tortoise

app = NexiosApp()
init_tortoise(
    app,
    db_url="sqlite://db.sqlite3",
    modules={"models": ["app.models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)
```

The API is intentionally similar to make migration easier!

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.