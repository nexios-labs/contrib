"""
Tests for accepts contrib module.
"""
import pytest
from nexios.http import Request, Response
from nexios_contrib.accepts.helper import (
    AcceptItem,
    parse_accept_header,
    parse_accept_language,
    parse_accept_charset,
    parse_accept_encoding,
    negotiate_content_type,
    negotiate_language,
    negotiate_charset,
    negotiate_encoding,
    matches_media_type,
    get_best_match,
    get_accepts_info,
    create_vary_header,
)
from nexios_contrib.accepts.middleware import (
    AcceptsMiddleware,
    Accepts,
    ContentNegotiationMiddleware,
    StrictContentNegotiationMiddleware,
)


class MockRequest:
    def __init__(self, headers=None):
        self.headers = headers or {}


class MockResponse:
    def __init__(self):
        self.headers = {}


def test_accept_item():
    """Test AcceptItem class."""
    item = AcceptItem("text/html", 1.0)
    assert item.value == "text/html"
    assert item.quality == 1.0
    assert item.params == {}

    item_with_params = AcceptItem("application/json", 0.9, {"charset": "utf-8"})
    assert item_with_params.quality == 0.9
    assert item_with_params.params["charset"] == "utf-8"


def test_parse_accept_header():
    """Test Accept header parsing."""
    # Test basic parsing
    items = parse_accept_header("text/html, application/json;q=0.9")
    assert len(items) == 2
    assert items[0].value == "text/html"
    assert items[0].quality == 1.0
    assert items[1].value == "application/json"
    assert items[1].quality == 0.9

    # Test with parameters
    items = parse_accept_header("text/html;level=1;q=0.8, application/json")
    assert len(items) == 2
    assert items[0].value == "text/html;level=1"
    assert items[0].quality == 0.8
    assert items[1].value == "application/json"
    assert items[1].quality == 1.0

    # Test wildcard
    items = parse_accept_header("text/*, */*")
    assert len(items) == 2
    assert items[0].value == "text/*"
    assert items[1].value == "*/*"


def test_parse_accept_language():
    """Test Accept-Language header parsing."""
    items = parse_accept_language("en-US, en;q=0.9, es;q=0.8")
    assert len(items) == 3
    assert items[0].value == "en-US"
    assert items[0].quality == 1.0
    assert items[1].value == "en"
    assert items[1].quality == 0.9
    assert items[2].value == "es"
    assert items[2].quality == 0.8


def test_parse_accept_charset():
    """Test Accept-Charset header parsing."""
    items = parse_accept_charset("utf-8, iso-8859-1;q=0.9")
    assert len(items) == 2
    assert items[0].value == "utf-8"
    assert items[0].quality == 1.0
    assert items[1].value == "iso-8859-1"
    assert items[1].quality == 0.9


def test_parse_accept_encoding():
    """Test Accept-Encoding header parsing."""
    items = parse_accept_encoding("gzip, deflate;q=0.9, br")
    assert len(items) == 3
    assert items[0].value == "gzip"
    assert items[0].quality == 1.0
    assert items[1].value == "br"
    assert items[1].quality == 1.0
    assert items[2].value == "deflate"
    assert items[2].quality == 0.9


def test_negotiate_content_type():
    """Test content type negotiation."""
    # Exact match
    result = negotiate_content_type("text/html", ["text/html", "application/json"])
    assert result == "text/html"

    # Type match
    result = negotiate_content_type("text/*", ["application/json", "text/html"])
    assert result == "text/html"

    # Wildcard match
    result = negotiate_content_type("*/*", ["application/json", "text/html"])
    assert result == "application/json"

    # Quality-based selection
    result = negotiate_content_type("application/json;q=0.8, text/html", ["text/html", "application/json"])
    assert result == "text/html"  # Higher quality wins

    # No match
    result = negotiate_content_type("application/xml", ["application/json", "text/html"])
    assert result is None


def test_negotiate_language():
    """Test language negotiation."""
    # Exact match
    result = negotiate_language("en-US", ["en", "es", "fr"])
    assert result == "en"

    # Prefix match
    result = negotiate_language("en", ["en-US", "en-GB", "es"])
    assert result == "en-US"  # More specific match

    # Quality-based selection
    result = negotiate_language("en;q=0.8, es", ["en", "es", "fr"])
    assert result == "es"  # Higher quality wins


