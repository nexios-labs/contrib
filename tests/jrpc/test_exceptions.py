"""
Tests for JRPC exception handling.
"""

import json

import pytest

from nexios import NexiosApp
from nexios.testclient import TestClient
from nexios_contrib.jrpc import JsonRpcPlugin, JsonRpcRegistry
from nexios_contrib.jrpc.exceptions import (
    JsonRpcError,
    JsonRpcMethodNotFound,
    JsonRpcInvalidParams,
    JsonRpcInvalidRequest,
    JsonRpcClientError
)


class TestJRPCExceptions:
    """Tests for JRPC exception handling."""

   

    
    def test_invalid_request_missing_method(self, jrpc_app, jrpc_client):
        """Test invalid request - missing method."""

        payload = {
            "jsonrpc": "2.0",
            "params": {},
            "id": 1
        }

        response = jrpc_client.post("/rpc", json=payload)
        assert response.status_code == 200

        result = response.json()
        assert "error" in result
        assert result["error"]["code"] == -32600
        assert "Method name must be a string" in result["error"]["message"]

    def test_invalid_request_invalid_method_type(self, jrpc_app, jrpc_client):
        """Test invalid request - method is not a string."""

        payload = {
            "jsonrpc": "2.0",
            "method": 123,
            "params": {},
            "id": 1
        }

        response = jrpc_client.post("/rpc", json=payload)
        assert response.status_code == 200

        result = response.json()
        assert "error" in result
        assert result["error"]["code"] == -32600
        assert "Method name must be a string" in result["error"]["message"]

    def test_invalid_request_invalid_params_type(self, jrpc_app, jrpc_client):
        """Test invalid request - params is not object or array."""

        payload = {
            "jsonrpc": "2.0",
            "method": "test",
            "params": "invalid_params",
            "id": 1
        }

        response = jrpc_client.post("/rpc", json=payload)
        assert response.status_code == 200

        result = response.json()
        assert "error" in result
        assert result["error"]["code"] == -32600
        assert "Params must be an object or array" in result["error"]["message"]

    def test_invalid_request_invalid_id_type(self, jrpc_app, jrpc_client):
        """Test invalid request - id is not string or number."""

        payload = {
            "jsonrpc": "2.0",
            "method": "test",
            "params": {},
            "id": {"invalid": "id"}
        }

        response = jrpc_client.post("/rpc", json=payload)
        assert response.status_code == 200

        result = response.json()
        assert "error" in result
        assert result["error"]["code"] == -32600
        assert "Id must be a string or number" in result["error"]["message"]

    

    def test_method_exception_handling(self, jrpc_app, jrpc_client, registry):
        """Test handling of exceptions raised in methods."""

        @registry.register()
        def failing_method() -> str:
            raise ValueError("Something went wrong")

        payload = {
            "jsonrpc": "2.0",
            "method": "failing_method",
            "params": {},
            "id": 1
        }

        response = jrpc_client.post("/rpc", json=payload)
        assert response.status_code == 200

        result = response.json()
        assert "error" in result
        assert result["error"]["code"] == -32603  # Internal error
        assert "Internal error" in result["error"]["message"]
        assert "Something went wrong" in result["error"]["data"]

    
    def test_notification_request(self, jrpc_app, jrpc_client, registry):
        """Test notification request (no id)."""

        @registry.register()
        def log_message(message: str) -> str:
            return f"Logged: {message}"

        # Notification request (no id)
        payload = {
            "jsonrpc": "2.0",
            "method": "log_message",
            "params": {"message": "test"}
        }

        response = jrpc_client.post("/rpc", json=payload)
        assert response.status_code == 200

        result = response.json()
        # Should still return result even for notifications
        assert result["jsonrpc"] == "2.0"
        assert result["result"] == "Logged: test"
        # But no id field for notifications
        assert result["id"] is None



    

    def test_json_rpc_error_class(self):
        """Test JsonRpcError class."""

        error = JsonRpcError(code=-32000, message="Custom error")

        assert error.code == -32000
        assert error.message == "Custom error"
        assert error.data is None

        # Test with data
        error_with_data = JsonRpcError(code=-32001, message="Error with data", data={"extra": "info"})
        assert error_with_data.data == {"extra": "info"}

    def test_json_rpc_method_not_found_exception(self):
        """Test JsonRpcMethodNotFound exception."""

        exc = JsonRpcMethodNotFound("test_method")

        assert exc.code == -32601
        assert "Method not found: test_method" == str(exc)
        assert exc.data is None

    def test_json_rpc_invalid_params_exception(self):
        """Test JsonRpcInvalidParams exception."""

        exc = JsonRpcInvalidParams("Invalid parameter type")

        assert exc.code == -32602
        assert str(exc) == "Invalid parameter type"

    def test_json_rpc_invalid_request_exception(self):
        """Test JsonRpcInvalidRequest exception."""

        exc = JsonRpcInvalidRequest("Malformed request")

        assert exc.code == -32600
        assert str(exc) == "Malformed request"

    def test_json_rpc_client_error(self):
        """Test JsonRpcClientError exception."""

        exc = JsonRpcClientError(code=-32603, message="Client error", data="extra data")

        assert exc.code == -32603
        assert exc.message == "Client error"
        assert exc.data == "extra data"
        assert str(exc) == "[-32603] Client error"
