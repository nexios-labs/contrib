"""
Nexios-Redis - Redis integration for Nexios web framework.

This module provides Redis client initialization, dependency injection,
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING

from nexios import NexiosApp, Depend
from nexios.http import Request, Response

from .client import RedisClient, RedisOperationError
from .config import RedisConfig



if TYPE_CHECKING:
    from nexios.dependencies import Context

__version__ = "0.1.0"
# __all__ = [
#     "RedisConfig",
#     "RedisClient",
#     "RedisConnectionError",
#     "init_redis",
#     "get_redis",
#     "get_redis_client",
#     "redis_get",
#     "redis_set",
#     "redis_delete",
#     "redis_exists",
#     "redis_expire",
#     "redis_ttl",
#     "redis_incr",
#     "redis_decr",
#     "redis_json_get",
#     "redis_json_set",
#     "RedisDepend",
#     "RedisOperationDepend",
#     "RedisKeyDepend",
#     "RedisCacheDepend",
# ]

# Global Redis client instance
_redis_client: Optional[RedisClient] = None

logger = logging.getLogger("nexios.redis")


class RedisConnectionError(Exception):
    """Raised when there's an error connecting to Redis."""
    pass


def init_redis(
    app: NexiosApp,
    url: str = "redis://localhost:6379",
    db: int = 0,
    password: Optional[str] = None,
    decode_responses: bool = True,
    **kwargs: Any,
) -> None:
    """
    Initialize Redis client for use in a Nexios application.

    This function sets up the Redis client and registers it with the Nexios app
    for dependency injection. It also adds startup and shutdown handlers to
    manage the Redis connection lifecycle.

    Args:
        app: The Nexios application instance.
        url: Redis connection URL.
        db: Redis database number.
        password: Redis password (if required).
        decode_responses: Whether to decode responses as strings.
        **kwargs: Additional arguments to pass to Redis client.

    Example:
        ```python
        from nexios import NexiosApp
        from nexios_contrib.redis import init_redis

        app = NexiosApp()

        # Initialize Redis with default settings
        init_redis(app)

        # Or with custom settings
        init_redis(
            app,
            url="redis://localhost:6379/1",
            password="mysecret",
            decode_responses=True
        )
        ```
    """
    global _redis_client

    config = RedisConfig(
        url=url,
        db=db,
        password=password,
        decode_responses=decode_responses,
        **kwargs
    )

    _redis_client = RedisClient(config)

    # Store Redis client in app state for easy access
    app.state["redis"] = _redis_client

    # Add startup handler
    async def _init_redis() -> None:
        """Initialize Redis connection on startup."""
        try:
            await _redis_client.connect()
            logger.info("Redis client connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise RedisConnectionError(f"Failed to connect to Redis: {e}")

    # Add shutdown handler
    async def _close_redis() -> None:
        """Close Redis connection on shutdown."""
        try:
            await _redis_client.close()
            logger.info("Redis client disconnected successfully")
        except Exception as e:
            logger.error(f"Error disconnecting from Redis: {e}")

    app.on_startup(_init_redis)
    app.on_shutdown(_close_redis)


def get_redis(context: Optional["Context"] = None) -> RedisClient:
    """
    Get the Redis client instance from the current context.

    This is a dependency function that can be used with Nexios's dependency
    injection system to get the Redis client in route handlers.

    Args:
        context: The Nexios context (automatically injected by DI system)

    Returns:
        The Redis client instance.

    Raises:
        RedisConnectionError: If Redis client is not initialized.

    Example:
        ```python
        from nexios import NexiosApp, Depend
        from nexios_contrib.redis import get_redis

        app = NexiosApp()

        @app.get("/cache/{key}")
        async def get_cached_data(
            request: Request,
            response: Response,
            redis: Depend(get_redis)  # Type: RedisClient
        ):
            # Use redis client
            value = await redis.get(request.path_params["key"])
            return {"value": value}
        ```
    """
    global _redis_client
    if _redis_client is None:
        raise RedisConnectionError("Redis client not initialized. Call init_redis() first.")
    return _redis_client


# Backward compatibility alias
get_redis_client = get_redis