def test_negotiate_charset():
    """Test charset negotiation."""
    result = negotiate_charset("utf-8, iso-8859-1;q=0.9", ["utf-8", "iso-8859-1"])
    assert result == "utf-8"

    result = negotiate_charset("*", ["utf-8", "iso-8859-1"])
    assert result == "utf-8"


def test_negotiate_encoding():
    """Test encoding negotiation."""
    result = negotiate_encoding("gzip, deflate;q=0.9", ["gzip", "deflate", "br"])
    assert result == ["gzip", "deflate"]  # br not in accept header

    result = negotiate_encoding("gzip;q=0.8, *", ["gzip", "deflate"])
    assert result == ["gzip", "deflate"]  # * includes all


def test_matches_media_type():
    """Test media type matching."""
    assert matches_media_type("text/html", "text/html") == True
    assert matches_media_type("text/*", "text/html") == True
    assert matches_media_type("*/*", "application/json") == True
    assert matches_media_type("application/*", "text/html") == False
    assert matches_media_type("text/html", "text/plain") == False


def test_get_best_match():
    """Test best match selection."""
    result = get_best_match("text/html, application/json;q=0.9", ["application/json", "text/html"])
    assert result == "application/json"  # First in options

    result = get_best_match("application/xml", ["application/json", "text/html"])
    assert result == "application/json"  # First in options (no match)


def test_get_accepts_info():
    """Test accepts info extraction."""
    request = MockRequest({
        "Accept": "text/html, application/json",
        "Accept-Language": "en-US, es;q=0.9",
        "Accept-Charset": "utf-8",
        "Accept-Encoding": "gzip"
    })

    info = get_accepts_info(request)

    assert len(info["accept"]) == 2
    assert len(info["accept_language"]) == 2
    assert len(info["accept_charset"]) == 1
    assert len(info["accept_encoding"]) == 1
    assert info["raw_accept"] == "text/html, application/json"


def test_create_vary_header():
    """Test Vary header creation."""
    result = create_vary_header(None, ["Accept", "Accept-Language"])
    assert result == "Accept, Accept-Language"

    result = create_vary_header("Accept", ["Accept-Language", "Accept-Charset"])
    assert result == "Accept, Accept-Language, Accept-Charset"

    result = create_vary_header("Accept, Accept-Language", ["Accept-Language"])
    assert result == "Accept, Accept-Language"  # No duplicates


def test_accepts_middleware():
    """Test AcceptsMiddleware functionality."""
    middleware = AcceptsMiddleware()

    request = MockRequest({"Accept": "application/json"})
    response = MockResponse()

    # Test middleware initialization
    assert middleware.default_content_type == "application/json"
    assert middleware.set_vary_header == True
    assert middleware.store_accepts_info == True


def test_accepts_convenience_function():
    """Test Accepts convenience function."""
    middleware = Accepts(
        default_content_type="application/xml",
        set_vary_header=False
    )

    assert middleware.default_content_type == "application/xml"
    assert middleware.set_vary_header == False


def test_content_negotiation_middleware():
    """Test ContentNegotiationMiddleware functionality."""
    middleware = ContentNegotiationMiddleware()

    request = MockRequest({"Accept": "text/html"})

    best_type = middleware.negotiate_content_type(
        request,
        ["text/html", "application/json"]
    )
    assert best_type == "text/html"

    languages = middleware.get_accepted_types(request)
    assert "text/html" in languages


def test_strict_content_negotiation_middleware():
    """Test StrictContentNegotiationMiddleware functionality."""
    middleware = StrictContentNegotiationMiddleware(
        available_types=["application/json", "application/xml"],
        available_languages=["en", "es"]
    )

    assert middleware.available_types == ["application/json", "application/xml"]
    assert middleware.available_languages == ["en", "es"]


if __name__ == "__main__":
    # Run basic tests
    test_accept_item()
    test_parse_accept_header()
    test_parse_accept_language()
    test_parse_accept_charset()
    test_parse_accept_encoding()
    test_negotiate_content_type()
    test_negotiate_language()
    test_negotiate_charset()
    test_negotiate_encoding()
    test_matches_media_type()
    test_get_best_match()
    test_get_accepts_info()
    test_create_vary_header()
    test_accepts_middleware()
    test_accepts_convenience_function()
    test_content_negotiation_middleware()
    test_strict_content_negotiation_middleware()
    print("All accepts tests passed!")
