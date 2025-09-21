"""
Tests for nexios_contrib.accepts.helper module.
"""
import pytest
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


class TestAcceptItem:
    """Tests for AcceptItem class."""

    def test_accept_item_creation(self):
        """Test creating an AcceptItem instance."""
        item = AcceptItem("text/html", 0.9, {"charset": "utf-8"})
        assert item.value == "text/html"
        assert item.quality == 0.9
        assert item.params == {"charset": "utf-8"}

    def test_accept_item_default_params(self):
        """Test AcceptItem with default parameters."""
        item = AcceptItem("application/json")
        assert item.value == "application/json"
        assert item.quality == 1.0
        assert item.params == {}

    def test_accept_item_repr(self):
        """Test AcceptItem string representation."""
        item = AcceptItem("text/html", 0.8)
        assert repr(item) == "AcceptItem(value=text/html, quality=0.8)"


class TestParseAcceptHeader:
    """Tests for parse_accept_header function."""

    def test_parse_empty_header(self):
        """Test parsing empty accept header."""
        result = parse_accept_header("")
        assert result == []

    def test_parse_single_media_type(self):
        """Test parsing single media type."""
        result = parse_accept_header("text/html")
        assert len(result) == 1
        assert result[0].value == "text/html"
        assert result[0].quality == 1.0

    def test_parse_multiple_media_types(self):
        """Test parsing multiple media types."""
        result = parse_accept_header("text/html, application/json")
        assert len(result) == 2
        assert result[1].value == "text/html"
        assert result[0].value == "application/json"

    def test_parse_with_quality_values(self):
        """Test parsing with quality values."""
        result = parse_accept_header("text/html;q=0.8, application/json;q=0.9")
        assert len(result) == 2
        assert result[0].value == "application/json"  # Higher quality first
        assert result[0].quality == 0.9
        assert result[1].value == "text/html"
        assert result[1].quality == 0.8




class TestParseAcceptLanguage:
    """Tests for parse_accept_language function."""

    def test_parse_language_header(self):
        """Test parsing accept language header."""
        result = parse_accept_language("en-US, fr;q=0.8, *;q=0.1")
        assert len(result) == 3
        assert result[0].value == "en-US"
        assert result[0].quality == 1.0
        assert result[1].value == "fr"
        assert result[1].quality == 0.8
        assert result[2].value == "*"
        assert result[2].quality == 0.1


class TestParseAcceptCharset:
    """Tests for parse_accept_charset function."""

    def test_parse_charset_header(self):
        """Test parsing accept charset header."""
        result = parse_accept_charset("utf-8, iso-8859-1;q=0.8")
        assert len(result) == 2
        assert result[0].value == "utf-8"
        assert result[0].quality == 1.0
        assert result[1].value == "iso-8859-1"
        assert result[1].quality == 0.8


class TestParseAcceptEncoding:
    """Tests for parse_accept_encoding function."""

class TestNegotiateContentType:
    """Tests for negotiate_content_type function."""

    def test_negotiate_exact_match(self):
        """Test content negotiation with exact match."""
        result = negotiate_content_type("text/html", ["text/html", "application/json"])
        assert result == "text/html"

    def test_negotiate_wildcard_match(self):
        """Test content negotiation with wildcard match."""
        result = negotiate_content_type("text/*", ["text/html", "application/json"])
        assert result == "text/html"

    def test_negotiate_all_wildcard(self):
        """Test content negotiation with */* wildcard."""
        result = negotiate_content_type("*/*", ["application/json", "text/html"])
        assert result == "application/json"

    def test_negotiate_no_match(self):
        """Test content negotiation with no match."""
        result = negotiate_content_type("image/*", ["text/html", "application/json"])
        assert result is None

    def test_negotiate_empty_available(self):
        """Test content negotiation with empty available types."""
        result = negotiate_content_type("text/html", [])
        assert result is None

    def test_negotiate_empty_accept(self):
        """Test content negotiation with empty accept header."""
        result = negotiate_content_type("", ["text/html", "application/json"])
        assert result == "text/html"


class TestNegotiateLanguage:
    """Tests for negotiate_language function."""

    def test_negotiate_exact_language_match(self):
        """Test language negotiation with exact match."""
        result = negotiate_language("en-US", ["en-US", "fr-FR"])
        assert result == "en-US"

    def test_negotiate_language_prefix_match(self):
        """Test language negotiation with prefix match."""
        result = negotiate_language("en", ["en-US", "fr-FR"])
        assert result == "en-US"

    def test_negotiate_no_match(self):
        """Test language negotiation with no match."""
        result = negotiate_language("de", ["en-US", "fr-FR"])
        assert result == "en-US"  # Returns first available when no match

    def test_negotiate_empty_available(self):
        """Test language negotiation with empty available languages."""
        result = negotiate_language("en", [])
        assert result is None


