"""
Tests for nexios_contrib.accepts.middleware module.
"""
import pytest
from nexios.http import Request, Response
from nexios_contrib.accepts.middleware import (
    AcceptsMiddleware,
    Accepts,
    ContentNegotiationMiddleware,
    StrictContentNegotiationMiddleware,
)


class MockCallNext:
    """Mock for the call_next function."""

    def __init__(self, return_value=None):
        self.return_value = return_value or Response()

    async def __call__(self):
        return self.return_value


class TestAcceptsMiddleware:
    """Tests for AcceptsMiddleware class."""

    async def test_process_request_without_accepts_info(self):
        """Test processing request without storing accepts info."""
        middleware = AcceptsMiddleware(store_accepts_info=False)

        class MockRequest:
            def __init__(self):
                self.headers = {'Accept': 'text/html'}

        class MockResponse:
            def __init__(self):
                self.headers = {}

            def set_header(self, key, value):
                self.headers[key] = value

        request = MockRequest()
        response = MockResponse()
        call_next = MockCallNext(response)

        result = await middleware.process_request(request, response, call_next)

        assert result == response
        # Should not have accepts attribute on request
        assert not hasattr(request, 'accepts')

    async def test_process_request_with_accepts_info(self):
        """Test processing request with accepts info stored."""
        middleware = AcceptsMiddleware(store_accepts_info=True)

        class MockRequest:
            def __init__(self):
                self.headers = {'Accept': 'text/html'}

        class MockResponse:
            def __init__(self):
                self.headers = {}

            def set_header(self, key, value):
                self.headers[key] = value

        request = MockRequest()
        response = MockResponse()
        call_next = MockCallNext(response)

        result = await middleware.process_request(request, response, call_next)

        assert result == response
        # Should have accepts attribute on request
        assert hasattr(request, 'accepts')
        assert 'accept' in request.accepts

    async def test_process_request_sets_vary_header(self):
        """Test that vary header is set when requested."""
        middleware = AcceptsMiddleware(set_vary_header=True)

        class MockRequest:
            def __init__(self):
                self.headers = {'Accept': 'text/html', 'Accept-Language': 'en'}

        class MockResponse:
            def __init__(self):
                self.headers = {}

            def get(self, key):
                return self.headers.get(key)

            def set_header(self, key, value):
                self.headers[key] = value

        request = MockRequest()
        response = MockResponse()
        call_next = MockCallNext(response)

        result = await middleware.process_request(request, response, call_next)

        assert result == response
        assert 'Vary' in response.headers
        assert 'Accept' in response.headers['Vary']
        assert 'Accept-Language' in response.headers['Vary']

    async def test_process_response_sets_content_type(self):
        """Test that content type is set in response processing."""
        middleware = AcceptsMiddleware(default_content_type='application/json')

        class MockRequest:
            def __init__(self):
                self.headers = {'Accept': 'text/html'}

        class MockResponse:
            def __init__(self):
                self.headers = {}

            def get(self, key):
                return self.headers.get(key)

            def set_header(self, key, value):
                self.headers[key] = value

        request = MockRequest()
        response = MockResponse()

        result = await middleware.process_response(request, response)

        assert result == response
        assert response.headers['Content-Type'] == 'application/json'

    async def test_process_response_preserves_existing_content_type(self):
        """Test that existing content type is preserved."""
        middleware = AcceptsMiddleware(default_content_type='application/json')

        class MockRequest:
            def __init__(self):
                self.headers = {}

        class MockResponse:
            def __init__(self):
                self.headers = {'Content-Type': 'text/html'}

            def get(self, key):
                return self.headers.get(key)

            def set_header(self, key, value):
                self.headers[key] = value

        request = MockRequest()
        response = MockResponse()

        result = await middleware.process_response(request, response)

        assert result == response
        assert response.headers['Content-Type'] == 'text/html'


class TestAccepts:
    """Tests for Accepts convenience function."""

    def test_accepts_function_returns_middleware(self):
        """Test that Accepts function returns middleware instance."""
        middleware = Accepts()
        assert isinstance(middleware, AcceptsMiddleware)

    def test_accepts_function_with_parameters(self):
        """Test that Accepts function passes parameters correctly."""
        middleware = Accepts(
            default_content_type='text/plain',
            default_language='fr',
            set_vary_header=False
        )
        assert isinstance(middleware, AcceptsMiddleware)
        assert middleware.default_content_type == 'text/plain'
        assert middleware.default_language == 'fr'
        assert middleware.set_vary_header is False


