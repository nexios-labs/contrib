"""
Test configuration and fixtures for nexios-contrib jrpc tests.
"""

import functools
from typing import Callable, Optional, Any

import pytest

from nexios import NexiosApp
from nexios.testclient import TestClient
from nexios_contrib.jrpc import JsonRpcPlugin, JsonRpcRegistry, get_registry


@pytest.fixture
def test_client_factory():
    """Factory for creating TestClient instances."""
    return functools.partial(TestClient)


@pytest.fixture
def app_factory():
    """Factory for creating NexiosApp instances with optional JRPC plugin."""
    def _create_app(jrpc_config: Optional[dict] = None):
        app = NexiosApp()
        if jrpc_config:
            JsonRpcPlugin(app, jrpc_config)
        return app

    return _create_app


@pytest.fixture
def jrpc_app():
    """Create a NexiosApp with JRPC plugin for testing."""
    app = NexiosApp()
    JsonRpcPlugin(app)
    return app


@pytest.fixture
def jrpc_client(jrpc_app):
    """Create a TestClient for JRPC testing."""
    return TestClient(jrpc_app)


@pytest.fixture
def registry():
    """Get a fresh JRPC registry for testing."""
    # Clear the singleton registry
    registry_instance = JsonRpcRegistry()
    registry_instance.methods.clear()
    return registry_instance


@pytest.fixture(autouse=True)
def clear_registry():
    """Clear the registry before each test."""
    registry_instance = get_registry()
    registry_instance.methods.clear()
    yield
    registry_instance.methods.clear()
