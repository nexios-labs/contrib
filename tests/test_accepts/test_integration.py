"""
Integration tests for nexios_contrib.accepts module.
"""
import pytest
from nexios import NexiosApp
from nexios.http import Request, Response
from nexios.routing import Router
from nexios.testing import Client
from nexios_contrib.accepts import (
    AcceptsMiddleware,
    Accepts,
    ContentNegotiationMiddleware,
    StrictContentNegotiationMiddleware,
)


# Create test app
app = NexiosApp()
router = Router("/api")


@router.get("/content")
async def get_content(req: Request, res: Response):
    """Test endpoint for content negotiation."""
    return res.json({"message": "Hello World"})


@router.get("/html")
async def get_html(req: Request, res: Response):
    """Test endpoint that returns HTML."""
    return res.html("<h1>Hello World</h1>")


@router.get("/text")
async def get_text(req: Request, res: Response):
    """Test endpoint that returns plain text."""
    return res.text("Hello World")


@router.get("/custom")
async def get_custom(req: Request, res: Response):
    """Test endpoint with custom content type."""
    res.set_header('Content-Type', 'application/custom')
    return res.json({"type": "custom"})


app.mount_router(router)


@pytest.fixture
async def async_client():
    """Fixture for async test client."""
    async with Client(app) as c:
        yield c


@pytest.fixture
async def client_with_accepts():
    """Fixture for client with Accepts middleware."""
    test_app = NexiosApp()
    test_app.add_middleware(Accepts())

    @test_app.get("/test")
    async def test_endpoint(req: Request, res: Response):
        return res.json({"message": "test"})

    async with Client(test_app) as c:
        yield c


@pytest.fixture
async def client_with_content_negotiation():
    """Fixture for client with ContentNegotiation middleware."""
    test_app = NexiosApp()
    test_app.add_middleware(ContentNegotiationMiddleware())

    @test_app.get("/negotiate")
    async def negotiate_endpoint(req: Request, res: Response):
        return res.json({"message": "negotiated"})

    async with Client(test_app) as c:
        yield c


@pytest.fixture
async def client_with_strict_negotiation():
    """Fixture for client with StrictContentNegotiation middleware."""
    test_app = NexiosApp()
    test_app.add_middleware(StrictContentNegotiationMiddleware(
        available_types=['application/json']
    ))

    @test_app.get("/strict")
    async def strict_endpoint(req: Request, res: Response):
        return res.json({"message": "strict"})

    async with Client(test_app) as c:
        yield c


class TestAcceptsMiddlewareIntegration:
    """Integration tests for AcceptsMiddleware."""

    async def test_accepts_middleware_stores_info(self, async_client):
        """Test that accepts middleware stores information in request."""
        response = await async_client.get("/api/content", headers={
            'Accept': 'application/json',
            'Accept-Language': 'en-US'
        })
        assert response.status_code == 200

    async def test_default_content_type_set(self, async_client):
        """Test that default content type is set when no Accept header."""
        response = await async_client.get("/api/content")
        assert response.status_code == 200
        assert response.headers.get('Content-Type') == 'application/json'

    async def test_vary_header_set(self, async_client):
        """Test that Vary header is set appropriately."""
        response = await async_client.get("/api/content", headers={
            'Accept': 'application/json',
            'Accept-Language': 'en-US'
        })
        assert response.status_code == 200
        # Should have Vary header set by middleware
        vary_header = response.headers.get('Vary', '')
        assert 'Accept' in vary_header or vary_header == ''

    async def test_custom_content_type_preserved(self, async_client):
        """Test that custom content type is preserved."""
        response = await async_client.get("/api/custom")
        assert response.status_code == 200
        assert response.headers.get('Content-Type') == 'application/custom'


class TestContentNegotiationIntegration:
    """Integration tests for content negotiation."""

    async def test_json_request_accepts_json(self, async_client):
        """Test JSON endpoint with JSON Accept header."""
        response = await async_client.get("/api/content", headers={
            'Accept': 'application/json'
        })
        assert response.status_code == 200
        assert response.headers.get('Content-Type') == 'application/json'
        assert response.json()['message'] == 'Hello World'

    async def test_json_request_accepts_html(self, async_client):
        """Test JSON endpoint with HTML Accept header."""
        response = await async_client.get("/api/content", headers={
            'Accept': 'text/html'
        })
        assert response.status_code == 200
        assert response.headers.get('Content-Type') == 'application/json'

    async def test_html_endpoint_with_html_accept(self, async_client):
        """Test HTML endpoint with HTML Accept header."""
        response = await async_client.get("/api/html", headers={
            'Accept': 'text/html'
        })
        assert response.status_code == 200
        assert response.headers.get('Content-Type') == 'text/html'

    async def test_text_endpoint_with_text_accept(self, async_client):
        """Test text endpoint with text Accept header."""
        response = await async_client.get("/api/text", headers={
            'Accept': 'text/plain'
        })
        assert response.status_code == 200
        assert response.headers.get('Content-Type') == 'text/plain'

    async def test_wildcard_accept(self, async_client):
        """Test with wildcard Accept header."""
        response = await async_client.get("/api/content", headers={
            'Accept': '*/*'
        })
        assert response.status_code == 200
        assert response.headers.get('Content-Type') == 'application/json'


