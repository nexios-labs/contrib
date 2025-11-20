"""
Nexios-Tortoise - Tortoise ORM integration for Nexios web framework.

This module provides Tortoise ORM initialization, connection management,
and exception handling for Nexios applications.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from nexios import NexiosApp

from .client import TortoiseClient, TortoiseConnectionError
from .config import TortoiseConfig
from .exceptions import handle_tortoise_exceptions


__version__ = "0.1.0"

# Global Tortoise client instance
_tortoise_client: Optional[TortoiseClient] = None

logger = logging.getLogger("nexios.tortoise")


class TortoiseConnectionError(Exception):
    """Raised when there's an error connecting to the database."""
    pass


def init_tortoise(
    app: NexiosApp,
    db_url: str,
    modules: Optional[Dict[str, List[str]]] = None,
    generate_schemas: bool = False,
    add_exception_handlers: bool = True,
    **kwargs: Any,
) -> None:
    """
    Initialize Tortoise ORM for use in a Nexios application.

    This function sets up the Tortoise ORM client and registers it with the Nexios app
    for dependency injection. It also adds startup and shutdown handlers to
    manage the database connection lifecycle.

    Args:
        app: The Nexios application instance.
        db_url: Database connection URL (e.g., "sqlite://db.sqlite3").
        modules: Dictionary mapping app names to model module paths.
        generate_schemas: Whether to generate database schemas on startup.
        add_exception_handlers: Whether to add Tortoise exception handlers.
        **kwargs: Additional arguments to pass to Tortoise.init().

    Example:
        ```python
        from nexios import NexiosApp
        from nexios_contrib.tortoise import init_tortoise

        app = NexiosApp()

        # Initialize Tortoise with SQLite
        init_tortoise(
            app,
            db_url="sqlite://db.sqlite3",
            modules={"models": ["app.models"]},
            generate_schemas=True
        )

        # Or with PostgreSQL
        init_tortoise(
            app,
            db_url="postgres://user:password@localhost:5432/mydb",
            modules={"models": ["app.models", "app.user_models"]},
            generate_schemas=False
        )
        ```
    """
    global _tortoise_client

    config = TortoiseConfig(
        db_url=db_url,
        modules=modules or {"models": []},
        generate_schemas=generate_schemas,
        **kwargs
    )

    _tortoise_client = TortoiseClient(config)

    # Store Tortoise client in app state for easy access
    app.state["tortoise"] = _tortoise_client

    # Add startup handler
    async def _init_tortoise() -> None:
        """Initialize Tortoise ORM connection on startup."""
        try:
            await _tortoise_client.init()
            logger.info("Tortoise ORM initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Tortoise ORM: {e}")
            raise TortoiseConnectionError(f"Failed to initialize Tortoise ORM: {e}")

    # Add shutdown handler
    async def _close_tortoise() -> None:
        """Close Tortoise ORM connections on shutdown."""
        try:
            await _tortoise_client.close()
            logger.info("Tortoise ORM connections closed successfully")
        except Exception as e:
            logger.error(f"Error closing Tortoise ORM connections: {e}")

    app.on_startup(_init_tortoise)
    app.on_shutdown(_close_tortoise)

    # Add exception handlers if requested
    if add_exception_handlers:
        handle_tortoise_exceptions(app)


def get_tortoise_client() -> TortoiseClient:
    """
    Get the Tortoise ORM client instance.

    Returns:
        The Tortoise ORM client instance.

    Raises:
        TortoiseConnectionError: If Tortoise client is not initialized.

    Example:
        ```python
        from nexios import NexiosApp
        from nexios_contrib.tortoise import init_tortoise, get_tortoise_client
        from app.models import User

        app = NexiosApp()

        @app.get("/users/{user_id}")
        async def get_user(request, response):
            tortoise = get_tortoise_client()
            user = await User.get(id=request.path_params["user_id"])
            return response.json(await user.to_dict())
        ```
    """
    global _tortoise_client
    if _tortoise_client is None:
        raise TortoiseConnectionError("Tortoise ORM client not initialized. Call init_tortoise() first.")
    return _tortoise_client