"""
Integration tests for Redis utility functions.
"""
import pytest
import json
from unittest.mock import patch

from nexios_contrib.redis import utils


class TestRedisUtils:
    """Test Redis utility functions."""

    @patch('nexios_contrib.redis.utils.get_redis_client')
    async def test_redis_get(self, mock_get_client, mock_redis):
        """Test redis_get utility function."""
        mock_get_client.return_value = mock_redis
        mock_redis.get.return_value = "test_value"
        
        result = await utils.redis_get("test_key")
        
        assert result == "test_value"
        mock_redis.get.assert_called_with("test_key")

    @patch('nexios_contrib.redis.utils.get_redis_client')
    async def test_redis_set(self, mock_get_client, mock_redis):
        """Test redis_set utility function."""
        mock_get_client.return_value = mock_redis
        mock_redis.set.return_value = True
        
        result = await utils.redis_set("test_key", "test_value", ex=300)
        
        assert result is True
        mock_redis.set.assert_called_with("test_key", "test_value", ex=300, px=None, nx=False, xx=False)

    @patch('nexios_contrib.redis.utils.get_redis_client')
    async def test_redis_delete(self, mock_get_client, mock_redis):
        """Test redis_delete utility function."""
        mock_get_client.return_value = mock_redis
        mock_redis.delete.return_value = 2
        
        result = await utils.redis_delete("key1", "key2")
        
        assert result == 2
        mock_redis.delete.assert_called_with("key1", "key2")

    @patch('nexios_contrib.redis.utils.get_redis_client')
    async def test_redis_exists(self, mock_get_client, mock_redis):
        """Test redis_exists utility function."""
        mock_get_client.return_value = mock_redis
        mock_redis.exists.return_value = 1
        
        result = await utils.redis_exists("test_key")
        
        assert result == 1
        mock_redis.exists.assert_called_with("test_key")

    @patch('nexios_contrib.redis.utils.get_redis_client')
    async def test_redis_expire(self, mock_get_client, mock_redis):
        """Test redis_expire utility function."""
        mock_get_client.return_value = mock_redis
        mock_redis.expire.return_value = True
        
        result = await utils.redis_expire("test_key", 300, nx=True)
        
        assert result is True
        mock_redis.expire.assert_called_with("test_key", 300, nx=True, xx=False, gt=False, lt=False)

    @patch('nexios_contrib.redis.utils.get_redis_client')
    async def test_redis_ttl(self, mock_get_client, mock_redis):
        """Test redis_ttl utility function."""
        mock_get_client.return_value = mock_redis
        mock_redis.ttl.return_value = 250
        
        result = await utils.redis_ttl("test_key")
        
        assert result == 250
        mock_redis.ttl.assert_called_with("test_key")    
    @patch('nexios_contrib.redis.utils.get_redis_client')
    async def test_redis_incr(self, mock_get_client, mock_redis):
        """Test redis_incr utility function."""
        mock_get_client.return_value = mock_redis
        mock_redis.incr.return_value = 5
        
        result = await utils.redis_incr("counter", 3)
        
        assert result == 5
        mock_redis.incr.assert_called_with("counter", 3)

    @patch('nexios_contrib.redis.utils.get_redis_client')
    async def test_redis_decr(self, mock_get_client, mock_redis):
        """Test redis_decr utility function."""
        mock_get_client.return_value = mock_redis
        mock_redis.decr.return_value = 2
        
        result = await utils.redis_decr("counter", 1)
        
        assert result == 2
        mock_redis.decr.assert_called_with("counter", 1)

    @patch('nexios_contrib.redis.utils.get_redis_client')
    async def test_redis_json_get(self, mock_get_client, mock_redis):
        """Test redis_json_get utility function."""
        mock_get_client.return_value = mock_redis
        test_data = {"name": "John", "age": 30}
        mock_redis.json_get.return_value = test_data
        
        result = await utils.redis_json_get("user:123", ".")
        
        assert result == test_data
        mock_redis.json_get.assert_called_with("user:123", ".")

    @patch('nexios_contrib.redis.utils.get_redis_client')
    async def test_redis_json_set(self, mock_get_client, mock_redis):
        """Test redis_json_set utility function."""
        mock_get_client.return_value = mock_redis
        mock_redis.json_set.return_value = True
        test_data = {"name": "John", "age": 30}
        
        result = await utils.redis_json_set("user:123", ".", test_data, nx=True)
        
        assert result is True
        mock_redis.json_set.assert_called_with("user:123", ".", test_data, nx=True, xx=False)

    @patch('nexios_contrib.redis.utils.get_redis_client')
    async def test_redis_hget(self, mock_get_client, mock_redis):
        """Test redis_hget utility function."""
        mock_get_client.return_value = mock_redis
        mock_redis.hget.return_value = "John"
        
        result = await utils.redis_hget("user:123", "name")
        
        assert result == "John"
        mock_redis.hget.assert_called_with("user:123", "name")

    @patch('nexios_contrib.redis.utils.get_redis_client')
    async def test_redis_hset(self, mock_get_client, mock_redis):
        """Test redis_hset utility function."""
        mock_get_client.return_value = mock_redis
        mock_redis.hset.return_value = 1
        
        result = await utils.redis_hset("user:123", "name", "John")
        
        assert result == 1
        mock_redis.hset.assert_called_with("user:123", "name", "John")

    @patch('nexios_contrib.redis.utils.get_redis_client')
    async def test_redis_hgetall(self, mock_get_client, mock_redis):
        """Test redis_hgetall utility function."""
        mock_get_client.return_value = mock_redis
        test_hash = {"name": "John", "email": "john@example.com"}
        mock_redis.hgetall.return_value = test_hash
        
        result = await utils.redis_hgetall("user:123")
        
        assert result == test_hash
        mock_redis.hgetall.assert_called_with("user:123")

    @patch('nexios_contrib.redis.utils.get_redis_client')
    async def test_redis_lpush(self, mock_get_client, mock_redis):
        """Test redis_lpush utility function."""
        mock_get_client.return_value = mock_redis
        mock_redis.lpush.return_value = 3
        
        result = await utils.redis_lpush("messages", "msg1", "msg2")
        
        assert result == 3
        mock_redis.lpush.assert_called_with("messages", "msg1", "msg2")

    @patch('nexios_contrib.redis.utils.get_redis_client')
    async def test_redis_rpush(self, mock_get_client, mock_redis):
        """Test redis_rpush utility function."""
        mock_get_client.return_value = mock_redis
        mock_redis.rpush.return_value = 4
        
        result = await utils.redis_rpush("messages", "msg3")
        
        assert result == 4
        mock_redis.rpush.assert_called_with("messages", "msg3")

    @patch('nexios_contrib.redis.utils.get_redis_client')
    async def test_redis_lpop(self, mock_get_client, mock_redis):
        """Test redis_lpop utility function."""
        mock_get_client.return_value = mock_redis
        mock_redis.lpop.return_value = "msg1"
        
        result = await utils.redis_lpop("messages")
        
        assert result == "msg1"
        mock_redis.lpop.assert_called_with("messages", None)

    @patch('nexios_contrib.redis.utils.get_redis_client')
    async def test_redis_rpop(self, mock_get_client, mock_redis):
        """Test redis_rpop utility function."""
        mock_get_client.return_value = mock_redis
        mock_redis.rpop.return_value = "msg3"
        
        result = await utils.redis_rpop("messages", 2)
        
        assert result == "msg3"
        mock_redis.rpop.assert_called_with("messages", 2)

    @patch('nexios_contrib.redis.utils.get_redis_client')
    async def test_redis_llen(self, mock_get_client, mock_redis):
        """Test redis_llen utility function."""
        mock_get_client.return_value = mock_redis
        mock_redis.llen.return_value = 5
        
        result = await utils.redis_llen("messages")
        
        assert result == 5
        mock_redis.llen.assert_called_with("messages")

    @patch('nexios_contrib.redis.utils.get_redis_client')
    async def test_redis_sadd(self, mock_get_client, mock_redis):
        """Test redis_sadd utility function."""
        mock_get_client.return_value = mock_redis
        mock_redis.sadd.return_value = 2
        
        result = await utils.redis_sadd("tags", "python", "redis")
        
        assert result == 2
        mock_redis.sadd.assert_called_with("tags", "python", "redis")

    @patch('nexios_contrib.redis.utils.get_redis_client')
    async def test_redis_smembers(self, mock_get_client, mock_redis):
        """Test redis_smembers utility function."""
        mock_get_client.return_value = mock_redis
        mock_redis.smembers.return_value = ["python", "redis"]
        
        result = await utils.redis_smembers("tags")
        
        assert result == ["python", "redis"]
        mock_redis.smembers.assert_called_with("tags")

    @patch('nexios_contrib.redis.utils.get_redis_client')
    async def test_redis_srem(self, mock_get_client, mock_redis):
        """Test redis_srem utility function."""
        mock_get_client.return_value = mock_redis
        mock_redis.srem.return_value = 1
        
        result = await utils.redis_srem("tags", "python")
        
        assert result == 1
        mock_redis.srem.assert_called_with("tags", "python")

    @patch('nexios_contrib.redis.utils.get_redis_client')
    async def test_redis_scard(self, mock_get_client, mock_redis):
        """Test redis_scard utility function."""
        mock_get_client.return_value = mock_redis
        mock_redis.scard.return_value = 3
        
        result = await utils.redis_scard("tags")
        
        assert result == 3
        mock_redis.scard.assert_called_with("tags")

    @patch('nexios_contrib.redis.utils.get_redis_client')
    async def test_redis_keys(self, mock_get_client, mock_redis):
        """Test redis_keys utility function."""
        mock_get_client.return_value = mock_redis
        mock_redis.keys.return_value = ["user:123", "user:456"]
        
        result = await utils.redis_keys("user:*")
        
        assert result == ["user:123", "user:456"]
        mock_redis.keys.assert_called_with("user:*")

    @patch('nexios_contrib.redis.utils.get_redis_client')
    async def test_redis_flushdb(self, mock_get_client, mock_redis):
        """Test redis_flushdb utility function."""
        mock_get_client.return_value = mock_redis
        mock_redis.flushdb.return_value = True
        
        result = await utils.redis_flushdb(asynchronous=True)
        
        assert result is True
        mock_redis.flushdb.assert_called_with(True)

    @patch('nexios_contrib.redis.utils.get_redis_client')
    async def test_redis_execute(self, mock_get_client, mock_redis):
        """Test redis_execute utility function."""
        mock_get_client.return_value = mock_redis
        mock_redis.execute.return_value = "PONG"
        
        result = await utils.redis_execute("PING")
        
        assert result == "PONG"
        mock_redis.execute.assert_called_with("PING")