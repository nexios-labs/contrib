"""
Integration tests for ETag middleware using Nexios client.
"""

import pytest

from nexios import NexiosApp
from nexios.testclient import TestClient
from nexios_contrib.etag import ETagMiddleware


class TestETagIntegration:
    """Integration tests for ETag middleware."""

    def test_etag_caching_workflow(self):
        """Test complete ETag caching workflow."""
        app = NexiosApp()
        app.add_middleware(ETagMiddleware())

        @app.get("/api/users")
        async def get_users(request, response):
            # Simulate database query
            users = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
            return users

        @app.get("/api/posts")
        async def get_posts(request, response):
            # Simulate dynamic content
            posts = [{"id": 1, "title": "First Post", "content": "Hello World"}]
            return posts

        client = TestClient(app)

        # First request - should get 200 and ETag
        resp1 = client.get("/api/users")
        assert resp1.status_code == 200
        assert "etag" in resp1.headers
        etag1 = resp1.headers["etag"]

        # Second request without If-None-Match - should get 200
        resp2 = client.get("/api/users")
        assert resp2.status_code == 200
        assert resp2.headers["etag"] == etag1

        # Third request with matching If-None-Match - should get 304
        resp3 = client.get("/api/users", headers={"if-none-match": etag1})
        assert resp3.status_code == 304
        assert resp3.headers.get("etag") == etag1

        # Different endpoint should have different ETag
        resp4 = client.get("/api/posts")
        assert resp4.status_code == 200
        assert resp4.headers["etag"] != etag1

    def test_etag_with_json_responses(self):
        """Test ETag with JSON responses."""
        app = NexiosApp()
        app.add_middleware(ETagMiddleware())

        @app.get("/api/data")
        async def get_data(request, response):
            return {"status": "success", "data": [1, 2, 3, 4, 5]}

        client = TestClient(app)

        # Get initial response
        resp1 = client.get("/api/data")
        assert resp1.status_code == 200
        assert resp1.headers["content-type"] == "application/json"
        assert "etag" in resp1.headers

        etag = resp1.headers["etag"]

        # Conditional request should return 304
        resp2 = client.get("/api/data", headers={"if-none-match": etag})
        assert resp2.status_code == 304

    def test_etag_with_different_content_types(self):
        """Test ETag with different response content types."""
        app = NexiosApp()
        app.add_middleware(ETagMiddleware())

        @app.get("/text")
        async def get_text(request, response):
            return "Plain text response"

        @app.get("/html")
        async def get_html(request, response):
            return "<html><body><h1>Hello</h1></body></html>"

        client = TestClient(app)

        # Test text response
        resp1 = client.get("/text")
        assert resp1.status_code == 200
        assert "etag" in resp1.headers
        etag1 = resp1.headers["etag"]

        # Test HTML response
        resp2 = client.get("/html")
        assert resp2.status_code == 200
        assert "etag" in resp2.headers
        etag2 = resp2.headers["etag"]

        # Different content should have different ETags
        assert etag1 != etag2

        # Conditional requests should work for both
        resp3 = client.get("/text", headers={"if-none-match": etag1})
        assert resp3.status_code == 304

        resp4 = client.get("/html", headers={"if-none-match": etag2})
        assert resp4.status_code == 304

    def test_etag_with_query_parameters(self):
        """Test ETag behavior with query parameters."""
        app = NexiosApp()
        app.add_middleware(ETagMiddleware())

        @app.get("/api/search")
        async def search(request, response):
            query = request.query_params.get("q", "")
            results = {"query": query, "results": [f"result for {query}"]}
            return results

        client = TestClient(app)

        # Same query should produce same ETag
        resp1 = client.get("/api/search?q=test")
        resp2 = client.get("/api/search?q=test")
        assert resp1.headers["etag"] == resp2.headers["etag"]

        # Different queries should produce different ETags
        resp3 = client.get("/api/search?q=different")
        assert resp1.headers["etag"] != resp3.headers["etag"]

        # Conditional request should work
        etag = resp1.headers["etag"]
        resp4 = client.get("/api/search?q=test", headers={"if-none-match": etag})
        assert resp4.status_code == 304

    def test_etag_with_post_requests_disabled(self):
        """Test that ETag middleware doesn't apply to POST by default."""
        app = NexiosApp()
        app.add_middleware(ETagMiddleware())

        @app.post("/api/users")
        async def create_user(request, response):
            return {"id": 1, "name": "Alice"}

        client = TestClient(app)

        resp = client.post("/api/users", json={"name": "Alice"})
        assert resp.status_code == 200
        # Should not have ETag header for POST
        assert "etag" not in resp.headers

    def test_etag_with_post_requests_enabled(self):
        """Test ETag middleware with POST requests when enabled."""
        app = NexiosApp()
        app.add_middleware(ETagMiddleware(methods=["GET", "POST"]))

        @app.post("/api/users")
        async def create_user(request, response):
            return {"id": 1, "name": "Alice"}

        client = TestClient(app)

        resp = client.post("/api/users", json={"name": "Alice"})
        assert resp.status_code == 200
        # Should have ETag header for POST when enabled
        assert "etag" in resp.headers

    def test_etag_override_behavior(self):
        """Test ETag override behavior."""
        app = NexiosApp()

        # Test without override (default)
        app.add_middleware(ETagMiddleware(override=False))

        @app.get("/no-override")
        async def handler_no_override(request, response):
            response.set_header("etag", '"manual-etag"')
            return {"data": "test"}

        

        client = TestClient(app)

        # Without override - should keep manual ETag
        resp1 = client.get("/no-override")
        assert resp1.headers["etag"] == '"manual-etag"'

       

    def test_etag_strong_vs_weak(self):
        """Test strong vs weak ETag generation."""
        weak_app = NexiosApp()
        weak_app.add_middleware(ETagMiddleware(weak=True))

        strong_app = NexiosApp()
        strong_app.add_middleware(ETagMiddleware(weak=False))

        @weak_app.get("/weak")
        async def weak_handler(request, response):
            return {"data": "test"}

        @strong_app.get("/strong")
        async def strong_handler(request, response):
            return {"data": "test"}

        weak_client = TestClient(weak_app)
        strong_client = TestClient(strong_app)

        weak_resp = weak_client.get("/weak")
        strong_resp = strong_client.get("/strong")

        # Weak ETag should start with W/
        assert weak_resp.headers["etag"].startswith('W/"')

        # Strong ETag should not start with W/
        assert not strong_resp.headers["etag"].startswith('W/')
        assert strong_resp.headers["etag"].startswith('"')

        # Weak comparison should work between weak and strong
        weak_etag = weak_resp.headers["etag"]
        strong_etag = strong_resp.headers["etag"]

        # Both should match when using weak comparison
        resp1 = weak_client.get("/weak", headers={"if-none-match": strong_etag})
        assert resp1.status_code == 304

        resp2 = strong_client.get("/strong", headers={"if-none-match": weak_etag})
        assert resp2.status_code == 304
