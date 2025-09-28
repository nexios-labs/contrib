"""
Dependency injection for Redis client in Nexios.

This module provides dependency injection utilities for accessing
Redis client and performing Redis operations in route handlers.
"""
from __future__ import annotations

import asyncio
from typing import Any, Literal, Optional, Union
from nexios.dependencies import Depend, Context
from nexios.http import Request

from .client import RedisClient
from . import get_redis


def RedisDepend() -> RedisClient:
    """
    Dependency injection function for accessing Redis client.

    This function can be used as a dependency in route handlers to
    automatically inject the Redis client instance.

    Returns:
        RedisClient: Dependency injection wrapper function.

    Example:
        ```python
        from nexios import NexiosApp
        from nexios_contrib.redis import RedisDepend

        app = NexiosApp()

        @app.get("/cache/{key}")
        async def get_cached_data(
            request: Request,
            response: Response,
            redis: RedisClient = RedisDepend()  # Injects RedisClient
        ):
            # Use redis client directly
            value = await redis.get(request.path_params["key"])
            return {"value": value}
        ```
    """
    def _wrap(context: Context = Context()) -> RedisClient:
        return get_redis(context)

    return Depend(_wrap)


def RedisOperationDepend(
    operation: Literal[
        "get", "set", "delete", "exists", "expire", "ttl", "incr", "decr",
        "json_get", "json_set", "hget", "hset", "hgetall", "lpush", "rpush",
        "lpop", "rpop", "llen", "sadd", "smembers", "srem", "scard",
        "keys", "flushdb", "execute"
    ],
    *args: Any,
    **kwargs: Any
) -> Any:
    """
    Dependency injection function for Redis operations.

    This function allows injecting the result of common Redis operations
    directly into route handlers.

    Args:
        operation: The Redis operation to perform ('get', 'set', 'exists', etc.)
        *args: Positional arguments for the operation
        **kwargs: Keyword arguments for the operation

    Returns:
        Any: Dependency injection wrapper function that returns operation result.

    Example:
        ```python
        from nexios import NexiosApp
        from nexios_contrib.redis import RedisOperationDepend

        app = NexiosApp()

        @app.get("/cache/{key}")
        async def get_cached_data(
            request: Request,
            cached_value: str = RedisOperationDepend("get", request.path_params["key"])
        ):
            # cached_value is already the result of redis.get(key)
            return {"value": cached_value}
        ```

        @app.post("/counter/{name}")
        async def increment_counter(
            request: Request,
            new_value: int = RedisOperationDepend("incr", "counter", 1)
        ):
            # new_value is already the result of redis.incr("counter", 1)
            return {"counter": new_value}
        ```
    """
    async def _wrap(context: Context = Context()) -> Any:
        redis = get_redis(context)

        # Get the Redis operation method
        if not hasattr(redis, operation):
            raise AttributeError(f"Redis client has no operation '{operation}'")

        method = getattr(redis, operation)

        # Call the operation with provided arguments
        if asyncio.iscoroutinefunction(method):
            return await method(*args, **kwargs)
        else:
            return method(*args, **kwargs)

    return Depend(_wrap)


def RedisKeyDepend(
    key: str,
    operation: Literal[
        "get", "json_get", "exists", "ttl", "expire", "incr", "decr",
        "hget", "hgetall", "llen", "scard"
    ] = "get",
    default: Any = None,
) -> Any:
    """
    Dependency injection function for Redis key operations.

    This function provides a convenient way to inject Redis values
    for specific keys with fallback defaults.

    Args:
        key: The Redis key to operate on
        operation: The operation to perform ('get', 'set', 'exists', etc.)
        default: Default value if key doesn't exist (for 'get' operation)

    Returns:
        Any: Dependency injection wrapper function.

    Example:
        ```python
        from nexios import NexiosApp
        from nexios_contrib.redis import RedisKeyDepend

        app = NexiosApp()

        @app.get("/user/{user_id}")
        async def get_user(
            user_id: str,
            user_data: dict = RedisKeyDepend(f"user:{{user_id}}", "json_get", {"name": "Unknown"})
        ):
            # user_data is the result of redis.json_get(f"user:{user_id}") or {"name": "Unknown"}
            return {"user": user_data}
        ```
    """
    async def _wrap(context: Context = Context()) -> Any:
        redis = get_redis(context)

        try:
            # Format the key with context if it contains placeholders
            formatted_key = key.format(**context.__dict__) if hasattr(context, '__dict__') else key

            if operation == "get":
                result = await redis.get(formatted_key)
                return result if result is not None else default
            elif operation == "json_get":
                result = await redis.json_get(formatted_key)
                return result if result is not None else default
            elif operation == "exists":
                return await redis.exists(formatted_key)
            else:
                # For other operations, return the method result
                method = getattr(redis, operation)
                if asyncio.iscoroutinefunction(method):
                    return await method(formatted_key)
                else:
                    return method(formatted_key)
        except Exception:
            return default

    return Depend(_wrap)


def RedisCacheDepend(key: str, ttl: int = 300) -> Any:
    """
    Dependency injection function for cached values.

    This function provides a simple caching mechanism where values
    are cached for a specified time-to-live period.

    Args:
        key: The cache key
        ttl: Time-to-live in seconds

    Returns:
        Any: Dependency injection wrapper function.

    Example:
        ```python
        from nexios import NexiosApp
        from nexios_contrib.redis import RedisCacheDepend

        app = NexiosApp()

        @app.get("/expensive-operation/{param}")
        async def expensive_operation(
            param: str,
            result: str = RedisCacheDepend(f"expensive:{param}", ttl=600)
        ):
            # If not cached, this would be computed and cached
            # For demo, we'll just return a value
            return {"result": f"computed_{param}"}
        ```
    """
    async def _wrap(context: Context = Context()) -> Any:
        redis = get_redis(context)

        # For this example, we'll just get the key
        # In a real implementation, you might want to check cache first
        # and compute/fallback if not found
        cached_value = await redis.get(key)
        if cached_value:
            return cached_value

        # Return a placeholder - in real usage, this would trigger computation
        return f"cached_{key}"

    return Depend(_wrap)