class TestNegotiateCharset:
    """Tests for negotiate_charset function."""

    def test_negotiate_exact_charset_match(self):
        """Test charset negotiation with exact match."""
        result = negotiate_charset("utf-8", ["utf-8", "iso-8859-1"])
        assert result == "utf-8"

    def test_negotiate_wildcard_charset(self):
        """Test charset negotiation with wildcard."""
        result = negotiate_charset("*", ["utf-8", "iso-8859-1"])
        assert result == "utf-8"

    def test_negotiate_no_match(self):
        """Test charset negotiation with no match."""
        result = negotiate_charset("ascii", ["utf-8", "iso-8859-1"])
        assert result == "utf-8"  # Returns first available when no match


class TestNegotiateEncoding:
    """Tests for negotiate_encoding function."""

    def test_negotiate_identity_encoding(self):
        """Test encoding negotiation with identity."""
        result = negotiate_encoding("identity", ["gzip", "deflate"])
        assert result == ["gzip", "deflate"]

    def test_negotiate_wildcard_encoding(self):
        """Test encoding negotiation with wildcard."""
        result = negotiate_encoding("*", ["gzip", "deflate"])
        assert result == ["gzip", "deflate"]

    def test_negotiate_specific_encoding(self):
        """Test encoding negotiation with specific encoding."""
        result = negotiate_encoding("gzip, deflate", ["gzip", "br"])
        assert result == ["gzip"]

    def test_negotiate_no_match(self):
        """Test encoding negotiation with no match."""
        result = negotiate_encoding("br", ["gzip", "deflate"])
        assert result == []


class TestMatchesMediaType:
    """Tests for matches_media_type function."""

    def test_exact_match(self):
        """Test exact media type match."""
        assert matches_media_type("text/html", "text/html") is True

    def test_wildcard_all_match(self):
        """Test */* wildcard match."""
        assert matches_media_type("*/*", "text/html") is True
        assert matches_media_type("*/*", "application/json") is True

    def test_type_wildcard_match(self):
        """Test type/* wildcard match."""
        assert matches_media_type("text/*", "text/html") is True
        assert matches_media_type("text/*", "text/plain") is True
        assert matches_media_type("text/*", "application/json") is False

    def test_no_match(self):
        """Test no match scenarios."""
        assert matches_media_type("image/*", "text/html") is False
        assert matches_media_type("text/html", "text/plain") is False


class TestGetBestMatch:
    """Tests for get_best_match function."""

    def test_get_best_exact_match(self):
        """Test getting best match with exact match."""
        result = get_best_match("text/html", ["text/html", "application/json"])
        assert result == "text/html"

    def test_get_best_wildcard_match(self):
        """Test getting best match with wildcard."""
        result = get_best_match("text/*", ["text/html", "application/json"])
        assert result == "text/html"

    def test_get_best_no_match(self):
        """Test getting best match with no match."""
        result = get_best_match("image/*", ["text/html", "application/json"])
        assert result == "text/html"  # Returns first option when no match

    def test_get_best_empty_options(self):
        """Test getting best match with empty options."""
        result = get_best_match("text/html", [])
        assert result is None


class TestGetAcceptsInfo:
    """Tests for get_accepts_info function."""

    

    def test_get_accepts_info_with_missing_headers(self):
        """Test getting accepts info with missing headers."""
        class MockRequest:
            def __init__(self):
                self.headers = {}

        request = MockRequest()
        result = get_accepts_info(request)

        assert result['accept'] == []
        assert result['accept_language'] == []
        assert result['accept_charset'] == []
        assert result['accept_encoding'] == []
        assert result['raw_accept'] == ''
        assert result['raw_accept_language'] == ''
        assert result['raw_accept_charset'] == ''
        assert result['raw_accept_encoding'] == ''


class TestCreateVaryHeader:
    """Tests for create_vary_header function."""

    def test_create_vary_header_new_fields(self):
        """Test creating vary header with new fields."""
        result = create_vary_header(None, ['Accept', 'Accept-Language'])
        assert result == 'Accept, Accept-Language'

    def test_create_vary_header_existing_fields(self):
        """Test creating vary header with existing fields."""
        result = create_vary_header('Accept-Encoding', ['Accept', 'Accept-Language'])
        assert result == 'Accept-Encoding, Accept, Accept-Language'

    def test_create_vary_header_duplicate_fields(self):
        """Test creating vary header with duplicate fields."""
        result = create_vary_header('Accept', ['Accept', 'Accept-Language'])
        assert result == 'Accept, Accept-Language'

    def test_create_vary_header_empty_new_fields(self):
        """Test creating vary header with empty new fields."""
        result = create_vary_header('Accept', [])
        assert result == 'Accept'
