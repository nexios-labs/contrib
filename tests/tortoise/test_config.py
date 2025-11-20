"""
Tests for Tortoise ORM configuration.
"""

import os
import pytest
from pydantic import ValidationError

from nexios_contrib.tortoise.config import TortoiseConfig


class TestTortoiseConfig:
    """Test Tortoise ORM configuration."""

    def test_basic_config_creation(self):
        """Test basic configuration creation."""
        config = TortoiseConfig(
            db_url="sqlite://:memory:",
            modules={"models": ["app.models"]},
            generate_schemas=True
        )
        
        assert config.db_url == "sqlite://:memory:"
        assert config.modules == {"models": ["app.models"]}
        assert config.generate_schemas is True
        assert config.use_tz is False
        assert config.timezone == "UTC"

    def test_default_values(self):
        """Test default configuration values."""
        config = TortoiseConfig(db_url="sqlite://:memory:")
        
        assert config.modules == {"models": []}
        assert config.generate_schemas is False
        assert config.use_tz is False
        assert config.timezone == "UTC"
        assert config.connections is None
        assert config.apps is None

    def test_db_url_validation(self):
        """Test database URL validation."""
        # Valid URLs
        valid_urls = [
            "sqlite://:memory:",
            "sqlite://db.sqlite3",
            "postgres://user:pass@localhost:5432/db",
            "postgresql://user:pass@localhost:5432/db",
            "mysql://user:pass@localhost:3306/db",
            "asyncpg://user:pass@localhost:5432/db",
            "aiomysql://user:pass@localhost:3306/db",
        ]
        
        for url in valid_urls:
            config = TortoiseConfig(db_url=url)
            assert config.db_url == url

        # Invalid URLs
        invalid_urls = [
            "invalid://url",
            "http://example.com",
            "ftp://example.com",
            "redis://localhost:6379",
        ]
        
        for url in invalid_urls:
            with pytest.raises(ValidationError):
                TortoiseConfig(db_url=url)

    def test_modules_validation(self):
        """Test modules configuration validation."""
        # Valid modules
        valid_modules = [
            {"models": ["app.models"]},
            {"app1": ["app1.models"], "app2": ["app2.models"]},
            {"models": ["app.models", "app.user_models"]},
        ]
        
        for modules in valid_modules:
            config = TortoiseConfig(db_url="sqlite://:memory:", modules=modules)
            assert config.modules == modules

        # Invalid modules
        invalid_modules = [
            "not_a_dict",
            {"models": "not_a_list"},
            {"models": [123, 456]},  # Non-string modules
        ]
        
        for modules in invalid_modules:
            with pytest.raises(ValidationError):
                TortoiseConfig(db_url="sqlite://:memory:", modules=modules)

    def test_to_tortoise_config(self):
        """Test conversion to Tortoise.init() kwargs."""
        config = TortoiseConfig(
            db_url="sqlite://:memory:",
            modules={"models": ["app.models"]},
            generate_schemas=True,
            use_tz=True,
            timezone="America/New_York"
        )
        
        tortoise_config = config.to_tortoise_config()
        
        expected_keys = ["db_url", "modules", "use_tz", "timezone"]
        for key in expected_keys:
            assert key in tortoise_config
        
        assert tortoise_config["db_url"] == "sqlite://:memory:"
        assert tortoise_config["modules"] == {"models": ["app.models"]}
        assert tortoise_config["use_tz"] is True
        assert tortoise_config["timezone"] == "America/New_York"

    def test_to_tortoise_config_with_connections_and_apps(self):
        """Test conversion with custom connections and apps."""
        connections = {
            "default": "sqlite://:memory:",
            "cache": "sqlite://cache.db"
        }
        apps = {
            "models": {
                "models": ["app.models"],
                "default_connection": "default"
            }
        }
        
        config = TortoiseConfig(
            db_url="sqlite://:memory:",
            connections=connections,
            apps=apps
        )
        
        tortoise_config = config.to_tortoise_config()
        
        assert tortoise_config["connections"] == connections
        assert tortoise_config["apps"] == apps

    

    
    
    

    def test_str_representation(self):
        """Test string representation of config."""
        config = TortoiseConfig(
            db_url="sqlite://:memory:",
            modules={"models": ["app.models"]}
        )
        
        config_str = str(config)
        assert "TortoiseConfig" in config_str
        assert "sqlite://:memory:" in config_str

    def test_str_representation_with_password(self):
        """Test string representation masks password in URL."""
        config = TortoiseConfig(
            db_url="postgres://user:secret@localhost:5432/db"
        )
        
        config_str = str(config)
        assert "secret" not in config_str
        assert "***" in config_str
        assert "postgres://user:***@localhost:5432/db" in config_str

    def test_complex_configuration(self):
        """Test complex configuration with all options."""
        connections = {
            "default": "sqlite://:memory:",
            "users": "postgres://user:pass@localhost:5432/users",
            "analytics": "mysql://user:pass@localhost:3306/analytics"
        }
        
        apps = {
            "models": {
                "models": ["app.models"],
                "default_connection": "default"
            },
            "users": {
                "models": ["users.models"],
                "default_connection": "users"
            }
        }
        
        config = TortoiseConfig(
            db_url="sqlite://:memory:",
            modules={"models": ["app.models", "users.models"]},
            generate_schemas=True,
            use_tz=True,
            timezone="UTC",
            connections=connections,
            apps=apps
        )
        
        assert config.db_url == "sqlite://:memory:"
        assert config.modules == {"models": ["app.models", "users.models"]}
        assert config.generate_schemas is True
        assert config.use_tz is True
        assert config.timezone == "UTC"
        assert config.connections == connections
        assert config.apps == apps
        
        # Test conversion
        tortoise_config = config.to_tortoise_config()
        assert tortoise_config["connections"] == connections
        assert tortoise_config["apps"] == apps