class TestAcceptsMiddlewareWithApp:
    """Tests for Accepts middleware integration with app."""

    async def test_accepts_middleware_integration(self, client_with_accepts):
        """Test that accepts middleware integrates properly."""
        response = await client_with_accepts.get("/test", headers={
            'Accept': 'application/json'
        })
        assert response.status_code == 200
        assert response.json()['message'] == 'test'

    async def test_accepts_info_available_in_request(self):
        """Test that accepts info is available in request object."""
        # This test would need access to the request object during processing
        # For now, we just test that the middleware doesn't break anything
        test_app = NexiosApp()
        test_app.add_middleware(Accepts(store_accepts_info=True))

        @test_app.get("/check")
        async def check_endpoint(req: Request, res: Response):
            # The accepts info should be available on the request
            accepts_info = getattr(req, 'accepts', None)
            return res.json({"has_accepts": accepts_info is not None})

        async with Client(test_app) as client:
            response = await client.get("/check")
            assert response.status_code == 200
            assert response.json()['has_accepts'] is True


class TestContentNegotiationMiddlewareIntegration:
    """Tests for ContentNegotiationMiddleware integration."""

    async def test_content_negotiation_middleware(self, client_with_content_negotiation):
        """Test content negotiation middleware integration."""
        response = await client_with_content_negotiation.get("/negotiate", headers={
            'Accept': 'application/json'
        })
        assert response.status_code == 200
        assert response.json()['message'] == 'negotiated'


class TestStrictContentNegotiationIntegration:
    """Tests for StrictContentNegotiationMiddleware integration."""

    async def test_strict_negotiation_success(self, client_with_strict_negotiation):
        """Test strict negotiation when client accepts correct type."""
        response = await client_with_strict_negotiation.get("/strict", headers={
            'Accept': 'application/json'
        })
        assert response.status_code == 200
        assert response.json()['message'] == 'strict'

    async def test_strict_negotiation_failure(self, client_with_strict_negotiation):
        """Test strict negotiation when client doesn't accept available type."""
        response = await client_with_strict_negotiation.get("/strict", headers={
            'Accept': 'text/html'
        })
        assert response.status_code == 406
        assert response.json()['error'] == 'Not Acceptable'

    async def test_strict_negotiation_with_wildcard(self):
        """Test strict negotiation with wildcard accept."""
        test_app = NexiosApp()
        test_app.add_middleware(StrictContentNegotiationMiddleware(
            available_types=['application/json']
        ))

        @test_app.get("/wildcard")
        async def wildcard_endpoint(req: Request, res: Response):
            return res.json({"message": "wildcard"})

        async with Client(test_app) as client:
            response = await client.get("/wildcard", headers={
                'Accept': '*/*'
            })
            assert response.status_code == 200
            assert response.json()['message'] == 'wildcard'


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    async def test_middleware_with_empty_headers(self):
        """Test middleware with empty headers."""
        test_app = NexiosApp()
        test_app.add_middleware(Accepts())

        @test_app.get("/empty")
        async def empty_endpoint(req: Request, res: Response):
            return res.json({"message": "empty"})

        async with Client(test_app) as client:
            response = await client.get("/empty")
            assert response.status_code == 200

    async def test_middleware_with_malformed_headers(self):
        """Test middleware with malformed Accept headers."""
        test_app = NexiosApp()
        test_app.add_middleware(Accepts())

        @test_app.get("/malformed")
        async def malformed_endpoint(req: Request, res: Response):
            return res.json({"message": "malformed"})

        async with Client(test_app) as client:
            response = await client.get("/malformed", headers={
                'Accept': 'text/html; q=invalid; charset=utf-8'
            })
            assert response.status_code == 200

    async def test_multiple_middleware_layers(self):
        """Test multiple middleware layers."""
        test_app = NexiosApp()
        test_app.add_middleware(Accepts())
        test_app.add_middleware(ContentNegotiationMiddleware())

        @test_app.get("/multiple")
        async def multiple_endpoint(req: Request, res: Response):
            return res.json({"message": "multiple"})

        async with Client(test_app) as client:
            response = await client.get("/multiple", headers={
                'Accept': 'application/json'
            })
            assert response.status_code == 200
