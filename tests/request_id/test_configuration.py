"""
Tests for Request ID dependency injection and configuration.
"""

import uuid
import pytest

from nexios import NexiosApp
from nexios.testclient import TestClient
from nexios_contrib.request_id import RequestIdMiddleware, RequestId
from nexios_contrib.request_id.dependency import RequestIdDepend


class TestRequestIdDependency:
    """Test Request ID dependency injection."""

    def test_request_id_dependency_injection(self, test_client_factory):
        """Test dependency injection of request ID into route handlers."""
        app = NexiosApp()
        app.add_middleware(RequestIdMiddleware())

        @app.get("/test")
        async def handler(request,response,request_id: str = RequestIdDepend()):
            return {"request_id": request_id}

        with test_client_factory(app) as client:
            resp = client.get("/test")

            assert resp.status_code == 200
            data = resp.json()

            # Should have request ID in response
            assert "request_id" in data
            assert data["request_id"] is not None

            # Should match header
            assert data["request_id"] == resp.headers["X-Request-ID"]

            # Should be valid UUID
            uuid.UUID(data["request_id"])

    def test_request_id_dependency_custom_attribute(self, test_client_factory):
        """Test dependency injection with custom attribute name."""
        app = NexiosApp()
        app.add_middleware(RequestIdMiddleware(request_attribute_name="custom_id"))

        @app.get("/test")
        async def handler(request, response, request_id: str = RequestIdDepend("custom_id")):
            return {"request_id": request_id}

        with test_client_factory(app) as client:
            resp = client.get("/test")

            assert resp.status_code == 200
            data = resp.json()

            # Should have request ID in response
            assert "request_id" in data
            assert data["request_id"] is not None

            # Should match header
            assert data["request_id"] == resp.headers["X-Request-ID"]

    def test_request_id_dependency_without_middleware(self, test_client_factory):
        """Test dependency injection without middleware (should fail gracefully)."""
        app = NexiosApp()
        # Note: No middleware added

        @app.get("/test")
        async def handler(request, response,request_id: str = RequestIdDepend()):
            return {"request_id": request_id}

        with test_client_factory(app) as client:
            resp = client.get("/test")

            assert resp.status_code == 200
            data = resp.json()

            # Should return None when no middleware is present
            assert data["request_id"] is None

    def test_request_id_dependency_multiple_endpoints(self, test_client_factory):
        """Test dependency injection across multiple endpoints."""
        app = NexiosApp()
        app.add_middleware(RequestIdMiddleware())

        @app.get("/endpoint1")
        async def handler1(request, response,request_id: str = RequestIdDepend()):
            return {"endpoint": "1", "request_id": request_id}

        @app.get("/endpoint2")
        async def handler2(request, response,request_id: str = RequestIdDepend()):
            return {"endpoint": "2", "request_id": request_id}

        with test_client_factory(app) as client:
            resp1 = client.get("/endpoint1")
            resp2 = client.get("/endpoint2")

            assert resp1.status_code == 200
            assert resp2.status_code == 200

            data1 = resp1.json()
            data2 = resp2.json()

            # Both should have request IDs
            assert data1["request_id"] is not None
            assert data2["request_id"] is not None

            # Should match respective headers
            assert data1["request_id"] == resp1.headers["X-Request-ID"]
            assert data2["request_id"] == resp2.headers["X-Request-ID"]

            # Should be different request IDs
            assert data1["request_id"] != data2["request_id"]


