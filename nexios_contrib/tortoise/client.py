"""
Tortoise ORM client wrapper for Nexios integration.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .config import TortoiseConfig

logger = logging.getLogger("nexios.tortoise")


class TortoiseConnectionError(Exception):
    """Raised when there's an error connecting to the database."""
    pass


class TortoiseClient:
    """
    Tortoise ORM client wrapper with connection management.

    This class provides a high-level interface for Tortoise ORM operations with
    proper connection lifecycle management for Nexios applications.
    """

    def __init__(self, config: TortoiseConfig):
        """
        Initialize Tortoise ORM client.

        Args:
            config: Tortoise configuration object
        """
        self.config = config
        self._initialized = False

    async def init(self) -> None:
        """Initialize Tortoise ORM."""
        if self._initialized:
            return

        try:
            from tortoise import Tortoise

            # Convert config to Tortoise.init() kwargs
            tortoise_config = self.config.to_tortoise_config()
            
            await Tortoise.init(**tortoise_config)

            # Generate schemas if requested
            if self.config.generate_schemas:
                await Tortoise.generate_schemas()
                logger.info("Database schemas generated successfully")

            self._initialized = True
            logger.info("Tortoise ORM initialized successfully")

        except ImportError:
            raise ImportError(
                "tortoise-orm package is required for Tortoise integration. "
                "Install it with: pip install tortoise-orm"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Tortoise ORM: {e}")
            raise TortoiseConnectionError(f"Failed to initialize Tortoise ORM: {e}")

    async def close(self) -> None:
        """Close Tortoise ORM connections."""
        if not self._initialized:
            return

        try:
            from tortoise import Tortoise

            await Tortoise.close_connections()
            self._initialized = False
            logger.info("Tortoise ORM connections closed successfully")

        except Exception as e:
            logger.error(f"Error closing Tortoise ORM connections: {e}")
            raise e

    async def generate_schemas(self, safe: bool = True) -> None:
        """
        Generate database schemas.

        Args:
            safe: If True, won't drop existing tables
        """
        if not self._initialized:
            await self.init()

        try:
            from tortoise import Tortoise

            await Tortoise.generate_schemas(safe=safe)
            logger.info("Database schemas generated successfully")

        except Exception as e:
            logger.error(f"Failed to generate schemas: {e}")
            raise e

    async def get_connection(self, connection_name: str = "default") -> Any:
        """
        Get a database connection.

        Args:
            connection_name: Name of the connection to retrieve

        Returns:
            Database connection object
        """
        if not self._initialized:
            await self.init()

        try:
            from tortoise import Tortoise

            return Tortoise.get_connection(connection_name)

        except Exception as e:
            logger.error(f"Failed to get connection '{connection_name}': {e}")
            raise e

    async def execute_query(self, query: str, *args: Any) -> List[Dict[str, Any]]:
        """
        Execute a raw SQL query.

        Args:
            query: SQL query string
            *args: Query parameters

        Returns:
            List of result dictionaries
        """
        if not self._initialized:
            await self.init()

        try:
            from tortoise import Tortoise

            connection = Tortoise.get_connection("default")
            return await connection.execute_query(query, args)

        except Exception as e:
            logger.error(f"Failed to execute query: {e}")
            raise e

    async def execute_script(self, script: str) -> None:
        """
        Execute a SQL script.

        Args:
            script: SQL script string
        """
        if not self._initialized:
            await self.init()

        try:
            from tortoise import Tortoise

            connection = Tortoise.get_connection("default")
            await connection.execute_script(script)

        except Exception as e:
            logger.error(f"Failed to execute script: {e}")
            raise e

    def is_initialized(self) -> bool:
        """Check if Tortoise ORM is initialized."""
        return self._initialized

    def get_models(self) -> Dict[str, Any]:
        """
        Get all registered models.

        Returns:
            Dictionary of model names to model classes
        """
        if not self._initialized:
            raise TortoiseConnectionError("Tortoise ORM not initialized")

        try:
            from tortoise import Tortoise

            return Tortoise.apps

        except Exception as e:
            logger.error(f"Failed to get models: {e}")
            raise e

    def __repr__(self) -> str:
        """String representation of TortoiseClient."""
        status = "initialized" if self._initialized else "not initialized"
        return f"TortoiseClient({status}, config={self.config})"