"""
Redis configuration for Nexios Redis integration.
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, validator


class RedisConfig(BaseModel):
    """
    Configuration for Redis client.

    This model defines all the configuration options for connecting to Redis
    and provides validation and sensible defaults.
    """

    url: str = Field(
        default="redis://localhost:6379",
        description="Redis connection URL"
    )
    db: int = Field(
        default=0,
        ge=0,
        le=15,
        description="Redis database number (0-15)"
    )
    password: Optional[str] = Field(
        default=None,
        description="Redis password"
    )
    decode_responses: bool = Field(
        default=True,
        description="Whether to decode responses as strings"
    )
    encoding: str = Field(
        default="utf-8",
        description="Encoding for string operations"
    )
    encoding_errors: str = Field(
        default="strict",
        description="Error handling for encoding"
    )
    socket_timeout: Optional[float] = Field(
        default=None,
        description="Socket timeout in seconds"
    )
    socket_connect_timeout: Optional[float] = Field(
        default=None,
        description="Socket connect timeout in seconds"
    )
    socket_keepalive: bool = Field(
        default=False,
        description="Enable TCP keepalive"
    )
    socket_keepalive_options: Optional[Dict[int, int]] = Field(
        default=None,
        description="TCP keepalive options"
    )
    health_check_interval: int = Field(
        default=30,
        description="Health check interval in seconds"
    )
    max_connections: Optional[int] = Field(
        default=None,
        description="Maximum connection pool size"
    )
    retry_on_timeout: bool = Field(
        default=False,
        description="Retry on timeout"
    )

    @validator("url")
    def validate_url(cls, v: str) -> str:
        """Validate Redis URL format."""
        if not v.startswith(("redis://", "rediss://", "unix://")):
            raise ValueError("URL must start with redis://, rediss://, or unix://")
        return v

    @classmethod
    def from_env(cls, prefix: str = "REDIS_") -> RedisConfig:
        """
        Create RedisConfig from environment variables.

        Args:
            prefix: Prefix for environment variables (default: "REDIS_")

        Returns:
            RedisConfig instance with values from environment

        Example:
            ```python
            # With environment variables:
            # REDIS_URL=redis://localhost:6379/1
            # REDIS_PASSWORD=mypassword
            # REDIS_DB=1
            # REDIS_DECODE_RESPONSES=true

            config = RedisConfig.from_env()
            ```
        """
        env_vars = {}
        for field_name, field in cls.__fields__.items():
            env_name = f"{prefix}{field_name.upper()}"
            env_value = os.getenv(env_name)

            if env_value is not None:
                # Type conversion for specific fields
                if field.type_ in (int, float):
                    try:
                        if field.type_ == int:
                            env_vars[field_name] = int(env_value)
                        else:
                            env_vars[field_name] = float(env_value)
                    except ValueError:
                        continue  # Skip invalid values
                elif field.type_ == bool:
                    env_vars[field_name] = env_value.lower() in ("true", "1", "yes", "on")
                else:
                    env_vars[field_name] = env_value

        return cls(**env_vars)

    def to_connection_kwargs(self) -> Dict[str, Any]:
        """
        Convert configuration to Redis connection kwargs.

        Returns:
            Dictionary of kwargs to pass to Redis client
        """
        kwargs = self.dict(exclude={"url"})

        # Handle URL parsing for host, port, etc.
        if self.url.startswith(("redis://", "rediss://")):
            # Parse URL to extract host, port, db, password
            from urllib.parse import urlparse

            parsed = urlparse(self.url)
            if parsed.hostname:
                kwargs["host"] = parsed.hostname
            if parsed.port:
                kwargs["port"] = parsed.port
            if parsed.password:
                kwargs["password"] = parsed.password

            # Extract db from path if present
            path_parts = parsed.path.strip("/").split("/")
            if path_parts and path_parts[0].isdigit():
                kwargs["db"] = int(path_parts[0])

        return kwargs

    def __str__(self) -> str:
        """String representation of Redis config (without sensitive data)."""
        safe_dict = self.dict()
        if self.password:
            safe_dict["password"] = "***"
        return f"RedisConfig({safe_dict})"
