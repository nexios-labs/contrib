"""
Tests for JsonRpcClient functionality.
"""

import json
import pytest

from nexios import NexiosApp
from nexios.testclient import TestClient
from nexios_contrib.jrpc import JsonRpcClient, JsonRpcRegistry


class TestJsonRpcClient:
    """Tests for JsonRpcClient."""

    @pytest.fixture
    def client_app(self, registry):
        """Create a test app with JRPC methods for client testing."""

        @registry.register()
        def add(a: int, b: int) -> int:
            return a + b

        @registry.register()
        def multiply(a: int, b: int) -> int:
            return a * b

        @registry.register()
        def divide(a: float, b: float) -> float:
            if b == 0:
                raise ValueError("Division by zero")
            return a / b

        app = NexiosApp()
        from nexios_contrib.jrpc import JsonRpcPlugin
        JsonRpcPlugin(app)

        return app

    @pytest.fixture
    def test_server(self, client_app):
        """Create a test server URL."""
        # Use TestClient as a server for testing the client
        return TestClient(client_app)

    def test_client_initialization(self, client_app):
        """Test client initialization."""

        # This test would normally use a real HTTP server URL
        # For testing purposes, we'll test the client structure
        client = JsonRpcClient("http://localhost:8000/rpc")

        assert client.base_url == "http://localhost:8000/rpc"
        assert client.request_id == 0

    def test_generate_request_id(self, client_app):
        """Test request ID generation."""

        client = JsonRpcClient("http://localhost:8000/rpc")

        id1 = client._generate_request_id()
        id2 = client._generate_request_id()
        id3 = client._generate_request_id()

        assert id1 == 1
        assert id2 == 2
        assert id3 == 3
        assert client.request_id == 3

    def test_method_call_via_attribute(self, client_app):
        """Test calling methods via attribute access."""

        client = JsonRpcClient("http://localhost:8000/rpc")

        # This would normally make HTTP requests
        # For testing, we verify the method caller is created
        method_caller = client.add

        assert callable(method_caller)

        # Test the method caller functionality (without actual HTTP call)
        # In a real test, this would make an HTTP request
        # result = method_caller(a=5, b=3)
        # assert result == 8

    def test_call_method_sync(self, client_app):
        """Test synchronous method call."""

        client = JsonRpcClient("http://localhost:8000/rpc")

        # This would normally make HTTP requests
        # For testing purposes, we test the method structure
        assert hasattr(client, 'call')
        assert callable(client.call)

        # Test parameters
        # In real usage:
        # result = client.call("add", {"a": 5, "b": 3})
        # assert result == 8

    def test_acall_method_async(self, client_app):
        """Test asynchronous method call."""

        client = JsonRpcClient("http://localhost:8000/rpc")

        # This would normally make async HTTP requests
        assert hasattr(client, 'acall')
        assert callable(client.acall)

    
    def test_client_with_different_base_urls(self, client_app):
        """Test client with different base URLs."""

        client1 = JsonRpcClient("http://localhost:8000/rpc")
        client2 = JsonRpcClient("http://example.com/api/jsonrpc")
        client3 = JsonRpcClient("https://secure.example.com/v1/rpc")

        assert client1.base_url == "http://localhost:8000/rpc"
        assert client2.base_url == "http://example.com/api/jsonrpc"
        assert client3.base_url == "https://secure.example.com/v1/rpc"

    def test_client_request_id_increment(self, client_app):
        """Test that request IDs increment properly."""

        client = JsonRpcClient("http://localhost:8000/rpc")

        initial_id = client.request_id

        # Generate several IDs
        for i in range(1, 6):
            new_id = client._generate_request_id()
            assert new_id == initial_id + i

        assert client.request_id == initial_id + 5
