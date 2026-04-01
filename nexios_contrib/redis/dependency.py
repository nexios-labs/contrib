"""
Dependency injection for Redis client in Nexios.

This module provides dependency injection utilities for accessing
Redis client and performing Redis operations in route handlers.
"""

from __future__ import annotations

from nexios.dependencies import Depend, Context

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

    return Depend(get_redis)
