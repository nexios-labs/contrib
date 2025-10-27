"""
Configuration tests for JRPC plugin.
"""

import pytest

from nexios import NexiosApp
from nexios.testclient import TestClient
from nexios_contrib.jrpc import JsonRpcPlugin, JsonRpcRegistry


class TestJRPCConfiguration:
    """Configuration tests for JRPC plugin."""

    def test_default_path_prefix(self, app_factory, test_client_factory, registry):
        """Test default path prefix configuration."""

        @registry.register()
        def test_method(a: int) -> int:
            return a * 2

        app = app_factory({"path_prefix": "/rpc"})
        client = test_client_factory(app)

        payload = {
            "jsonrpc": "2.0",
            "method": "test_method",
            "params": {"a": 5},
            "id": 1
        }

        response = client.post("/rpc", json=payload)
        assert response.status_code == 200
        assert response.json()["result"] == 10

    def test_custom_path_prefix(self, app_factory, test_client_factory, registry):
        """Test custom path prefix configuration."""

        @registry.register()
        def test_method(a: int) -> int:
            return a * 3

        app = app_factory({"path_prefix": "/api/jsonrpc"})
        client = test_client_factory(app)

        payload = {
            "jsonrpc": "2.0",
            "method": "test_method",
            "params": {"a": 4},
            "id": 1
        }

        # Should work with custom prefix
        response = client.post("/api/jsonrpc", json=payload)
        assert response.status_code == 200
        assert response.json()["result"] == 12

        # Should not work with default prefix
        response_default = client.post("/rpc", json=payload)
        assert response_default.status_code == 404

    def test_root_path_prefix(self, app_factory, test_client_factory, registry):
        """Test root path prefix configuration."""

        @registry.register()
        def test_method(a: int) -> int:
            return a + 10

        app = app_factory({"path_prefix": "/"})
        client = test_client_factory(app)

        payload = {
            "jsonrpc": "2.0",
            "method": "test_method",
            "params": {"a": 5},
            "id": 1
        }

        response = client.post("/", json=payload)
        assert response.status_code == 200
        assert response.json()["result"] == 15

    def test_nested_path_prefix(self, app_factory, test_client_factory, registry):
        """Test nested path prefix configuration."""

        @registry.register()
        def test_method(a: int) -> int:
            return a * 4

        app = app_factory({"path_prefix": "/api/v1/rpc"})
        client = test_client_factory(app)

        payload = {
            "jsonrpc": "2.0",
            "method": "test_method",
            "params": {"a": 3},
            "id": 1
        }

        # Should work with nested prefix
        response = client.post("/api/v1/rpc", json=payload)
        assert response.status_code == 200
        assert response.json()["result"] == 12

        # Should not work with shorter prefix
        response_short = client.post("/api/rpc", json=payload)
        assert response_short.status_code == 404

    def test_plugin_without_explicit_config(self, app_factory, test_client_factory, registry):
        """Test plugin with default configuration."""

        @registry.register()
        def test_method(a: int) -> int:
            return a + 100

        # Create app and plugin without explicit config
        app = NexiosApp()
        plugin = JsonRpcPlugin(app)  # Uses default config
        client = test_client_factory(app)

        payload = {
            "jsonrpc": "2.0",
            "method": "test_method",
            "params": {"a": 5},
            "id": 1
        }

        response = client.post("/rpc", json=payload)
        assert response.status_code == 200
        assert response.json()["result"] == 105

    def test_multiple_plugins_different_prefixes(self, test_client_factory, registry):
        """Test multiple JRPC plugins with different prefixes."""

        # Create first app with first prefix
        app1 = NexiosApp()
        JsonRpcPlugin(app1, {"path_prefix": "/api1"})
        client1 = test_client_factory(app1)

        @registry.register("method1")
        def method_one(a: int) -> int:
            return a + 1

        # Create second app with second prefix
        app2 = NexiosApp()
        JsonRpcPlugin(app2, {"path_prefix": "/api2"})
        client2 = test_client_factory(app2)

        @registry.register("method2")
        def method_two(a: int) -> int:
            return a + 2

        # Test first app
        payload1 = {
            "jsonrpc": "2.0",
            "method": "method1",
            "params": {"a": 5},
            "id": 1
        }

        response1 = client1.post("/api1", json=payload1)
        assert response1.status_code == 200
        assert response1.json()["result"] == 6

        # Test second app
        payload2 = {
            "jsonrpc": "2.0",
            "method": "method2",
            "params": {"a": 5},
            "id": 1
        }

        response2 = client2.post("/api2", json=payload2)
        assert response2.status_code == 200
        assert response2.json()["result"] == 7

    def test_plugin_integration_with_other_routes(self, app_factory, test_client_factory, registry):
        """Test JRPC plugin alongside other routes."""

        app = app_factory({"path_prefix": "/jsonrpc"})

        @registry.register()
        def calculate(a: int, b: int) -> int:
            return a + b

        @app.get("/health")
        async def health_check(request, response):
            return {"status": "healthy"}

        @app.get("/api/users")
        async def get_users(request, response):
            return [{"id": 1, "name": "Alice"}]

        client = test_client_factory(app)

        # Test regular routes still work
        health_response = client.get("/health")
        assert health_response.status_code == 200
        assert health_response.json()["status"] == "healthy"

        users_response = client.get("/api/users")
        assert users_response.status_code == 200
        assert users_response.json() == [{"id": 1, "name": "Alice"}]

        # Test JRPC still works
        jrpc_payload = {
            "jsonrpc": "2.0",
            "method": "calculate",
            "params": {"a": 10, "b": 20},
            "id": 1
        }

        jrpc_response = client.post("/jsonrpc", json=jrpc_payload)
        assert jrpc_response.status_code == 200
        assert jrpc_response.json()["result"] == 30
