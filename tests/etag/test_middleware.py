"""
Tests for ETagMiddleware.
"""

import pytest

from nexios import NexiosApp
from nexios.http import Request, Response
from nexios.testclient import TestClient
from nexios_contrib.etag import ETagMiddleware


class TestETagMiddleware:
    """Test ETagMiddleware functionality."""

    def test_middleware_sets_etag_on_get(self, test_client_factory):
        """Test that middleware sets ETag on GET requests."""
        app = NexiosApp()
        app.add_middleware(ETagMiddleware())

        @app.get("/test")
        async def handler(request, response):
            return {"message": "Hello, World!"}

        with test_client_factory(app) as client:
            resp = client.get("/test")
            assert resp.status_code == 200
            assert "etag" in resp.headers
            assert resp.headers["etag"].startswith('W/"')

    def test_middleware_sets_etag_on_head(self, test_client_factory):
        """Test that middleware sets ETag on HEAD requests."""
        app = NexiosApp()
        app.add_middleware(ETagMiddleware())

        @app.head("/test")
        async def handler(request, response):
            return {"message": "Hello, World!"}

        with test_client_factory(app) as client:
            resp = client.head("/test")
            assert resp.status_code == 200
            assert "etag" in resp.headers
            assert resp.headers["etag"].startswith('W/"')

    def test_middleware_ignores_post(self, test_client_factory):
        """Test that middleware ignores POST requests by default."""
        app = NexiosApp()
        app.add_middleware(ETagMiddleware())

        @app.post("/test")
        async def handler(request, response):
            return {"message": "Hello, World!"}

        with test_client_factory(app) as client:
            resp = client.post("/test", json={"data": "test"})
            assert resp.status_code == 200
            assert "etag" not in resp.headers

    def test_middleware_custom_methods(self, test_client_factory):
        """Test middleware with custom methods."""
        app = NexiosApp()
        app.add_middleware(ETagMiddleware(methods=["GET", "POST"]))

        @app.post("/test")
        async def handler(request, response):
            return {"message": "Hello, World!"}

        with test_client_factory(app) as client:
            resp = client.post("/test", json={"data": "test"})
            assert resp.status_code == 200
            assert "etag" in resp.headers

    def test_middleware_weak_etag_default(self, test_client_factory):
        """Test that middleware generates weak ETags by default."""
        app = NexiosApp()
        app.add_middleware(ETagMiddleware())

        @app.get("/test")
        async def handler(request, response):
            return {"message": "Hello, World!"}

        with test_client_factory(app) as client:
            resp = client.get("/test")
            assert resp.headers["etag"].startswith('W/"')

    def test_middleware_strong_etag(self, test_client_factory):
        """Test middleware with strong ETags."""
        app = NexiosApp()
        app.add_middleware(ETagMiddleware(weak=False))

        @app.get("/test")
        async def handler(request, response):
            return {"message": "Hello, World!"}

        with test_client_factory(app) as client:
            resp = client.get("/test")
            assert not resp.headers["etag"].startswith('W/')
            assert resp.headers["etag"].startswith('"')

    def test_middleware_does_not_override_existing_etag(self, test_client_factory):
        """Test that middleware doesn't override existing ETag by default."""
        app = NexiosApp()
        app.add_middleware(ETagMiddleware())

        @app.get("/test")
        async def handler(request, response):
            response.set_header("etag", '"custom-etag"')
            return {"message": "Hello, World!"}

        with test_client_factory(app) as client:
            resp = client.get("/test")
            assert resp.headers["etag"] == '"custom-etag"'

    def test_middleware_overrides_existing_etag(self, test_client_factory):
        """Test that middleware overrides existing ETag when override=True."""
        app = NexiosApp()
        app.add_middleware(ETagMiddleware(override=True))

        @app.get("/test")
        async def handler(request, response):
            response.set_header("etag", '"custom-etag"')
            return {"message": "Hello, World!"}

        with test_client_factory(app) as client:
            resp = client.get("/test")
            assert not resp.headers["etag"] == '"custom-etag"'
            assert resp.headers["etag"].startswith('W/"')

    def test_middleware_consistent_etag(self, test_client_factory):
        """Test that middleware generates consistent ETags for same response."""
        app = NexiosApp()
        app.add_middleware(ETagMiddleware())

        @app.get("/test")
        async def handler(request, response):
            return {"message": "Hello, World!"}

        with test_client_factory(app) as client:
            resp1 = client.get("/test")
            resp2 = client.get("/test")
            assert resp1.headers["etag"] == resp2.headers["etag"]

    def test_middleware_different_etag_for_different_content(self, test_client_factory):
        """Test that different content produces different ETags."""
        app = NexiosApp()
        app.add_middleware(ETagMiddleware())

        @app.get("/test1")
        async def handler1(request, response):
            return {"message": "Hello, World!"}

        @app.get("/test2")
        async def handler2(request, response):
            return {"message": "Hello, World2!"}

        with test_client_factory(app) as client:
            resp1 = client.get("/test1")
            resp2 = client.get("/test2")
            assert resp1.headers["etag"] != resp2.headers["etag"]

    def test_middleware_empty_response(self, test_client_factory):
        """Test middleware with empty response."""
        app = NexiosApp()
        app.add_middleware(ETagMiddleware())

        @app.get("/test")
        async def handler(request, response):
            return ""

        with test_client_factory(app) as client:
            resp = client.get("/test")
            assert resp.status_code == 200
            assert "etag" in resp.headers

    def test_middleware_binary_response(self, test_client_factory):
        """Test middleware with binary response."""
        app = NexiosApp()
        app.add_middleware(ETagMiddleware())

        @app.get("/test")
        async def handler(request, response):
            return b"binary data"

        with test_client_factory(app) as client:
            resp = client.get("/test")
            assert resp.status_code == 200
            assert "etag" in resp.headers


