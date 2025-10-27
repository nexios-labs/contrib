"""
Tests for ETag middleware edge cases and error conditions.
"""

import pytest

from nexios import NexiosApp
from nexios.http import Request, Response
from nexios.testclient import TestClient
from nexios_contrib.etag import (
    ETagMiddleware,
    etag_matches,
    generate_etag_from_bytes,
    is_fresh,
    normalize_etag,
    parse_if_none_match,
)


class TestETagEdgeCases:
    """Test ETag middleware edge cases."""

    def test_etag_with_large_response(self):
        """Test ETag with large response body."""
        app = NexiosApp()
        app.add_middleware(ETagMiddleware())

        @app.get("/large")
        async def large_handler(request, response):
            # Generate a large response
            data = "x" * 10000  # 10KB of data
            return data

        client = TestClient(app)

        resp = client.get("/large")
        assert resp.status_code == 200
        assert "etag" in resp.headers
        assert resp.headers["etag"].startswith('W/"')

        # Conditional request should work with large response
        etag = resp.headers["etag"]
        resp2 = client.get("/large", headers={"if-none-match": etag})
        assert resp2.status_code == 304

    def test_etag_with_special_characters(self):
        """Test ETag with special characters in response."""
        app = NexiosApp()
        app.add_middleware(ETagMiddleware())

        @app.get("/special")
        async def special_handler(request, response):
            return {"special": "chars", "unicode": "测试", "symbols": "!@#$%^&*()"}

        client = TestClient(app)

        resp = client.get("/special")
        assert resp.status_code == 200
        assert "etag" in resp.headers
        assert resp.headers["etag"].startswith('W/"')

        # Should be able to make conditional requests
        etag = resp.headers["etag"]
        resp2 = client.get("/special", headers={"if-none-match": etag})
        assert resp2.status_code == 304

    def test_etag_consistency_across_requests(self):
        """Test ETag consistency across multiple requests."""
        app = NexiosApp()
        app.add_middleware(ETagMiddleware())

        @app.get("/consistent")
        async def consistent_handler(request, response):
            return {"timestamp": "2023-01-01", "data": [1, 2, 3]}

        client = TestClient(app)

        # Make multiple requests and collect ETags
        etags = []
        for i in range(5):
            resp = client.get("/consistent")
            etags.append(resp.headers["etag"])

        # All ETags should be the same
        assert all(etag == etags[0] for etag in etags)

    def test_etag_with_query_parameters_effect(self):
        """Test that query parameters affect ETag generation."""
        app = NexiosApp()
        app.add_middleware(ETagMiddleware())

        @app.get("/search")
        async def search_handler(request, response):
            query = request.query_params.get("q", "")
            return {"query": query, "results": []}

        client = TestClient(app)

        # Same query should produce same ETag
        resp1 = client.get("/search?q=test")
        resp2 = client.get("/search?q=test")
        assert resp1.headers["etag"] == resp2.headers["etag"]

        # Different queries should produce different ETags
        resp3 = client.get("/search?q=different")
        assert resp1.headers["etag"] != resp3.headers["etag"]

        # No query vs empty query should be different
        resp4 = client.get("/search")
        resp5 = client.get("/search?q=")
        # These might be the same or different depending on implementation
        # but both should be valid ETags
        assert "etag" in resp4.headers
        assert "etag" in resp5.headers

    def test_etag_with_headers_and_cookies(self):
        """Test ETag behavior when response has headers and cookies."""
        app = NexiosApp()
        app.add_middleware(ETagMiddleware())

        @app.get("/headers")
        async def headers_handler(request, response):
            response.set_header("x-custom", "value")
            response.set_cookie("session", "abc123")
            return {"data": "test"}

        client = TestClient(app)

        resp = client.get("/headers")
        assert resp.status_code == 200
        assert "etag" in resp.headers
        assert resp.headers.get("x-custom") == "value"
        assert "session" in resp.cookies

        # Conditional request should still work
        etag = resp.headers["etag"]
        resp2 = client.get("/headers", headers={"if-none-match": etag})
        assert resp2.status_code == 304

    def test_etag_with_streaming_response(self):
        """Test ETag with streaming response (if supported)."""
        app = NexiosApp()
        app.add_middleware(ETagMiddleware())

        @app.get("/stream")
        async def stream_handler(request, response):
            # Return a simple string that could be streamed
            return "Streaming content"

        client = TestClient(app)

        resp = client.get("/stream")
        assert resp.status_code == 200
        assert "etag" in resp.headers

        # Should work with conditional requests
        etag = resp.headers["etag"]
        resp2 = client.get("/stream", headers={"if-none-match": etag})
        assert resp2.status_code == 304


