"""
Real Redis integration tests (requires actual Redis server).

These tests require a running Redis server and are marked with @pytest.mark.integration
so they can be skipped in CI/CD environments where Redis is not available.
"""
import pytest
import asyncio
import json
from typing import Optional

from nexios import NexiosApp, Depend
from nexios.http import Request, Response
from nexios.testclient import TestClient

from nexios_contrib.redis import (
    init_redis, get_redis, RedisClient, RedisConfig, RedisConnectionError
)


# Skip these tests if Redis is not available
pytestmark = pytest.mark.integration


@pytest.fixture(scope="session")
def redis_available():
    """Check if Redis server is available for testing."""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=15, decode_responses=True)
        r.ping()
        return True
    except (ImportError, redis.ConnectionError, redis.TimeoutError):
        pytest.skip("Redis server not available for integration tests")


@pytest.fixture
async def real_redis_client(redis_available):
    """Create a real Redis client for testing."""
    config = RedisConfig(
        url="redis://localhost:6379",
        db=15,  # Use test database
        decode_responses=True
    )
    
    client = RedisClient(config)
    await client.connect()
    
    # Clean up test database before tests
    await client.flushdb()
    
    yield client
    
    # Clean up after tests
    await client.flushdb()
    await client.close()


@pytest.fixture
def real_redis_app(redis_available):
    """Create a Nexios app with real Redis connection."""
    app = NexiosApp()
    
    init_redis(
        app,
        url="redis://localhost:6379",
        db=15,  # Test database
        decode_responses=True
    )
    
    return app


@pytest.fixture
def real_test_client(real_redis_app):
    """Create a test client with real Redis."""
    return TestClient(real_redis_app)


class TestRealRedisIntegration:
    """Test Redis integration with actual Redis server."""

    async def test_real_redis_connection(self, real_redis_client):
        """Test actual Redis connection."""
        # Test ping
        result = await real_redis_client.ping()
        assert result is True

    async def test_real_basic_operations(self, real_redis_client):
        """Test basic Redis operations with real server."""
        # Test SET and GET
        await real_redis_client.set("test_key", "test_value")
        value = await real_redis_client.get("test_key")
        assert value == "test_value"
        
        # Test EXISTS
        exists = await real_redis_client.exists("test_key")
        assert exists == 1
        
        # Test DELETE
        deleted = await real_redis_client.delete("test_key")
        assert deleted == 1
        
        # Verify deletion
        value = await real_redis_client.get("test_key")
        assert value is None

    async def test_real_expiration(self, real_redis_client):
        """Test Redis expiration with real server."""
        # Set key with expiration
        await real_redis_client.set("expire_key", "expire_value", ex=1)
        
        # Check TTL
        ttl = await real_redis_client.ttl("expire_key")
        assert 0 < ttl <= 1
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        
        # Key should be expired
        value = await real_redis_client.get("expire_key")
        assert value is None

    async def test_real_counter_operations(self, real_redis_client):
        """Test Redis counter operations with real server."""
        # Test INCR
        value1 = await real_redis_client.incr("counter")
        assert value1 == 1
        
        value2 = await real_redis_client.incr("counter", 5)
        assert value2 == 6
        
        # Test DECR
        value3 = await real_redis_client.decr("counter", 2)
        assert value3 == 4

    async def test_real_hash_operations(self, real_redis_client):
        """Test Redis hash operations with real server."""
        # Test HSET
        result = await real_redis_client.hset("user:123", "name", "John")
        assert result == 1
        
        result = await real_redis_client.hset("user:123", "email", "john@example.com")
        assert result == 1
        
        # Test HGET
        name = await real_redis_client.hget("user:123", "name")
        assert name == "John"
        
        # Test HGETALL
        user_data = await real_redis_client.hgetall("user:123")
        assert user_data == {"name": "John", "email": "john@example.com"}

    async def test_real_list_operations(self, real_redis_client):
        """Test Redis list operations with real server."""
        # Test LPUSH and RPUSH
        length1 = await real_redis_client.lpush("messages", "msg1")
        assert length1 == 1
        
        length2 = await real_redis_client.rpush("messages", "msg2")
        assert length2 == 2
        
        # Test LLEN
        length = await real_redis_client.llen("messages")
        assert length == 2
        
        # Test LPOP and RPOP
        left_msg = await real_redis_client.lpop("messages")
        assert left_msg == "msg1"
        
        right_msg = await real_redis_client.rpop("messages")
        assert right_msg == "msg2"
        
        # List should be empty
        length = await real_redis_client.llen("messages")
        assert length == 0

    async def test_real_set_operations(self, real_redis_client):
        """Test Redis set operations with real server."""
        # Test SADD
        added = await real_redis_client.sadd("tags", "python", "redis", "cache")
        assert added == 3
        
        # Test SCARD
        size = await real_redis_client.scard("tags")
        assert size == 3
        
        # Test SMEMBERS
        members = await real_redis_client.smembers("tags")
        assert set(members) == {"python", "redis", "cache"}
        
        # Test SREM
        removed = await real_redis_client.srem("tags", "cache")
        assert removed == 1
        
        # Verify removal
        size = await real_redis_client.scard("tags")
        assert size == 2

   

    async def test_real_keys_operation(self, real_redis_client):
        """Test Redis KEYS operation with real server."""
        # Set up test keys
        await real_redis_client.set("user:123", "data1")
        await real_redis_client.set("user:456", "data2")
        await real_redis_client.set("session:abc", "session_data")
        
        # Test KEYS with pattern
        user_keys = await real_redis_client.keys("user:*")
        assert set(user_keys) == {"user:123", "user:456"}
        
        all_keys = await real_redis_client.keys("*")
        assert len(all_keys) >= 3

   
    async def test_real_connection_error_handling(self):
        """Test connection error handling with invalid Redis config."""
        config = RedisConfig(
            url="redis://localhost:9999",  # Invalid port
            socket_connect_timeout=1.0
        )
        
        client = RedisClient(config)
        
        with pytest.raises(ConnectionError):
            await client.connect()

    async def test_real_database_isolation(self, redis_available):
        """Test that different databases are isolated."""
        # Create clients for different databases
        config1 = RedisConfig(url="redis://localhost:6379", db=14)
        config2 = RedisConfig(url="redis://localhost:6379", db=15)
        
        client1 = RedisClient(config1)
        client2 = RedisClient(config2)
        
        try:
            await client1.connect()
            await client2.connect()
            
            # Set value in database 14
            await client1.set("isolation_test", "db14_value")
            
            # Check that it doesn't exist in database 15
            value_db15 = await client2.get("isolation_test")
            assert value_db15 is None
            
            # Set different value in database 15
            await client2.set("isolation_test", "db15_value")
            
            # Verify both databases have their own values
            value_db14 = await client1.get("isolation_test")
            value_db15 = await client2.get("isolation_test")
            
            assert value_db14 == "db14_value"
            assert value_db15 == "db15_value"
            
        finally:
            await client1.flushdb()
            await client2.flushdb()
            await client1.close()
            await client2.close()