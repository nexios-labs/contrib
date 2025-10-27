"""
Integration tests for Request ID middleware using Nexios client.
"""

import pytest

from nexios import NexiosApp
from nexios.testclient import TestClient
from nexios_contrib.request_id import RequestIdMiddleware, RequestId


class TestRequestIdIntegration:
    """Integration tests for Request ID middleware."""

    def test_request_id_generation_and_inclusion(self):
        """Test that request IDs are automatically generated and included in responses."""
        app = NexiosApp()
        app.add_middleware(RequestIdMiddleware())

        @app.get("/api/users")
        async def get_users(request, response):
            return {"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}

        client = TestClient(app)

        # Make a request
        resp = client.get("/api/users")
        assert resp.status_code == 200

        # Check that request ID is in response headers
        assert "X-Request-ID" in resp.headers
        request_id = resp.headers["X-Request-ID"]

        # Validate UUID format
        import uuid
        assert uuid.UUID(request_id) is not None

    def test_request_id_persistence_across_requests(self):
        """Test that each request gets a unique request ID."""
        app = NexiosApp()
        app.add_middleware(RequestIdMiddleware())

        @app.get("/api/data")
        async def get_data(request, response):
            return {"data": "test"}

        client = TestClient(app)

        # Make multiple requests
        resp1 = client.get("/api/data")
        resp2 = client.get("/api/data")
        resp3 = client.get("/api/data")

        # All responses should have request IDs
        assert "X-Request-ID" in resp1.headers
        assert "X-Request-ID" in resp2.headers
        assert "X-Request-ID" in resp3.headers

        # All request IDs should be unique
        request_ids = [resp1.headers["X-Request-ID"], resp2.headers["X-Request-ID"], resp3.headers["X-Request-ID"]]
        assert len(set(request_ids)) == 3

    def test_request_id_extraction_from_headers(self):
        """Test that request ID can be extracted from incoming request headers."""
        app = NexiosApp()
        app.add_middleware(RequestIdMiddleware())

        @app.get("/api/echo")
        async def echo_request_id(request, response):
            return {"request_id": getattr(request.state, "request_id", None)}

        client = TestClient(app)

        # Send request with custom request ID
        custom_request_id = "550e8400-e29b-41d4-a716-446655440000"
        resp = client.get("/api/echo", headers={"X-Request-ID": custom_request_id})

        assert resp.status_code == 200
        assert "X-Request-ID" in resp.headers
        assert resp.headers["X-Request-ID"] == custom_request_id

    def test_request_id_storage_in_request_object(self):
        """Test that request ID is stored in the request object."""
        app = NexiosApp()
        app.add_middleware(RequestIdMiddleware())

        @app.get("/api/request-info")
        async def get_request_info(request, response):
            request_id = getattr(request.state, "request_id", None)
            return {"request_id": request_id}

        client = TestClient(app)

        resp = client.get("/api/request-info")
        assert resp.status_code == 200

        # Check response contains request ID
        data = resp.json()
        assert "request_id" in data
        assert data["request_id"] is not None

        # Check header also contains same request ID
        assert resp.headers["X-Request-ID"] == data["request_id"]

    def test_request_id_with_different_http_methods(self):
        """Test request ID generation with different HTTP methods."""
        app = NexiosApp()
        app.add_middleware(RequestIdMiddleware())

        @app.post("/api/users")
        async def create_user(request, response):
            return {"id": 1, "name": "Alice"}

        @app.put("/api/users/1")
        async def update_user(request, response):
            return {"id": 1, "name": "Alice Updated"}

        @app.delete("/api/users/1")
        async def delete_user(request, response):
            return {"message": "User deleted"}

        client = TestClient(app)

        # Test POST
        resp1 = client.post("/api/users", json={"name": "Alice"})
        assert resp1.status_code == 200
        assert "X-Request-ID" in resp1.headers

        # Test PUT
        resp2 = client.put("/api/users/1", json={"name": "Alice Updated"})
        assert resp2.status_code == 200
        assert "X-Request-ID" in resp2.headers

        # Test DELETE
        resp3 = client.delete("/api/users/1")
        assert resp3.status_code == 200
        assert "X-Request-ID" in resp3.headers

        # All should have unique request IDs
        request_ids = [
            resp1.headers["X-Request-ID"],
            resp2.headers["X-Request-ID"],
            resp3.headers["X-Request-ID"]
        ]
        assert len(set(request_ids)) == 3

    def test_request_id_with_query_parameters(self):
        """Test request ID behavior with query parameters."""
        app = NexiosApp()
        app.add_middleware(RequestIdMiddleware())

        @app.get("/api/search")
        async def search(request, response):
            query = request.query_params.get("q", "")
            return {"query": query, "results": [f"result for {query}"]}

        client = TestClient(app)

        # Same query should produce same response but different request IDs
        resp1 = client.get("/api/search?q=test")
        resp2 = client.get("/api/search?q=test")

        assert resp1.status_code == 200
        assert resp2.status_code == 200
        assert "X-Request-ID" in resp1.headers
        assert "X-Request-ID" in resp2.headers

        # Request IDs should be different even for same query
        assert resp1.headers["X-Request-ID"] != resp2.headers["X-Request-ID"]

    def test_request_id_force_generate_option(self):
        """Test force_generate option always generates new request IDs."""
        app = NexiosApp()
        app.add_middleware(RequestIdMiddleware(force_generate=True))

        @app.get("/api/data")
        async def get_data(request, response):
            return {"data": "test"}

        client = TestClient(app)

        # Send request with custom request ID header
        custom_request_id = "550e8400-e29b-41d4-a716-446655440000"
        resp = client.get("/api/data", headers={"X-Request-ID": custom_request_id})

        assert resp.status_code == 200
        assert "X-Request-ID" in resp.headers

        # Should generate new ID despite custom header due to force_generate=True
        assert resp.headers["X-Request-ID"] != custom_request_id

        # Should be a valid UUID
        import uuid
        assert uuid.UUID(resp.headers["X-Request-ID"]) is not None

    def test_request_id_custom_header_name(self):
        """Test request ID with custom header name."""
        app = NexiosApp()
        app.add_middleware(RequestIdMiddleware(header_name="X-Custom-Request-ID"))

        @app.get("/api/test")
        async def test_endpoint(request, response):
            return {"message": "test"}

        client = TestClient(app)

        resp = client.get("/api/test")
        assert resp.status_code == 200

        # Check custom header name
        assert "X-Custom-Request-ID" in resp.headers
        assert "X-Request-ID" not in resp.headers

        # Should be valid UUID
        import uuid
        assert uuid.UUID(resp.headers["X-Custom-Request-ID"]) is not None

    def test_request_id_without_response_inclusion(self):
        """Test request ID without including in response headers."""
        app = NexiosApp()
        app.add_middleware(RequestIdMiddleware(include_in_response=False))

        @app.get("/api/data")
        async def get_data(request, response):
            return {"data": "test"}

        client = TestClient(app)

        resp = client.get("/api/data")
        assert resp.status_code == 200

        # Request ID should not be in response headers
        assert "X-Request-ID" not in resp.headers

        # But should still be stored in request object
        # We can't directly test this from the client side, but the middleware should still work

    def test_request_id_convenience_function(self):
        """Test RequestId convenience function."""
        app = NexiosApp()
        app.add_middleware(RequestId())

        @app.get("/api/test")
        async def test_endpoint(request, response):
            return {"message": "test"}

        client = TestClient(app)

        resp = client.get("/api/test")
        assert resp.status_code == 200
        assert "X-Request-ID" in resp.headers

        # Should be valid UUID
        import uuid
        assert uuid.UUID(resp.headers["X-Request-ID"]) is not None
