"""
Test configuration and fixtures for nexios-contrib etag tests.
"""

import functools
from typing import Callable, Optional, Any

import pytest

from nexios import NexiosApp
from nexios.testclient import TestClient


@pytest.fixture
def test_client_factory():
    """Factory for creating TestClient instances."""
    return functools.partial(TestClient)


@pytest.fixture
def app_factory():
    """Factory for creating NexiosApp instances with optional middleware."""
    def _create_app(middleware: Optional[Any] = None):
        app = NexiosApp()
        if middleware:
            app.add_middleware(middleware)
        return app

    return _create_app
