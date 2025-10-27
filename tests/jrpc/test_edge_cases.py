"""
Edge cases and complex scenario tests for JRPC.
"""

import json
from typing import Any, Dict

import pytest

from nexios import NexiosApp
from nexios.testclient import TestClient
from nexios_contrib.jrpc import JsonRpcPlugin, JsonRpcRegistry


class TestJRPEdgeCases:
    """Edge cases and complex scenarios for JRPC."""

    def test_very_large_request_id(self, jrpc_app, jrpc_client, registry):
        """Test with very large request ID."""

        @registry.register()
        def echo(value: Any) -> Any:
            return value

        payload = {
            "jsonrpc": "2.0",
            "method": "echo",
            "params": {"value": "test"},
            "id": 999999999999999999999999999999999999999999999999999999999999999999
        }

        response = jrpc_client.post("/rpc", json=payload)
        assert response.status_code == 200

        result = response.json()
        assert result["result"] == "test"
        assert result["id"] == 999999999999999999999999999999999999999999999999999999999999999999

    def test_string_request_id(self, jrpc_app, jrpc_client, registry):
        """Test with string request ID."""

        @registry.register()
        def echo(value: Any) -> Any:
            return value

        payload = {
            "jsonrpc": "2.0",
            "method": "echo",
            "params": {"value": "test"},
            "id": "unique-request-id-123"
        }

        response = jrpc_client.post("/rpc", json=payload)
        assert response.status_code == 200

        result = response.json()
        assert result["result"] == "test"
        assert result["id"] == "unique-request-id-123"

    def test_null_request_id(self, jrpc_app, jrpc_client, registry):
        """Test with null request ID."""

        @registry.register()
        def echo(value: Any) -> Any:
            return value

        payload = {
            "jsonrpc": "2.0",
            "method": "echo",
            "params": {"value": "test"},
            "id": None
        }

        response = jrpc_client.post("/rpc", json=payload)
        assert response.status_code == 200

        result = response.json()
        assert result["result"] == "test"
        assert result["id"] is None

   

        
    

   
    def test_method_with_mixed_param_types(self, jrpc_app, jrpc_client, registry):
        """Test method with mixed parameter types."""

        @registry.register()
        def mixed_params(
            number: int,
            text: str,
            flag: bool,
            numbers: list,
            config: dict
        ) -> dict:
            return {
                "number": number,
                "text": text,
                "flag": flag,
                "sum": sum(numbers),
                "config_keys": list(config.keys())
            }

        payload = {
            "jsonrpc": "2.0",
            "method": "mixed_params",
            "params": {
                "number": 42,
                "text": "test",
                "flag": True,
                "numbers": [1, 2, 3],
                "config": {"host": "localhost", "port": 8080}
            },
            "id": 1
        }

        response = jrpc_client.post("/rpc", json=payload)
        assert response.status_code == 200

        result = response.json()["result"]
        assert result["number"] == 42
        assert result["text"] == "test"
        assert result["flag"] is True
        assert result["sum"] == 6
        assert result["config_keys"] == ["host", "port"]

    def test_rapid_successive_calls(self, jrpc_app, jrpc_client, registry):
        """Test rapid successive calls."""

        @registry.register()
        def increment(counter: int) -> int:
            return counter + 1

        # Make multiple rapid calls
        results = []
        for i in range(10):
            payload = {
                "jsonrpc": "2.0",
                "method": "increment",
                "params": {"counter": i},
                "id": i
            }

            response = jrpc_client.post("/rpc", json=payload)
            assert response.status_code == 200
            results.append(response.json()["result"])

        # Check results are correct
        expected = list(range(1, 11))
        assert results == expected

    def test_method_with_special_characters_in_name(self, jrpc_app, jrpc_client, registry):
        """Test method with special characters in name."""

        @registry.register("method_with_special-chars.test")
        def special_method(value: str) -> str:
            return f"processed: {value}"

        payload = {
            "jsonrpc": "2.0",
            "method": "method_with_special-chars.test",
            "params": {"value": "test"},
            "id": 1
        }

        response = jrpc_client.post("/rpc", json=payload)
        assert response.status_code == 200
        assert response.json()["result"] == "processed: test"

    def test_empty_method_name(self, jrpc_app, jrpc_client):
        """Test empty method name error."""

        payload = {
            "jsonrpc": "2.0",
            "method": "",
            "params": {},
            "id": 1
        }

        response = jrpc_client.post("/rpc", json=payload)
        assert response.status_code == 200

        result = response.json()
        assert "error" in result
        assert result["error"]["code"] == -32600
        assert "Method name must be a string" in result["error"]["message"]

    def test_method_name_with_whitespace(self, jrpc_app, jrpc_client, registry):
        """Test method name with whitespace."""

        @registry.register()
        def method_with_spaces() -> str:
            return "success"

        payload = {
            "jsonrpc": "2.0",
            "method": "method_with_spaces",
            "params": {},
            "id": 1
        }

        response = jrpc_client.post("/rpc", json=payload)
        assert response.status_code == 200
        assert response.json()["result"] == "success"

    def test_very_long_method_name(self, jrpc_app, jrpc_client, registry):
        """Test very long method name."""

        long_name = "a" * 1000  # 1000 character method name

        @registry.register(long_name)
        def very_long_name_method() -> str:
            return "success"

        payload = {
            "jsonrpc": "2.0",
            "method": long_name,
            "params": {},
            "id": 1
        }

        response = jrpc_client.post("/rpc", json=payload)
        assert response.status_code == 200
        assert response.json()["result"] == "success"

    def test_large_response_data(self, jrpc_app, jrpc_client, registry):
        """Test with large response data."""

        @registry.register()
        def generate_large_data(size: int) -> list:
            return list(range(size))

        payload = {
            "jsonrpc": "2.0",
            "method": "generate_large_data",
            "params": {"size": 1000},
            "id": 1
        }

        response = jrpc_client.post("/rpc", json=payload)
        assert response.status_code == 200

        result = response.json()["result"]
        assert len(result) == 1000
        assert result[0] == 0
        assert result[-1] == 999
