"""
Redis client wrapper for Nexios integration.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any
import redis
from nexios_contrib.redis.config import RedisConfig

# Check for async redis availability at module load time
try:
    import redis.asyncio as async_redis
    _REDIS_AVAILABLE = True
except ImportError:
    async_redis = None
    _REDIS_AVAILABLE = False


class RedisOperationError(Exception):
    """Raised when there's an error performing a Redis operation."""
    pass


class RedisClient(async_redis.Redis):
    """
    Redis client that inherits from redis.asyncio.Redis, giving access to
    ALL Redis commands (get, set, delete, hgetall, etc.) without manual wrapping.

    Adds connection lifecycle management (connect/close) and custom helper methods.
    """

    def __init__(self, config: RedisConfig):
        """
        Initialize Redis client.

        Args:
            config: Redis configuration object
        """
        self.config = config
        self._connection_lock = asyncio.Lock()
        self._connected = False

        if not _REDIS_AVAILABLE:
            raise ImportError(
                "redis package is required for Redis integration. "
                "Install it with: pip install redis"
            )

        # Build connection kwargs from config and initialize the parent Redis client
        connection_kwargs = config.to_connection_kwargs()
        super().__init__(**connection_kwargs)

    async def connect(self) -> None:
        """Establish connection to Redis."""
        async with self._connection_lock:
            if self._connected:
                return

            try:
                await self.ping()
                self._connected = True
            except Exception as e:
                raise ConnectionError(f"Failed to connect to Redis: {e}")

    async def close(self) -> None:
        """Close Redis connection."""
        async with self._connection_lock:
            if self._connected:
                await super().close()
                self._connected = False

    async def json_get(self, key: str, path: str = ".") -> Any:
        """
        Get JSON value from Redis.

        Requires redis-py with JSON support.
        """
        if not self._connected:
            await self.connect()

        try:
            if hasattr(async_redis.Redis, "json"):
                return await self.json().get(key, path)
            else:
                # Fallback to regular get and JSON parsing
                value = await self.get(key)
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
            if hasattr(async_redis.Redis, "json"):
                await self.json().set(key, path, value, nx=nx, xx=xx)
                return True
            else:
                # Fallback to JSON serialization and regular set
                json_value = json.dumps(value)
                return await self.set(key, json_value, nx=nx, xx=xx)
        except Exception as e:
            raise RedisOperationError(f"Failed to set JSON for key '{key}': {e}")

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
            return await self.execute_command(*args)
        except Exception as e:
            raise RedisOperationError(f"Failed to execute Redis command: {e}")

    def __repr__(self) -> str:
        """String representation of RedisClient."""
        connected = "connected" if self._connected else "disconnected"
        return f"RedisClient({connected}, config={self.config})"