class TestRequestIdConfiguration:
    """Test Request ID configuration options."""

    

    def test_force_generate_configuration(self, test_client_factory):
        """Test force_generate configuration option."""
        app = NexiosApp()
        app.add_middleware(RequestIdMiddleware(force_generate=True))

        @app.get("/test")
        async def handler(request, response):
            return {"message": "test"}

        with test_client_factory(app) as client:
            custom_id = "550e8400-e29b-41d4-a716-446655440000"
            resp = client.get("/test", headers={"X-Request-ID": custom_id})

            assert resp.status_code == 200
            assert "X-Request-ID" in resp.headers

            # Should generate new ID despite custom header
            assert resp.headers["X-Request-ID"] != custom_id

            # Should be valid UUID
            uuid.UUID(resp.headers["X-Request-ID"])

    def test_custom_header_name_configuration(self, test_client_factory):
        """Test custom header name configuration."""
        app = NexiosApp()
        app.add_middleware(RequestIdMiddleware(header_name="X-Custom-Request-ID"))

        @app.get("/test")
        async def handler(request, response):
            return {"message": "test"}

        with test_client_factory(app) as client:
            resp = client.get("/test")

            assert resp.status_code == 200
            assert "X-Custom-Request-ID" in resp.headers
            assert "X-Request-ID" not in resp.headers

    def test_custom_attribute_name_configuration(self, test_client_factory):
        """Test custom attribute name configuration."""
        app = NexiosApp()
        app.add_middleware(RequestIdMiddleware(request_attribute_name="custom_id"))

        @app.get("/test")
        async def handler(request, response):
            stored_id = getattr(request.state, "custom_id", None)
            return {"stored_id": stored_id}

        with test_client_factory(app) as client:
            resp = client.get("/test")

            assert resp.status_code == 200
            data = resp.json()

            assert "stored_id" in data
            assert data["stored_id"] is not None
            assert data["stored_id"] == resp.headers["X-Request-ID"]

    def test_include_in_response_false_configuration(self, test_client_factory):
        """Test include_in_response=False configuration."""
        app = NexiosApp()
        app.add_middleware(RequestIdMiddleware(include_in_response=False))

        @app.get("/test")
        async def handler(request, response):
            return {"message": "test"}

        with test_client_factory(app) as client:
            resp = client.get("/test")

            assert resp.status_code == 200
            # Should not include in response headers
            assert "X-Request-ID" not in resp.headers

    def test_store_in_request_false_configuration(self, test_client_factory):
        """Test store_in_request=False configuration."""
        app = NexiosApp()
        app.add_middleware(RequestIdMiddleware(store_in_request=False))

        @app.get("/test")
        async def handler(request, response):
            stored_id = getattr(request.state, "request_id", None)
            return {"stored_id": stored_id}

        with test_client_factory(app) as client:
            resp = client.get("/test")

            assert resp.status_code == 200
            data = resp.json()

            # Should not store in request object
            assert data["stored_id"] is None

            # But should still include in response header
            assert "X-Request-ID" in resp.headers

    def test_convenience_function_configuration(self, test_client_factory):
        """Test RequestId convenience function with custom configuration."""
        app = NexiosApp()
        app.add_middleware(RequestId(
            header_name="X-Custom-Request-ID",
            force_generate=True,
            request_attribute_name="custom_id"
        ))

        @app.get("/test")
        async def handler(request, response):
            stored_id = getattr(request.state, "custom_id", None)
            return {"stored_id": stored_id}

        with test_client_factory(app) as client:
            custom_id = "550e8400-e29b-41d4-a716-446655440000"
            resp = client.get("/test", headers={"X-Custom-Request-ID": custom_id})

            assert resp.status_code == 200
            data = resp.json()

            # Should use custom header name
            assert "X-Custom-Request-ID" in resp.headers
            assert "X-Request-ID" not in resp.headers

            # Should force generate (ignore custom header)
            assert resp.headers["X-Custom-Request-ID"] != custom_id

            # Should store with custom attribute name
            assert data["stored_id"] == resp.headers["X-Custom-Request-ID"]

    def test_all_configuration_options_together(self, test_client_factory):
        """Test all configuration options working together."""
        app = NexiosApp()
        app.add_middleware(RequestIdMiddleware(
            header_name="X-Trace-ID",
            force_generate=True,
            store_in_request=True,
            request_attribute_name="trace_id",
            include_in_response=True
        ))

        @app.get("/test")
        async def handler(request, response):
            trace_id = getattr(request.state, "trace_id", None)
            return {"trace_id": trace_id}

        with test_client_factory(app) as client:
            custom_id = "550e8400-e29b-41d4-a716-446655440000"
            resp = client.get("/test", headers={"X-Trace-ID": custom_id})

            assert resp.status_code == 200
            data = resp.json()

            # Should use custom header name
            assert "X-Trace-ID" in resp.headers
            assert "X-Request-ID" not in resp.headers

            # Should force generate
            assert resp.headers["X-Trace-ID"] != custom_id

            # Should store with custom attribute
            assert data["trace_id"] == resp.headers["X-Trace-ID"]

            # Should be valid UUID
            uuid.UUID(resp.headers["X-Trace-ID"])
