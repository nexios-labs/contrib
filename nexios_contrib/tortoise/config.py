"""
Tortoise ORM configuration for Nexios Tortoise integration.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class TortoiseConfig(BaseModel):
    """
    Configuration for Tortoise ORM client.

    This model defines all the configuration options for connecting to databases
    via Tortoise ORM and provides validation and sensible defaults.
    """

    db_url: str = Field(
        description="Database connection URL"
    )
    modules: Dict[str, List[str]] = Field(
        default_factory=lambda: {"models": []},
        description="Dictionary mapping app names to model module paths"
    )
    generate_schemas: bool = Field(
        default=False,
        description="Whether to generate database schemas on startup"
    )
    use_tz: bool = Field(
        default=False,
        description="Whether to use timezone-aware datetime objects"
    )
    timezone: str = Field(
        default="UTC",
        description="Default timezone for datetime objects"
    )
    connections: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Custom connection configurations"
    )
    apps: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Custom app configurations"
    )

    @validator("db_url")
    def validate_db_url(cls, v: str) -> str:
        """Validate database URL format."""
        supported_schemes = [
            "sqlite://", "postgres://", "postgresql://", 
            "mysql://", "asyncpg://", "aiomysql://"
        ]
        if not any(v.startswith(scheme) for scheme in supported_schemes):
            raise ValueError(
                f"Database URL must start with one of: {', '.join(supported_schemes)}"
            )
        return v

    @validator("modules")
    def validate_modules(cls, v: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Validate modules configuration."""
        if not isinstance(v, dict):
            raise ValueError("modules must be a dictionary")
        
        for app_name, module_list in v.items():
            if not isinstance(module_list, list):
                raise ValueError(f"modules['{app_name}'] must be a list of strings")
            
            for module in module_list:
                if not isinstance(module, str):
                    raise ValueError(f"All modules in modules['{app_name}'] must be strings")
        
        return v

    @classmethod
    def from_env(cls, prefix: str = "TORTOISE_") -> TortoiseConfig:
        """
        Create TortoiseConfig from environment variables.

        Args:
            prefix: Prefix for environment variables (default: "TORTOISE_")

        Returns:
            TortoiseConfig instance with values from environment

        Example:
            ```python
            # With environment variables:
            # TORTOISE_DB_URL=sqlite://db.sqlite3
            # TORTOISE_GENERATE_SCHEMAS=true
            # TORTOISE_USE_TZ=true

            config = TortoiseConfig.from_env()
            ```
        """
        env_vars = {}
        
        # Handle simple fields
        for field_name, field in cls.__fields__.items():
            if field_name in ["modules", "connections", "apps"]:
                continue  # Skip complex fields
                
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

        # Handle modules from environment (JSON format expected)
        modules_env = os.getenv(f"{prefix}MODULES")
        if modules_env:
            try:
                import json
                env_vars["modules"] = json.loads(modules_env)
            except (json.JSONDecodeError, ValueError):
                pass  # Skip invalid JSON

        return cls(**env_vars)

    def to_tortoise_config(self) -> Dict[str, Any]:
        """
        Convert configuration to Tortoise.init() kwargs.

        Returns:
            Dictionary of kwargs to pass to Tortoise.init()
        """
        config = {
            "db_url": self.db_url,
            "modules": self.modules,
            "use_tz": self.use_tz,
            "timezone": self.timezone,
        }

        if self.connections:
            config["connections"] = self.connections
        
        if self.apps:
            config["apps"] = self.apps

        return config

    def __str__(self) -> str:
        """String representation of Tortoise config (without sensitive data)."""
        safe_dict = self.dict()
        # Mask password in db_url if present
        if "://" in self.db_url and "@" in self.db_url:
            parts = self.db_url.split("://")
            if len(parts) == 2:
                scheme = parts[0]
                rest = parts[1]
                if "@" in rest:
                    auth_part, host_part = rest.split("@", 1)
                    if ":" in auth_part:
                        user, _ = auth_part.split(":", 1)
                        safe_dict["db_url"] = f"{scheme}://{user}:***@{host_part}"
        
        return f"TortoiseConfig({safe_dict})"