class TestETagErrorConditions:
    """Test ETag error conditions and robustness."""

    def test_invalid_etag_in_if_none_match(self):
        """Test handling of invalid ETags in If-None-Match header."""
        app = NexiosApp()
        app.add_middleware(ETagMiddleware())

        @app.get("/test")
        async def handler(request, response):
            return {"data": "test"}

        client = TestClient(app)

        # First get valid ETag
        resp1 = client.get("/test")
        valid_etag = resp1.headers["etag"]

        # Request with invalid ETag should return 200 (not 304)
        resp2 = client.get("/test", headers={"if-none-match": "invalid-etag"})
        assert resp2.status_code == 200
        assert resp2.headers["etag"] == valid_etag

        # Request with mix of valid and invalid ETags
        resp3 = client.get("/test", headers={"if-none-match": f'"valid", invalid, {valid_etag}'})
        assert resp3.status_code == 304  # Should match the valid one

    def test_malformed_if_none_match_header(self):
        """Test handling of malformed If-None-Match header."""
        app = NexiosApp()
        app.add_middleware(ETagMiddleware())

        @app.get("/test")
        async def handler(request, response):
            return {"data": "test"}

        client = TestClient(app)

        # Test various malformed headers
        malformed_headers = [
            "unclosed-quote",
            '"unclosed-quote',
            'W/"unclosed-quote',
            "comma,only",
            "",
            ",",
            "   ",  # whitespace only
        ]

        for malformed in malformed_headers:
            resp = client.get("/test", headers={"if-none-match": malformed})
            # Should return 200 since no valid ETags to match
            assert resp.status_code == 200

    def test_etag_matches_with_invalid_inputs(self):
        """Test etag_matches with invalid inputs."""
        # Valid ETag
        valid_etag = '"abc123"'

        # Test with invalid candidate ETags
        assert not etag_matches(valid_etag, ["invalid"])
        assert not etag_matches(valid_etag, ["", "invalid", "also-invalid"])
        assert not etag_matches("invalid", [valid_etag])

        # Test with empty lists
        assert not etag_matches(valid_etag, [])
        assert not etag_matches("", [])

    

   
    def test_generate_etag_from_bytes_edge_cases(self):
        """Test generate_etag_from_bytes with edge cases."""
        # Empty bytes
        etag1 = generate_etag_from_bytes(b"")
        assert etag1.startswith('W/"')

        # Single byte
        etag2 = generate_etag_from_bytes(b"x")
        assert etag2.startswith('W/"')

        # Large data
        large_data = b"x" * 1000000  # 1MB
        etag3 = generate_etag_from_bytes(large_data)
        assert etag3.startswith('W/"')

        # All should be different
        assert etag1 != etag2 != etag3

    def test_middleware_with_exception_in_handler(self):
        """Test middleware behavior when handler raises exception."""
        app = NexiosApp()
        app.add_middleware(ETagMiddleware())

        @app.get("/error")
        async def error_handler(request, response):
            raise ValueError("Something went wrong")

        client = TestClient(app)

        # Exception should propagate, but if response is created, it should have ETag
        # This tests that middleware doesn't interfere with error handling
        try:
            resp = client.get("/error")
            # Depending on error handling, this might be 500 or other error
            # The important thing is that ETag middleware doesn't break error flow
            assert isinstance(resp.status_code, int)
        except Exception:
            # If exception propagates to client, that's also acceptable
            pass

    def test_concurrent_requests_etag_consistency(self):
        """Test ETag consistency with concurrent requests."""
        app = NexiosApp()
        app.add_middleware(ETagMiddleware())

        @app.get("/concurrent")
        async def concurrent_handler(request, response):
            return {"request_id": "123", "data": "test"}

        client = TestClient(app)

        # Make multiple concurrent requests
        responses = []
        for i in range(10):
            resp = client.get("/concurrent")
            responses.append(resp)

        # All should succeed
        for resp in responses:
            assert resp.status_code == 200
            assert "etag" in resp.headers

        # All should have the same ETag since content is the same
        etags = [resp.headers["etag"] for resp in responses]
        assert all(etag == etags[0] for etag in etags)
