"""
Test configuration and fixtures for Redis integration tests.
"""
import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

from nexios import NexiosApp
from nexios.testclient import TestClient
from nexios_contrib.redis import RedisClient, RedisConfig, init_redis


# @pytest.fixture(scope="session")
# def event_loop():
#     """Create an instance of the default event loop for the test session."""
#     loop = asyncio.get_event_loop_policy().new_event_loop()
#     yield loop
#     loop.close()


@pytest.fixture
def redis_config():
    """Create a Redis configuration for testing."""
    return RedisConfig(
        url="redis://localhost:6379",
        db=15,  # Use a test database
        decode_responses=True,
        socket_timeout=5.0,
        socket_connect_timeout=5.0
    )


@pytest.fixture
def mock_redis():
    """Create a mock Redis client for testing without actual Redis connection."""
    mock = AsyncMock()
    
    # Mock common Redis operations
    mock.ping.return_value = True
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = 1
    mock.exists.return_value = 0
    mock.expire.return_value = True
    mock.ttl.return_value = -1
    mock.incr.return_value = 1
    mock.decr.return_value = 0
    mock.keys.return_value = []
    mock.flushdb.return_value = True
    
    # Hash operations
    mock.hget.return_value = None
    mock.hset.return_value = 1
    mock.hgetall.return_value = {}
    
    # List operations
    mock.lpush.return_value = 1
    mock.rpush.return_value = 1
    mock.lpop.return_value = None
    mock.rpop.return_value = None
    mock.llen.return_value = 0
    
    # Set operations
    mock.sadd.return_value = 1
    mock.smembers.return_value = set()
    mock.srem.return_value = 1
    mock.scard.return_value = 0
    
    # JSON operations (mock for redis-py with JSON support)
    mock.json.return_value = mock
    
    mock.close.return_value = None
    
    return mock


@pytest.fixture
async def redis_client(redis_config, mock_redis):
    """Create a Redis client with mocked connection."""
    client = RedisClient(redis_config)
    
    # Replace the actual Redis connection with our mock
    client._redis = mock_redis
    client._connected = True
    
    yield client
    
    await client.close()


@pytest.fixture
def app_with_redis():
    """Create a Nexios app with Redis initialized."""
    app = NexiosApp()
    
    # Initialize Redis with test configuration
    init_redis(
        app,
        url="redis://localhost:6379",
        db=15,  # Test database
        decode_responses=True
    )
    
    return app


@pytest.fixture
def app_with_mock_redis(mock_redis):
    """Create a Nexios app with mocked Redis."""
    app = NexiosApp()
    
    # Create a mock Redis client
    from nexios_contrib.redis import _redis_client
    from nexios_contrib.redis.client import RedisClient
    from nexios_contrib.redis.config import RedisConfig
    
    config = RedisConfig(url="redis://localhost:6379", db=15)
    client = RedisClient(config)
    client._redis = mock_redis
    client._connected = True
    
    # Store in app state and global variable
    app.state["redis"] = client
    import nexios_contrib.redis
    nexios_contrib.redis._redis_client = client
    
    yield app
    
    # Cleanup
    nexios_contrib.redis._redis_client = None


@pytest.fixture
def test_client_with_redis(app_with_mock_redis):
    """Create a test client with mocked Redis."""
    return TestClient(app_with_mock_redis)



@pytest.fixture
def sample_data():
    """Sample data for testing."""
    return {
        "user": {
            "id": "123",
            "name": "John Doe",
            "email": "john@example.com",
            "age": 30
        },
        "session": {
            "id": "session_abc123",
            "user_id": "123",
            "expires_at": "2024-12-31T23:59:59Z"
        },
        "cache_data": {
            "key": "expensive_computation",
            "value": {"result": 42, "computed_at": "2024-01-01T00:00:00Z"}
        }
    }


@pytest.fixture
def redis_keys():
    """Common Redis keys for testing."""
    return {
        "user": "user:123",
        "session": "session:abc123",
        "counter": "counter:visits",
        "cache": "cache:expensive_computation",
        "list": "messages:inbox",
        "set": "tags:article:123",
        "hash": "profile:123"
    }