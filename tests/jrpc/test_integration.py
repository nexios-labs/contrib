"""
Integration tests for JRPC server using Nexios TestClient.
"""

import json
from typing import Dict, Any

import pytest

from nexios import NexiosApp
from nexios.testclient import TestClient
from nexios_contrib.jrpc import JsonRpcPlugin, JsonRpcRegistry, get_registry


class TestJRPCIntegration:
    """Integration tests for JRPC server."""

    def test_basic_method_call(self, jrpc_app, jrpc_client, registry):
        """Test basic JSON-RPC method call."""

        @registry.register()
        def add(a: int, b: int) -> int:
            return a + b

        # Make JSON-RPC request
        payload = {
            "jsonrpc": "2.0",
            "method": "add",
            "params": {"a": 5, "b": 3},
            "id": 1
        }

        response = jrpc_client.post("/rpc", json=payload)
        assert response.status_code == 200

        result = response.json()
        assert result["jsonrpc"] == "2.0"
        assert result["result"] == 8
        assert result["id"] == 1

    def test_method_call_with_positional_params(self, jrpc_app, jrpc_client, registry):
        """Test JSON-RPC method call with positional parameters."""

        @registry.register()
        def multiply(a: int, b: int) -> int:
            return a * b

        payload = {
            "jsonrpc": "2.0",
            "method": "multiply",
            "params": [4, 7],
            "id": 2
        }

        response = jrpc_client.post("/rpc", json=payload)
        assert response.status_code == 200

        result = response.json()
        assert result["result"] == 28
        assert result["id"] == 2

    def test_async_method_call(self, jrpc_app, jrpc_client, registry):
        """Test async JSON-RPC method call."""

        @registry.register()
        async def async_add(a: int, b: int) -> int:
            return a + b

        payload = {
            "jsonrpc": "2.0",
            "method": "async_add",
            "params": {"a": 10, "b": 5},
            "id": 3
        }

        response = jrpc_client.post("/rpc", json=payload)
        assert response.status_code == 200

        result = response.json()
        assert result["result"] == 15
        assert result["id"] == 3

    def test_multiple_methods(self, jrpc_app, jrpc_client, registry):
        """Test multiple registered methods."""

        @registry.register()
        def subtract(a: int, b: int) -> int:
            return a - b

        @registry.register()
        def divide(a: float, b: float) -> float:
            return a / b

        # Test subtract
        payload1 = {
            "jsonrpc": "2.0",
            "method": "subtract",
            "params": {"a": 10, "b": 3},
            "id": 4
        }

        response1 = jrpc_client.post("/rpc", json=payload1)
        assert response1.status_code == 200
        assert response1.json()["result"] == 7

        # Test divide
        payload2 = {
            "jsonrpc": "2.0",
            "method": "divide",
            "params": {"a": 15.0, "b": 3.0},
            "id": 5
        }

        response2 = jrpc_client.post("/rpc", json=payload2)
        assert response2.status_code == 200
        assert response2.json()["result"] == 5.0

    def test_method_with_default_parameters(self, jrpc_app, jrpc_client, registry):
        """Test method with default parameters."""

        @registry.register()
        def greet(name: str, greeting: str = "Hello") -> str:
            return f"{greeting}, {name}!"

        # Call without default parameter
        payload1 = {
            "jsonrpc": "2.0",
            "method": "greet",
            "params": {"name": "Alice"},
            "id": 6
        }

        response1 = jrpc_client.post("/rpc", json=payload1)
        assert response1.status_code == 200
        assert response1.json()["result"] == "Hello, Alice!"

        # Call with default parameter
        payload2 = {
            "jsonrpc": "2.0",
            "method": "greet",
            "params": {"name": "Bob", "greeting": "Hi"},
            "id": 7
        }

        response2 = jrpc_client.post("/rpc", json=payload2)
        assert response2.status_code == 200
        assert response2.json()["result"] == "Hi, Bob!"

    def test_method_without_parameters(self, jrpc_app, jrpc_client, registry):
        """Test method without parameters."""

        @registry.register()
        def get_time() -> str:
            return "2023-01-01"

        payload = {
            "jsonrpc": "2.0",
            "method": "get_time",
            "params": {},
            "id": 8
        }

        response = jrpc_client.post("/rpc", json=payload)
        assert response.status_code == 200
        assert response.json()["result"] == "2023-01-01"

    
    def test_custom_method_name(self, jrpc_app, jrpc_client, registry):
        """Test method registration with custom name."""

        @registry.register("custom_sum")
        def add_numbers(a: int, b: int) -> int:
            return a + b

        payload = {
            "jsonrpc": "2.0",
            "method": "custom_sum",
            "params": {"a": 7, "b": 8},
            "id": 9
        }

        response = jrpc_client.post("/rpc", json=payload)
        assert response.status_code == 200
        assert response.json()["result"] == 15

    def test_different_return_types(self, jrpc_app, jrpc_client, registry):
        """Test methods returning different types."""

        @registry.register()
        def get_string() -> str:
            return "test string"

        @registry.register()
        def get_number() -> int:
            return 42

        @registry.register()
        def get_boolean() -> bool:
            return True

        @registry.register()
        def get_list() -> list:
            return [1, 2, 3, 4, 5]

        @registry.register()
        def get_dict() -> dict:
            return {"key": "value", "number": 123}

        # Test string
        response1 = jrpc_client.post("/rpc", json={
            "jsonrpc": "2.0",
            "method": "get_string",
            "id": 10
        })
        assert response1.json()["result"] == "test string"

        # Test number
        response2 = jrpc_client.post("/rpc", json={
            "jsonrpc": "2.0",
            "method": "get_number",
            "id": 11
        })
        assert response2.json()["result"] == 42

        # Test boolean
        response3 = jrpc_client.post("/rpc", json={
            "jsonrpc": "2.0",
            "method": "get_boolean",
            "id": 12
        })
        assert response3.json()["result"] is True

        # Test list
        response4 = jrpc_client.post("/rpc", json={
            "jsonrpc": "2.0",
            "method": "get_list",
            "id": 13
        })
        assert response4.json()["result"] == [1, 2, 3, 4, 5]

        # Test dict
        response5 = jrpc_client.post("/rpc", json={
            "jsonrpc": "2.0",
            "method": "get_dict",
            "id": 14
        })
        assert response5.json()["result"] == {"key": "value", "number": 123}
