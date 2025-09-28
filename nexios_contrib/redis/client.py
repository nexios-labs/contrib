"""
Redis client wrapper for Nexios integration.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Optional, Union

from nexios_contrib.redis.config import RedisConfig


class RedisOperationError(Exception):
    """Raised when there's an error performing a Redis operation."""
    pass


class RedisClient:
    """
    Redis client wrapper with connection management and utility methods.

    This class provides a high-level interface for Redis operations with
    proper connection lifecycle management for Nexios applications.
    """

    def __init__(self, config: RedisConfig):
        """
        Initialize Redis client.

        Args:
            config: Redis configuration object
        """
        self.config = config
        self._redis = None
        self._connection_lock = asyncio.Lock()
        self._connected = False

    async def connect(self) -> None:
        """Establish connection to Redis."""
        async with self._connection_lock:
            if self._connected:
                return

            try:
                import redis.asyncio as redis

                connection_kwargs = self.config.to_connection_kwargs()

                # Create Redis client
                self._redis = redis.Redis(**connection_kwargs)

                # Test connection
                await self._redis.ping()

                self._connected = True

            except ImportError:
                raise ImportError(
                    "redis package is required for Redis integration. "
                    "Install it with: pip install redis"
                )
            except Exception as e:
                raise ConnectionError(f"Failed to connect to Redis: {e}")

    async def close(self) -> None:
        """Close Redis connection."""
        async with self._connection_lock:
            if self._redis and self._connected:
                await self._redis.close()
                self._connected = False
                self._redis = None

    async def ping(self) -> bool:
        """Test Redis connection."""
        if not self._connected:
            await self.connect()

        try:
            return await self._redis.ping()
        except Exception as e:
            self._connected = False
            raise e

    async def get(self, key: str) -> Optional[str]:
        """Get value by key."""
        if not self._connected:
            await self.connect()

        try:
            return await self._redis.get(key)
        except Exception as e:
            raise RedisOperationError(f"Failed to get key '{key}': {e}")

    async def set(
        self,
        key: str,
        value: Union[str, int, float],
        ex: Optional[int] = None,
        px: Optional[int] = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """
        Set value with optional expiration.

        Args:
            key: Redis key
            value: Value to set
            ex: Expire time in seconds
            px: Expire time in milliseconds
            nx: Only set if key does not exist
            xx: Only set if key exists

        Returns:
            True if successful
        """
        if not self._connected:
            await self.connect()

        try:
            return await self._redis.set(key, value, ex=ex, px=px, nx=nx, xx=xx)
        except Exception as e:
            raise RedisOperationError(f"Failed to set key '{key}': {e}")

    async def delete(self, *keys: str) -> int:
        """Delete one or more keys."""
        if not self._connected:
            await self.connect()

        try:
            return await self._redis.delete(*keys)
        except Exception as e:
            raise RedisOperationError(f"Failed to delete keys: {e}")

    async def exists(self, *keys: str) -> int:
        """Check if keys exist."""
        if not self._connected:
            await self.connect()

        try:
            return await self._redis.exists(*keys)
        except Exception as e:
            raise RedisOperationError(f"Failed to check key existence: {e}")

    async def expire(self, key: str, seconds: int, nx: bool = False, xx: bool = False, gt: bool = False, lt: bool = False) -> bool:
        """Set expiration on key."""
        if not self._connected:
            await self.connect()

        try:
            return await self._redis.expire(key, seconds, nx=nx, xx=xx, gt=gt, lt=lt)
        except Exception as e:
            raise RedisOperationError(f"Failed to set expiration for key '{key}': {e}")

    async def ttl(self, key: str) -> int:
        """Get time to live for key."""
        if not self._connected:
            await self.connect()

        try:
            return await self._redis.ttl(key)
        except Exception as e:
            raise RedisOperationError(f"Failed to get TTL for key '{key}': {e}")

    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment key value."""
        if not self._connected:
            await self.connect()

        try:
            return await self._redis.incr(key, amount)
        except Exception as e:
            raise RedisOperationError(f"Failed to increment key '{key}': {e}")

    async def decr(self, key: str, amount: int = 1) -> int:
        """Decrement key value."""
        if not self._connected:
            await self.connect()

        try:
            return await self._redis.decr(key, amount)
        except Exception as e:
            raise RedisOperationError(f"Failed to decrement key '{key}': {e}")

    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern."""
        if not self._connected:
            await self.connect()

        try:
            return await self._redis.keys(pattern)
        except Exception as e:
            raise RedisOperationError(f"Failed to get keys with pattern '{pattern}': {e}")

    async def flushdb(self, asynchronous: bool = False) -> bool:
        """Flush current database."""
        if not self._connected:
            await self.connect()

        try:
            await self._redis.flushdb(asynchronous=asynchronous)
            return True
        except Exception as e:
            raise RedisOperationError(f"Failed to flush database: {e}")

    async def json_get(self, key: str, path: str = ".") -> Any:
        """
        Get JSON value from Redis.

        Requires redis-py with JSON support.
        """
        if not self._connected:
            await self.connect()

        try:
            import redis.asyncio as redis
            if hasattr(redis.Redis, "json"):
                return await self._redis.json().get(key, path)
            else:
                # Fallback to regular get and JSON parsing
                value = await self._redis.get(key)
                return json.loads(value) if value else None
        except Exception as e:
            raise RedisOperationError(f"Failed to get JSON from key '{key}': {e}")

    async def json_set(self, key: str, path: str, value: Any, nx: bool = False, xx: bool = False) -> bool:
        """
        Set JSON value in Redis.

        Requires redis-py with JSON support.
        """
        if not self._connected:
            await self.connect()

        try:
            import redis.asyncio as redis
            if hasattr(redis.Redis, "json"):
                await self._redis.json().set(key, path, value, nx=nx, xx=xx)
                return True
            else:
                # Fallback to JSON serialization and regular set
                json_value = json.dumps(value)
                return await self._redis.set(key, json_value, nx=nx, xx=xx)
        except Exception as e:
            raise RedisOperationError(f"Failed to set JSON for key '{key}': {e}")

    async def hget(self, key: str, field: str) -> Optional[str]:
        """Get hash field value."""
        if not self._connected:
            await self.connect()

        try:
            return await self._redis.hget(key, field)
        except Exception as e:
            raise RedisOperationError(f"Failed to get hash field '{field}' from key '{key}': {e}")

    async def hset(self, key: str, field: str, value: Union[str, int, float]) -> int:
        """Set hash field value."""
        if not self._connected:
            await self.connect()

        try:
            return await self._redis.hset(key, field, value)
        except Exception as e:
            raise RedisOperationError(f"Failed to set hash field '{field}' in key '{key}': {e}")

    async def hgetall(self, key: str) -> Dict[str, str]:
        """Get all hash fields and values."""
        if not self._connected:
            await self.connect()

        try:
            return await self._redis.hgetall(key)
        except Exception as e:
            raise RedisOperationError(f"Failed to get all hash fields from key '{key}': {e}")

    async def lpush(self, key: str, *values: Union[str, int, float]) -> int:
        """Push values to list (left side)."""
        if not self._connected:
            await self.connect()

        try:
            return await self._redis.lpush(key, *values)
        except Exception as e:
            raise RedisOperationError(f"Failed to push values to list '{key}': {e}")

    async def rpush(self, key: str, *values: Union[str, int, float]) -> int:
        """Push values to list (right side)."""
        if not self._connected:
            await self.connect()

        try:
            return await self._redis.rpush(key, *values)
        except Exception as e:
            raise RedisOperationError(f"Failed to push values to list '{key}': {e}")

    async def lpop(self, key: str, count: Optional[int] = None) -> Union[Optional[str], List[str]]:
        """Pop value(s) from list (left side)."""
        if not self._connected:
            await self.connect()

        try:
            return await self._redis.lpop(key, count)
        except Exception as e:
            raise RedisOperationError(f"Failed to pop from list '{key}': {e}")

    async def rpop(self, key: str, count: Optional[int] = None) -> Union[Optional[str], List[str]]:
        """Pop value(s) from list (right side)."""
        if not self._connected:
            await self.connect()

        try:
            return await self._redis.rpop(key, count)
        except Exception as e:
            raise RedisOperationError(f"Failed to pop from list '{key}': {e}")

    async def llen(self, key: str) -> int:
        """Get list length."""
        if not self._connected:
            await self.connect()

        try:
            return await self._redis.llen(key)
        except Exception as e:
            raise RedisOperationError(f"Failed to get length of list '{key}': {e}")

    async def sadd(self, key: str, *members: Union[str, int, float]) -> int:
        """Add members to set."""
        if not self._connected:
            await self.connect()

        try:
            return await self._redis.sadd(key, *members)
        except Exception as e:
            raise RedisOperationError(f"Failed to add members to set '{key}': {e}")

    async def smembers(self, key: str) -> List[str]:
        """Get all set members."""
        if not self._connected:
            await self.connect()

        try:
            return await self._redis.smembers(key)
        except Exception as e:
            raise RedisOperationError(f"Failed to get members of set '{key}': {e}")

    async def srem(self, key: str, *members: Union[str, int, float]) -> int:
        """Remove members from set."""
        if not self._connected:
            await self.connect()

        try:
            return await self._redis.srem(key, *members)
        except Exception as e:
            raise RedisOperationError(f"Failed to remove members from set '{key}': {e}")

    async def scard(self, key: str) -> int:
        """Get set cardinality (size)."""
        if not self._connected:
            await self.connect()

        try:
            return await self._redis.scard(key)
        except Exception as e:
            raise RedisOperationError(f"Failed to get size of set '{key}': {e}")

    async def execute(self, *args: Any) -> Any:
        """
        Execute raw Redis command.

        Args:
            *args: Redis command and arguments

        Returns:
            Command result
        """
        if not self._connected:
            await self.connect()

        try:
            return await self._redis.execute_command(*args)
        except Exception as e:
            raise RedisOperationError(f"Failed to execute Redis command: {e}")

    def __repr__(self) -> str:
        """String representation of RedisClient."""
        connected = "connected" if self._connected else "disconnected"
        return f"RedisClient({connected}, config={self.config})"