class TestContentNegotiationMiddleware:
    """Tests for ContentNegotiationMiddleware class."""

    async def test_negotiate_content_type_method(self):
        """Test content type negotiation method."""
        middleware = ContentNegotiationMiddleware()

        class MockRequest:
            def __init__(self):
                self.headers = {'Accept': 'text/html'}

        request = MockRequest()
        result = middleware.negotiate_content_type(request, ['text/html', 'application/json'])
        assert result == 'text/html'

    async def test_negotiate_language_method(self):
        """Test language negotiation method."""
        middleware = ContentNegotiationMiddleware()

        class MockRequest:
            def __init__(self):
                self.headers = {'Accept-Language': 'en-US'}

        request = MockRequest()
        result = middleware.negotiate_language(request, ['en-US', 'fr-FR'])
        assert result == 'en-US'

    async def test_get_accepted_types_method(self):
        """Test getting accepted types method."""
        middleware = ContentNegotiationMiddleware()

        class MockRequest:
            def __init__(self):
                self.headers = {'Accept': 'text/html, application/json;q=0.8'}

        request = MockRequest()
        # Mock the accepts attribute
        from nexios_contrib.accepts.helper import parse_accept_header
        request.accepts = {
            'accept': parse_accept_header('text/html, application/json;q=0.8')
        }

        result = middleware.get_accepted_types(request)
        assert 'text/html' in result
        assert 'application/json' in result

    async def test_get_accepted_languages_method(self):
        """Test getting accepted languages method."""
        middleware = ContentNegotiationMiddleware()

        class MockRequest:
            def __init__(self):
                self.headers = {'Accept-Language': 'en-US, fr;q=0.8'}

        request = MockRequest()
        # Mock the accepts attribute
        from nexios_contrib.accepts.helper import parse_accept_language
        request.accepts = {
            'accept_language': parse_accept_language('en-US, fr;q=0.8')
        }

        result = middleware.get_accepted_languages(request)
        assert 'en-US' in result
        assert 'fr' in result


class TestStrictContentNegotiationMiddleware:
    """Tests for StrictContentNegotiationMiddleware class."""

    def test_initialization(self):
        """Test strict middleware initialization."""
        middleware = StrictContentNegotiationMiddleware(
            available_types=['application/json', 'text/html'],
            available_languages=['en', 'fr']
        )
        assert middleware.available_types == ['application/json', 'text/html']
        assert middleware.available_languages == ['en', 'fr']

    async def test_process_request_strict_negotiation_success(self):
        """Test strict negotiation when client accepts available type."""
        middleware = StrictContentNegotiationMiddleware(
            available_types=['application/json', 'text/html']
        )

        class MockRequest:
            def __init__(self):
                self.headers = {'Accept': 'application/json'}

        class MockResponse:
            def __init__(self):
                self.status_code = 200
                self.headers = {}

            def status(self, code):
                self.status_code = code

            def set_header(self, key, value):
                self.headers[key] = value

            def get(self, key):
                return self.headers.get(key)

        request = MockRequest()
        response = MockResponse()
        call_next = MockCallNext(response)

        result = await middleware.process_request(request, response, call_next)

        assert result == response
        assert hasattr(request, 'negotiated_content_type')
        assert request.negotiated_content_type == 'application/json'

    async def test_process_request_strict_negotiation_failure(self):
        """Test strict negotiation when client doesn't accept any available type."""
        middleware = StrictContentNegotiationMiddleware(
            available_types=['application/json']
        )

        class MockRequest:
            def __init__(self):
                self.headers = {'Accept': 'text/html'}

        class MockResponse:
            def __init__(self, request):
                self.request = request
                self.status_code = 200
                self.headers = {}

            def status(self, code):
                self.status_code = code

            def set_header(self, key, value):
                self.headers[key] = value

        request = MockRequest()
        response = MockResponse(request)
        call_next = MockCallNext()

        result = await middleware.process_request(request, response, call_next)

        # Should return error response, not call call_next
        assert isinstance(result, dict)
        assert result['error'] == 'Not Acceptable'
        assert result['available_types'] == ['application/json']
