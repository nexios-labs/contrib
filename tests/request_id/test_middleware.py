"""
Tests for RequestIdMiddleware.
"""

import pytest
import uuid

from nexios import NexiosApp
from nexios.testclient import TestClient
from nexios_contrib.request_id import RequestIdMiddleware


class TestRequestIdMiddleware:
    """Test RequestIdMiddleware functionality."""

    def test_middleware_generates_request_id_on_get(self, test_client_factory):
        """Test that middleware generates request ID on GET requests."""
        app = NexiosApp()
        app.add_middleware(RequestIdMiddleware())

        @app.get("/test")
        async def handler(request, response):
            return {"message": "Hello, World!"}

        with test_client_factory(app) as client:
            resp = client.get("/test")
            assert resp.status_code == 200
            assert "X-Request-ID" in resp.headers

            # Validate UUID format
            request_id = resp.headers["X-Request-ID"]
            uuid.UUID(request_id)  # Should not raise exception

    def test_middleware_generates_request_id_on_post(self, test_client_factory):
        """Test that middleware generates request ID on POST requests."""
        app = NexiosApp()
        app.add_middleware(RequestIdMiddleware())

        @app.post("/test")
        async def handler(request, response):
            return {"message": "Created"}

        with test_client_factory(app) as client:
            resp = client.post("/test", json={"data": "test"})
            assert resp.status_code == 200
            assert "X-Request-ID" in resp.headers

            # Validate UUID format
            request_id = resp.headers["X-Request-ID"]
            uuid.UUID(request_id)  # Should not raise exception

    def test_middleware_generates_request_id_on_put(self, test_client_factory):
        """Test that middleware generates request ID on PUT requests."""
        app = NexiosApp()
        app.add_middleware(RequestIdMiddleware())

        @app.put("/test")
        async def handler(request, response):
            return {"message": "Updated"}

        with test_client_factory(app) as client:
            resp = client.put("/test", json={"data": "test"})
            assert resp.status_code == 200
            assert "X-Request-ID" in resp.headers

    def test_middleware_generates_request_id_on_delete(self, test_client_factory):
        """Test that middleware generates request ID on DELETE requests."""
        app = NexiosApp()
        app.add_middleware(RequestIdMiddleware())

        @app.delete("/test")
        async def handler(request, response):
            return {"message": "Deleted"}

        with test_client_factory(app) as client:
            resp = client.delete("/test")
            assert resp.status_code == 200
            assert "X-Request-ID" in resp.headers

    def test_middleware_generates_unique_request_ids(self, test_client_factory):
        """Test that middleware generates unique request IDs for different requests."""
        app = NexiosApp()
        app.add_middleware(RequestIdMiddleware())

        @app.get("/test")
        async def handler(request, response):
            return {"message": "Hello, World!"}

        with test_client_factory(app) as client:
            resp1 = client.get("/test")
            resp2 = client.get("/test")
            resp3 = client.get("/test")

            request_ids = [
                resp1.headers["X-Request-ID"],
                resp2.headers["X-Request-ID"],
                resp3.headers["X-Request-ID"]
            ]

            # All request IDs should be unique
            assert len(set(request_ids)) == 3

    def test_middleware_extracts_request_id_from_header(self, test_client_factory):
        """Test that middleware extracts request ID from incoming request header."""
        app = NexiosApp()
        app.add_middleware(RequestIdMiddleware())

        @app.get("/test")
        async def handler(request, response):
            return {"message": "Hello, World!"}

        with test_client_factory(app) as client:
            custom_request_id = "550e8400-e29b-41d4-a716-446655440000"
            resp = client.get("/test", headers={"X-Request-ID": custom_request_id})

            assert resp.status_code == 200
            assert resp.headers["X-Request-ID"] == custom_request_id

    def test_middleware_force_generate_ignores_header(self, test_client_factory):
        """Test that force_generate=True ignores incoming request ID header."""
        app = NexiosApp()
        app.add_middleware(RequestIdMiddleware(force_generate=True))

        @app.get("/test")
        async def handler(request, response):
            return {"message": "Hello, World!"}

        with test_client_factory(app) as client:
            custom_request_id = "550e8400-e29b-41d4-a716-446655440000"
            resp = client.get("/test", headers={"X-Request-ID": custom_request_id})

            assert resp.status_code == 200
            assert "X-Request-ID" in resp.headers

            # Should generate new ID, not use the provided one
            assert resp.headers["X-Request-ID"] != custom_request_id

            # Should be valid UUID
            uuid.UUID(resp.headers["X-Request-ID"])

    def test_middleware_custom_header_name(self, test_client_factory):
        """Test middleware with custom header name."""
        app = NexiosApp()
        app.add_middleware(RequestIdMiddleware(header_name="X-Custom-Request-ID"))

        @app.get("/test")
        async def handler(request, response):
            return {"message": "Hello, World!"}

        with test_client_factory(app) as client:
            resp = client.get("/test")

            assert resp.status_code == 200
            assert "X-Custom-Request-ID" in resp.headers
            assert "X-Request-ID" not in resp.headers

            # Should be valid UUID
            uuid.UUID(resp.headers["X-Custom-Request-ID"])

    def test_middleware_custom_header_extraction(self, test_client_factory):
        """Test middleware extracts from custom header name."""
        app = NexiosApp()
        app.add_middleware(RequestIdMiddleware(header_name="X-Custom-Request-ID"))

        @app.get("/test")
        async def handler(request, response):
            return {"message": "Hello, World!"}

        with test_client_factory(app) as client:
            custom_request_id = "550e8400-e29b-41d4-a716-446655440000"
            resp = client.get("/test", headers={"X-Custom-Request-ID": custom_request_id})

            assert resp.status_code == 200
            assert resp.headers["X-Custom-Request-ID"] == custom_request_id

    def test_middleware_stores_in_request_object(self, test_client_factory):
        """Test that middleware stores request ID in request object."""
        app = NexiosApp()
        app.add_middleware(RequestIdMiddleware())

        @app.get("/test")
        async def handler(request, response):
            # Access stored request ID
            stored_request_id = getattr(request.state, "request_id", None)
            return {"stored_request_id": stored_request_id}

        with test_client_factory(app) as client:
            resp = client.get("/test")

            assert resp.status_code == 200
            data = resp.json()

            # Should have stored request ID
            assert "stored_request_id" in data
            assert data["stored_request_id"] is not None

            # Should match header
            assert data["stored_request_id"] == resp.headers["X-Request-ID"]

    def test_middleware_custom_attribute_name(self, test_client_factory):
        """Test middleware with custom request attribute name."""
        app = NexiosApp()
        app.add_middleware(RequestIdMiddleware(request_attribute_name="custom_request_id"))

        @app.get("/test")
        async def handler(request, response):
            # Access stored request ID with custom attribute name
            stored_request_id = getattr(request.state, "custom_request_id", None)
            return {"stored_request_id": stored_request_id}

        with test_client_factory(app) as client:
            resp = client.get("/test")

            assert resp.status_code == 200
            data = resp.json()

            # Should have stored request ID with custom attribute name
            assert "stored_request_id" in data
            assert data["stored_request_id"] is not None

            # Should match header
            assert data["stored_request_id"] == resp.headers["X-Request-ID"]

    def test_middleware_without_response_inclusion(self, test_client_factory):
        """Test middleware without including request ID in response headers."""
        app = NexiosApp()
        app.add_middleware(RequestIdMiddleware(include_in_response=False))

        @app.get("/test")
        async def handler(request, response):
            return {"message": "Hello, World!"}

        with test_client_factory(app) as client:
            resp = client.get("/test")

            assert resp.status_code == 200
            # Request ID should not be in response headers
            assert "X-Request-ID" not in resp.headers

    def test_middleware_without_request_storage(self, test_client_factory):
        """Test middleware without storing request ID in request object."""
        app = NexiosApp()
        app.add_middleware(RequestIdMiddleware(store_in_request=False))

        @app.get("/test")
        async def handler(request, response):
            # Try to access stored request ID
            stored_request_id = getattr(request.state, "request_id", None)
            return {"stored_request_id": stored_request_id}

        with test_client_factory(app) as client:
            resp = client.get("/test")

            assert resp.status_code == 200
            data = resp.json()

            # Should not have stored request ID
            assert data["stored_request_id"] is None

            # But should still be in response header
            assert "X-Request-ID" in resp.headers

    def test_middleware_different_endpoints_different_ids(self, test_client_factory):
        """Test that different endpoints get different request IDs."""
        app = NexiosApp()
        app.add_middleware(RequestIdMiddleware())

        @app.get("/endpoint1")
        async def handler1(request, response):
            return {"endpoint": "1"}

        @app.get("/endpoint2")
        async def handler2(request, response):
            return {"endpoint": "2"}

        with test_client_factory(app) as client:
            resp1 = client.get("/endpoint1")
            resp2 = client.get("/endpoint2")

            assert resp1.headers["X-Request-ID"] != resp2.headers["X-Request-ID"]

    def test_middleware_with_json_response(self, test_client_factory):
        """Test middleware with JSON responses."""
        app = NexiosApp()
        app.add_middleware(RequestIdMiddleware())

        @app.get("/json")
        async def handler(request, response):
            return {"status": "success", "data": [1, 2, 3]}

        with test_client_factory(app) as client:
            resp = client.get("/json")

            assert resp.status_code == 200
            assert resp.headers["content-type"] == "application/json"
            assert "X-Request-ID" in resp.headers

            # Validate UUID format
            uuid.UUID(resp.headers["X-Request-ID"])

    def test_middleware_with_text_response(self, test_client_factory):
        """Test middleware with text responses."""
        app = NexiosApp()
        app.add_middleware(RequestIdMiddleware())

        @app.get("/text")
        async def handler(request, response):
            return "Plain text response"

        with test_client_factory(app) as client:
            resp = client.get("/text")

            assert resp.status_code == 200
            assert "X-Request-ID" in resp.headers

            # Validate UUID format
            uuid.UUID(resp.headers["X-Request-ID"])

    def test_middleware_with_empty_response(self, test_client_factory):
        """Test middleware with empty responses."""
        app = NexiosApp()
        app.add_middleware(RequestIdMiddleware())

        @app.get("/empty")
        async def handler(request, response):
            return ""

        with test_client_factory(app) as client:
            resp = client.get("/empty")

            assert resp.status_code == 200
            assert "X-Request-ID" in resp.headers

            # Validate UUID format
            uuid.UUID(resp.headers["X-Request-ID"])
