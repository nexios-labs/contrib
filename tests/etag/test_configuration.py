"""
Tests for ETag middleware configuration options.
"""

import pytest

from nexios import NexiosApp
from nexios.testclient import TestClient
from nexios_contrib.etag import ETagMiddleware


class TestETagConfiguration:
    """Test different ETag middleware configurations."""

    def test_weak_etag_configuration(self):
        """Test weak ETag configuration."""
        # Test default (weak=True)
        app1 = NexiosApp()
        app1.add_middleware(ETagMiddleware())

        # Test explicit weak=True
        app2 = NexiosApp()
        app2.add_middleware(ETagMiddleware(weak=True))

        # Test weak=False
        app3 = NexiosApp()
        app3.add_middleware(ETagMiddleware(weak=False))

        @app1.get("/default")
        async def default_handler(request, response):
            return {"data": "test"}

        @app2.get("/explicit-weak")
        async def explicit_weak_handler(request, response):
            return {"data": "test"}

        @app3.get("/strong")
        async def strong_handler(request, response):
            return {"data": "test"}

        client1 = TestClient(app1)
        client2 = TestClient(app2)
        client3 = TestClient(app3)

        resp1 = client1.get("/default")
        resp2 = client2.get("/explicit-weak")
        resp3 = client3.get("/strong")

        # Both default and explicit weak should produce weak ETags
        assert resp1.headers["etag"].startswith('W/"')
        assert resp2.headers["etag"].startswith('W/"')

        # Strong should produce strong ETags
        assert not resp3.headers["etag"].startswith('W/')
        assert resp3.headers["etag"].startswith('"')

    def test_methods_configuration(self):
        """Test methods configuration."""
        # Default methods: GET, HEAD
        app1 = NexiosApp()
        app1.add_middleware(ETagMiddleware())

        # Custom methods including POST
        app2 = NexiosApp()
        app2.add_middleware(ETagMiddleware(methods=["GET", "POST"]))

        # Only HEAD method
        app3 = NexiosApp()
        app3.add_middleware(ETagMiddleware(methods=["HEAD"]))

        @app1.get("/default-get")
        async def default_get_handler(request, response):
            return {"method": "GET"}

        @app1.post("/default-post")
        async def default_post_handler(request, response):
            return {"method": "POST"}

        @app2.post("/custom-post")
        async def custom_post_handler(request, response):
            return {"method": "POST"}

        @app3.head("/head-only")
        async def head_only_handler(request, response):
            return {"method": "HEAD"}

        client1 = TestClient(app1)
        client2 = TestClient(app2)
        client3 = TestClient(app3)

        # Default config: GET should have ETag, POST should not
        resp1 = client1.get("/default-get")
        assert "etag" in resp1.headers

        resp2 = client1.post("/default-post", json={})
        assert "etag" not in resp2.headers

        # Custom config: POST should have ETag
        resp3 = client2.post("/custom-post", json={})
        assert "etag" in resp3.headers

        # HEAD-only config: HEAD should have ETag
        resp4 = client3.head("/head-only")
        assert "etag" in resp4.headers

    def test_override_configuration(self):
        """Test override configuration."""
        # override=False (default)
        app1 = NexiosApp()
        app1.add_middleware(ETagMiddleware(override=False))

        # override=True
        app2 = NexiosApp()
        app2.add_middleware(ETagMiddleware(override=True))

        @app1.get("/no-override")
        async def no_override_handler(request, response):
            response.set_header("etag", '"manual-etag"')
            return {"data": "test"}

        @app2.get("/with-override")
        async def with_override_handler(request, response):
            response.set_header("etag", '"manual-etag"')
            return {"data": "test"}

        client1 = TestClient(app1)
        client2 = TestClient(app2)

        # Without override: should keep manual ETag
        resp1 = client1.get("/no-override")
        assert resp1.headers["etag"] == '"manual-etag"'

        # With override: should use computed ETag
        resp2 = client2.get("/with-override")
        assert resp2.headers["etag"] != '"manual-etag"'
        assert resp2.headers["etag"].startswith('W/"')

    def test_combined_configuration_options(self):
        """Test combined configuration options."""
        app = NexiosApp()
        app.add_middleware(ETagMiddleware(
            weak=False,  # Strong ETags
            methods=["GET", "POST"],  # Include POST
            override=True  # Override manual ETags
        ))

        @app.get("/get-endpoint")
        async def get_handler(request, response):
            response.set_header("etag", '"manual-etag"')
            return {"method": "GET"}

        @app.post("/post-endpoint")
        async def post_handler(request, response):
            response.set_header("etag", '"manual-etag"')
            return {"method": "POST"}

        client = TestClient(app)

        # GET should use computed strong ETag (override manual)
        resp1 = client.get("/get-endpoint")
        assert not resp1.headers["etag"].startswith('W/')
        assert resp1.headers["etag"] != '"manual-etag"'

        # POST should also use computed strong ETag (override manual)
        resp2 = client.post("/post-endpoint", json={})
        assert not resp2.headers["etag"].startswith('W/')
        assert resp2.headers["etag"] != '"manual-etag"'

    def test_case_insensitive_methods(self):
        """Test that method matching is case insensitive."""
        app = NexiosApp()
        app.add_middleware(ETagMiddleware(methods=["get", "post"]))

        @app.get("/test")
        async def get_handler(request, response):
            return {"method": request.method}

        @app.post("/test")
        async def post_handler(request, response):
            return {"method": request.method}

        client = TestClient(app)

        # GET should have ETag (case insensitive)
        resp1 = client.get("/test")
        assert "etag" in resp1.headers

        # POST should have ETag (case insensitive)
        resp2 = client.post("/test", json={})
        assert "etag" in resp2.headers

    def test_empty_methods_list(self):
        """Test behavior with empty methods list."""
        app = NexiosApp()
        app.add_middleware(ETagMiddleware(methods=[]))

        @app.get("/test")
        async def handler(request, response):
            return {"method": "GET"}

        client = TestClient(app)

        # No methods should be processed
        resp = client.get("/test")
        assert "etag" not in resp.headers

    def test_multiple_methods_list(self):
        """Test with multiple methods in list."""
        app = NexiosApp()
        app.add_middleware(ETagMiddleware(methods=["GET", "HEAD", "OPTIONS"]))

        @app.get("/test")
        async def get_handler(request, response):
            return {"method": "GET"}

        @app.head("/test")
        async def head_handler(request, response):
            return {"method": "HEAD"}

        @app.options("/test")
        async def options_handler(request, response):
            return {"method": "OPTIONS"}

        @app.post("/test")
        async def post_handler(request, response):
            return {"method": "POST"}

        client = TestClient(app)

        # Methods in list should have ETags
        resp1 = client.get("/test")
        assert "etag" in resp1.headers

        resp2 = client.head("/test")
        assert "etag" in resp2.headers

        resp3 = client.options("/test")
        assert "etag" in resp3.headers

        # Methods not in list should not have ETags
        resp4 = client.post("/test", json={})
        assert "etag" not in resp4.headers

    def test_configuration_with_different_response_types(self):
        """Test configuration options with different response types."""
        app = NexiosApp()
        app.add_middleware(ETagMiddleware(weak=False))  # Strong ETags

        @app.get("/json")
        async def json_handler(request, response):
            return {"type": "json"}

        @app.get("/text")
        async def text_handler(request, response):
            return "plain text"

        @app.get("/bytes")
        async def bytes_handler(request, response):
            return b"binary data"

        client = TestClient(app)

        # All should have strong ETags
        resp1 = client.get("/json")
        resp2 = client.get("/text")
        resp3 = client.get("/bytes")

        assert not resp1.headers["etag"].startswith('W/')
        assert not resp2.headers["etag"].startswith('W/')
        assert not resp3.headers["etag"].startswith('W/')

        # All should be different ETags since content is different
        etags = [resp1.headers["etag"], resp2.headers["etag"], resp3.headers["etag"]]
        assert len(set(etags)) == 3  # All different
