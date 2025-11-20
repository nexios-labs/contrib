"""
Tests for Tortoise ORM initialization and main module functions.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from nexios import NexiosApp
from nexios_contrib.tortoise import (
    init_tortoise,
    get_tortoise_client,
    TortoiseConnectionError,
)
from nexios_contrib.tortoise.config import TortoiseConfig


class TestTortoiseInit:
    """Test Tortoise ORM initialization."""

    def test_init_tortoise_basic(self):
        """Test basic Tortoise initialization."""
        app = NexiosApp()
        
        with patch("nexios_contrib.tortoise.TortoiseClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            
            init_tortoise(
                app,
                db_url="sqlite://:memory:",
                modules={"models": ["app.models"]},
                generate_schemas=True
            )
            
            # Verify client was created with correct config
            mock_client_class.assert_called_once()
            config_arg = mock_client_class.call_args[0][0]
            assert isinstance(config_arg, TortoiseConfig)
            assert config_arg.db_url == "sqlite://:memory:"
            assert config_arg.modules == {"models": ["app.models"]}
            assert config_arg.generate_schemas is True
            
            # Verify client was stored in app state
            assert app.state["tortoise"] == mock_client
            
            # Verify startup and shutdown handlers were registered
            assert len(app.startup_handlers) == 1
            assert len(app.shutdown_handlers) == 1

    def test_init_tortoise_with_defaults(self):
        """Test Tortoise initialization with default values."""
        app = NexiosApp()
        
        with patch("nexios_contrib.tortoise.TortoiseClient") as mock_client_class:
            init_tortoise(app, db_url="sqlite://:memory:")
            
            config_arg = mock_client_class.call_args[0][0]
            assert config_arg.modules == {"models": []}
            assert config_arg.generate_schemas is False

    def test_init_tortoise_without_exception_handlers(self):
        """Test initialization without exception handlers."""
        app = NexiosApp()
        
        with patch("nexios_contrib.tortoise.TortoiseClient"):
            with patch("nexios_contrib.tortoise.handle_tortoise_exceptions") as mock_handle:
                init_tortoise(
                    app,
                    db_url="sqlite://:memory:",
                    add_exception_handlers=False
                )
                
                # Exception handlers should not be added
                mock_handle.assert_not_called()

    def test_init_tortoise_with_exception_handlers(self):
        """Test initialization with exception handlers."""
        app = NexiosApp()
        
        with patch("nexios_contrib.tortoise.TortoiseClient"):
            with patch("nexios_contrib.tortoise.handle_tortoise_exceptions") as mock_handle:
                init_tortoise(
                    app,
                    db_url="sqlite://:memory:",
                    add_exception_handlers=True
                )
                
                # Exception handlers should be added
                mock_handle.assert_called_once_with(app)

    def test_init_tortoise_with_kwargs(self):
        """Test initialization with additional kwargs."""
        app = NexiosApp()
        
        with patch("nexios_contrib.tortoise.TortoiseClient") as mock_client_class:
            init_tortoise(
                app,
                db_url="sqlite://:memory:",
                modules={"models": ["app.models"]},
                use_tz=True,
                timezone="America/New_York",
                custom_param="custom_value"
            )
            
            config_arg = mock_client_class.call_args[0][0]
            assert config_arg.use_tz is True
            assert config_arg.timezone == "America/New_York"

    @pytest.mark.asyncio
    async def test_startup_handler_success(self):
        """Test successful startup handler execution."""
        app = NexiosApp()
        
        with patch("nexios_contrib.tortoise.TortoiseClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.init = AsyncMock()
            mock_client_class.return_value = mock_client
            
            init_tortoise(app, db_url="sqlite://:memory:")
            
            # Execute startup handler
            await app._startup()
            
            # Verify client.init was called
            mock_client.init.assert_called_once()

    @pytest.mark.asyncio
    async def test_startup_handler_failure(self):
        """Test startup handler failure."""
        app = NexiosApp()
        
        with patch("nexios_contrib.tortoise.TortoiseClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.init = AsyncMock(side_effect=Exception("Init failed"))
            mock_client_class.return_value = mock_client
            
            init_tortoise(app, db_url="sqlite://:memory:")
            
            # Startup should raise TortoiseConnectionError
            with pytest.raises(TortoiseConnectionError) as exc_info:
                await app._startup()
            
            assert "Failed to initialize Tortoise ORM" in str(exc_info.value)
            assert "Init failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_shutdown_handler_success(self):
        """Test successful shutdown handler execution."""
        app = NexiosApp()
        
        with patch("nexios_contrib.tortoise.TortoiseClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client
            
            init_tortoise(app, db_url="sqlite://:memory:")
            
            # Execute shutdown handler
            await app._shutdown()
            
            # Verify client.close was called
            mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_handler_failure(self):
        """Test shutdown handler with error (should not raise)."""
        app = NexiosApp()
        
        with patch("nexios_contrib.tortoise.TortoiseClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.close = AsyncMock(side_effect=Exception("Close failed"))
            mock_client_class.return_value = mock_client
            
            init_tortoise(app, db_url="sqlite://:memory:")
            
            # Shutdown should not raise (errors are logged)
            await app._shutdown()
            
            # Verify client.close was called
            mock_client.close.assert_called_once()

    def test_get_tortoise_client_success(self):
        """Test successful client retrieval."""
        app = NexiosApp()
        
        with patch("nexios_contrib.tortoise.TortoiseClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            
            init_tortoise(app, db_url="sqlite://:memory:")
            
            client = get_tortoise_client()
            assert client == mock_client

    def test_get_tortoise_client_not_initialized(self):
        """Test client retrieval when not initialized."""
        # Reset global client
        import nexios_contrib.tortoise
        nexios_contrib.tortoise._tortoise_client = None
        
        with pytest.raises(TortoiseConnectionError) as exc_info:
            get_tortoise_client()
        
        assert "Tortoise ORM client not initialized" in str(exc_info.value)
        assert "Call init_tortoise() first" in str(exc_info.value)

    def test_multiple_init_calls(self):
        """Test that multiple init calls work correctly."""
        app = NexiosApp()
        
        with patch("nexios_contrib.tortoise.TortoiseClient") as mock_client_class:
            mock_client1 = MagicMock()
            mock_client2 = MagicMock()
            mock_client_class.side_effect = [mock_client1, mock_client2]
            
            # First init
            init_tortoise(app, db_url="sqlite://:memory:")
            client1 = get_tortoise_client()
            assert client1 == mock_client1
            
            # Second init (should replace the first)
            init_tortoise(app, db_url="sqlite://test.db")
            client2 = get_tortoise_client()
            assert client2 == mock_client2
            assert client2 != client1

    def test_init_tortoise_complex_config(self):
        """Test initialization with complex configuration."""
        app = NexiosApp()
        
        modules = {
            "models": ["app.models", "app.user_models"],
            "analytics": ["analytics.models"]
        }
        
        with patch("nexios_contrib.tortoise.TortoiseClient") as mock_client_class:
            init_tortoise(
                app,
                db_url="postgres://user:pass@localhost:5432/db",
                modules=modules,
                generate_schemas=False,
                add_exception_handlers=True,
                use_tz=True,
                timezone="Europe/London"
            )
            
            config_arg = mock_client_class.call_args[0][0]
            assert config_arg.db_url == "postgres://user:pass@localhost:5432/db"
            assert config_arg.modules == modules
            assert config_arg.generate_schemas is False
            assert config_arg.use_tz is True
            assert config_arg.timezone == "Europe/London"

    def test_app_state_storage(self):
        """Test that client is stored in app state."""
        app = NexiosApp()
        
        with patch("nexios_contrib.tortoise.TortoiseClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            
            init_tortoise(app, db_url="sqlite://:memory:")
            
            # Verify client is in app state
            assert "tortoise" in app.state
            assert app.state["tortoise"] == mock_client

    def test_handler_registration_count(self):
        """Test that exactly one startup and shutdown handler are registered."""
        app = NexiosApp()
        
        initial_startup_count = len(app.startup_handlers)
        initial_shutdown_count = len(app.shutdown_handlers)
        
        with patch("nexios_contrib.tortoise.TortoiseClient"):
            init_tortoise(app, db_url="sqlite://:memory:")
            
            # Should add exactly one of each handler
            assert len(app.startup_handlers) == initial_startup_count + 1
            assert len(app.shutdown_handlers) == initial_shutdown_count + 1