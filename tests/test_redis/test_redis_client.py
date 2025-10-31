"""
Integration tests for RedisClient class.
"""
import pytest
import json
from unittest.mock import AsyncMock

from nexios_contrib.redis.client import RedisClient, RedisOperationError
from nexios_contrib.redis.config import RedisConfig


class TestRedisClient:
    """Test RedisClient functionality."""

    async def test_client_initialization(self, redis_config):
        """Test Redis client initialization."""
        client = RedisClient(redis_config)
        
        assert client.config == redis_config
        assert client._redis is None
        assert not client._connected

    async def test_client_connection(self, redis_client, mock_redis):
        """Test Redis client connection."""
        # Client should already be connected via fixture
        assert redis_client._connected
        assert redis_client._redis == mock_redis
        
        # Test ping
        result = await redis_client.ping()
        assert result is True
        mock_redis.ping.assert_called_once()

    async def test_client_close(self, redis_client, mock_redis):
        """Test Redis client close."""
        await redis_client.close()
        
        assert not redis_client._connected
        assert redis_client._redis is None
        mock_redis.close.assert_called_once()

    async def test_basic_operations(self, redis_client, mock_redis):
        """Test basic Redis operations."""
        # Test SET
        mock_redis.set.return_value = True
        result = await redis_client.set("test_key", "test_value")
        assert result is True
        mock_redis.set.assert_called_with("test_key", "test_value", ex=None, px=None, nx=False, xx=False)
        
        # Test GET
        mock_redis.get.return_value = "test_value"
        result = await redis_client.get("test_key")
        assert result == "test_value"
        mock_redis.get.assert_called_with("test_key")
        
        # Test DELETE
        mock_redis.delete.return_value = 1
        result = await redis_client.delete("test_key")
        assert result == 1
        mock_redis.delete.assert_called_with("test_key")
        
        # Test EXISTS
        mock_redis.exists.return_value = 1
        result = await redis_client.exists("test_key")
        assert result == 1
        mock_redis.exists.assert_called_with("test_key")

    async def test_expiration_operations(self, redis_client, mock_redis):
        """Test Redis expiration operations."""
        # Test EXPIRE
        mock_redis.expire.return_value = True
        result = await redis_client.expire("test_key", 300)
        assert result is True
        mock_redis.expire.assert_called_with("test_key", 300, nx=False, xx=False, gt=False, lt=False)
        
        # Test TTL
        mock_redis.ttl.return_value = 300
        result = await redis_client.ttl("test_key")
        assert result == 300
        mock_redis.ttl.assert_called_with("test_key")

    async def test_counter_operations(self, redis_client, mock_redis):
        """Test Redis counter operations."""
        # Test INCR
        mock_redis.incr.return_value = 5
        result = await redis_client.incr("counter", 5)
        assert result == 5
        mock_redis.incr.assert_called_with("counter", 5)
        
        # Test DECR
        mock_redis.decr.return_value = 3
        result = await redis_client.decr("counter", 2)
        assert result == 3
        mock_redis.decr.assert_called_with("counter", 2)

    async def test_hash_operations(self, redis_client, mock_redis):
        """Test Redis hash operations."""
        # Test HSET
        mock_redis.hset.return_value = 1
        result = await redis_client.hset("user:123", "name", "John")
        assert result == 1
        mock_redis.hset.assert_called_with("user:123", "name", "John")
        
        # Test HGET
        mock_redis.hget.return_value = "John"
        result = await redis_client.hget("user:123", "name")
        assert result == "John"
        mock_redis.hget.assert_called_with("user:123", "name")
        
        # Test HGETALL
        mock_redis.hgetall.return_value = {"name": "John", "age": "30"}
        result = await redis_client.hgetall("user:123")
        assert result == {"name": "John", "age": "30"}
        mock_redis.hgetall.assert_called_with("user:123")

    async def test_list_operations(self, redis_client, mock_redis):
        """Test Redis list operations."""
        # Test LPUSH
        mock_redis.lpush.return_value = 2
        result = await redis_client.lpush("messages", "msg1", "msg2")
        assert result == 2
        mock_redis.lpush.assert_called_with("messages", "msg1", "msg2")
        
        # Test RPUSH
        mock_redis.rpush.return_value = 3
        result = await redis_client.rpush("messages", "msg3")
        assert result == 3
        mock_redis.rpush.assert_called_with("messages", "msg3")
        
        # Test LPOP
        mock_redis.lpop.return_value = "msg1"
        result = await redis_client.lpop("messages")
        assert result == "msg1"
        mock_redis.lpop.assert_called_with("messages", None)
        
        # Test RPOP
        mock_redis.rpop.return_value = "msg3"
        result = await redis_client.rpop("messages")
        assert result == "msg3"
        mock_redis.rpop.assert_called_with("messages", None)
        
        # Test LLEN
        mock_redis.llen.return_value = 1
        result = await redis_client.llen("messages")
        assert result == 1
        mock_redis.llen.assert_called_with("messages")

    async def test_set_operations(self, redis_client, mock_redis):
        """Test Redis set operations."""
        # Test SADD
        mock_redis.sadd.return_value = 2
        result = await redis_client.sadd("tags", "python", "redis")
        assert result == 2
        mock_redis.sadd.assert_called_with("tags", "python", "redis")
        
        # Test SMEMBERS
        mock_redis.smembers.return_value = {"python", "redis"}
        result = await redis_client.smembers("tags")
        assert result == {"python", "redis"}
        mock_redis.smembers.assert_called_with("tags")
        
        # Test SREM
        mock_redis.srem.return_value = 1
        result = await redis_client.srem("tags", "python")
        assert result == 1
        mock_redis.srem.assert_called_with("tags", "python")
        
        # Test SCARD
        mock_redis.scard.return_value = 1
        result = await redis_client.scard("tags")
        assert result == 1
        mock_redis.scard.assert_called_with("tags")

   

    
    async def test_keys_operation(self, redis_client, mock_redis):
        """Test Redis KEYS operation."""
        mock_redis.keys.return_value = ["user:123", "user:456"]
        result = await redis_client.keys("user:*")
        assert result == ["user:123", "user:456"]
        mock_redis.keys.assert_called_with("user:*")

    async def test_flushdb_operation(self, redis_client, mock_redis):
        """Test Redis FLUSHDB operation."""
        mock_redis.flushdb.return_value = None
        result = await redis_client.flushdb()
        assert result is True
        mock_redis.flushdb.assert_called_with(asynchronous=False)

    async def test_execute_command(self, redis_client, mock_redis):
        """Test Redis raw command execution."""
        mock_redis.execute_command.return_value = "PONG"
        result = await redis_client.execute("PING")
        assert result == "PONG"
        mock_redis.execute_command.assert_called_with("PING")

    async def test_operation_errors(self, redis_client, mock_redis):
        """Test Redis operation error handling."""
        # Test GET error
        mock_redis.get.side_effect = Exception("Connection error")
        
        with pytest.raises(RedisOperationError, match="Failed to get key 'test_key'"):
            await redis_client.get("test_key")
        
        # Test SET error
        mock_redis.set.side_effect = Exception("Connection error")
        
        with pytest.raises(RedisOperationError, match="Failed to set key 'test_key'"):
            await redis_client.set("test_key", "value")

    async def test_auto_connect_on_operation(self, redis_config, mock_redis):
        """Test automatic connection when performing operations."""
        client = RedisClient(redis_config)
        client._redis = mock_redis
        client._connected = False
        
        # Mock the connect method
        async def mock_connect():
            client._connected = True
            client._redis = mock_redis
        
        client.connect = mock_connect
        
        # Perform operation - should auto-connect
        mock_redis.get.return_value = "value"
        result = await client.get("test_key")
        
        assert result == "value"
        assert client._connected

    def test_client_repr(self, redis_client, redis_config):
        """Test Redis client string representation."""
        repr_str = repr(redis_client)
        assert "RedisClient" in repr_str
        assert "connected" in repr_str
        assert str(redis_config) in repr_str