class TestETagMiddlewareConditionalRequests:
    """Test ETagMiddleware conditional request handling."""

    def test_conditional_get_matching_etag(self, test_client_factory):
        """Test conditional GET with matching ETag returns 304."""
        app = NexiosApp()
        app.add_middleware(ETagMiddleware())

        @app.get("/test")
        async def handler(request, response):
            return {"message": "Hello, World!"}

        with test_client_factory(app) as client:
            # First request to get the ETag
            resp1 = client.get("/test")
            etag = resp1.headers["etag"]

            # Second request with If-None-Match
            resp2 = client.get("/test", headers={"if-none-match": etag})
            assert resp2.status_code == 304
            assert resp2.headers.get("etag") == etag

    def test_conditional_get_non_matching_etag(self, test_client_factory):
        """Test conditional GET with non-matching ETag returns 200."""
        app = NexiosApp()
        app.add_middleware(ETagMiddleware())

        @app.get("/test")
        async def handler(request, response):
            return {"message": "Hello, World!"}

        with test_client_factory(app) as client:
            resp = client.get("/test", headers={"if-none-match": '"different-etag"'})
            assert resp.status_code == 200
            assert "etag" in resp.headers

    def test_conditional_get_multiple_etags(self, test_client_factory):
        """Test conditional GET with multiple ETags in If-None-Match."""
        app = NexiosApp()
        app.add_middleware(ETagMiddleware())

        @app.get("/test")
        async def handler(request, response):
            return {"message": "Hello, World!"}

        with test_client_factory(app) as client:
            # First request to get the ETag
            resp1 = client.get("/test")
            etag = resp1.headers["etag"]

            # Second request with multiple ETags including the matching one
            resp2 = client.get("/test", headers={"if-none-match": f'"other-etag", {etag}, "another-etag"'})
            assert resp2.status_code == 304

    def test_conditional_get_weak_etag_match(self, test_client_factory):
        """Test conditional GET with weak ETag matching."""
        app = NexiosApp()
        app.add_middleware(ETagMiddleware())

        @app.get("/test")
        async def handler(request, response):
            return {"message": "Hello, World!"}

        with test_client_factory(app) as client:
            # First request to get the ETag
            resp1 = client.get("/test")
            etag = resp1.headers["etag"]

            # Second request with weak version of same ETag
            weak_etag = etag.replace('W/"', '"') if etag.startswith('W/') else f'W/{etag}'
            resp2 = client.get("/test", headers={"if-none-match": weak_etag})
            assert resp2.status_code == 304

    def test_conditional_head_request(self, test_client_factory):
        """Test conditional HEAD request with matching ETag."""
        app = NexiosApp()
        app.add_middleware(ETagMiddleware())

        @app.head("/test")
        async def handler(request, response):
            return {"message": "Hello, World!"}

        with test_client_factory(app) as client:
            # First request to get the ETag
            resp1 = client.head("/test")
            etag = resp1.headers["etag"]

            # Second request with If-None-Match
            resp2 = client.head("/test", headers={"if-none-match": etag})
            assert resp2.status_code == 304
            assert resp2.headers.get("etag") == etag

    def test_conditional_request_no_etag_on_response(self, test_client_factory):
        """Test conditional request when response has no ETag."""
        app = NexiosApp()
        app.add_middleware(ETagMiddleware())

        @app.get("/test")
        async def handler(request, response):
            # Manually remove any ETag that might be set
            response.remove_header("etag")
            return {"message": "Hello, World!"}

        with test_client_factory(app) as client:
            resp = client.get("/test", headers={"if-none-match": '"some-etag"'})
            # Should return 200 because there's no ETag to match against
            assert resp.status_code == 200
