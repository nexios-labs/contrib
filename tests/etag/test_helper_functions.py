"""
Tests for ETag helper functions.
"""

import typing

from nexios.http import Request, Response
from nexios_contrib.etag import (
    compute_and_set_etag,
    etag_matches,
    generate_etag_from_bytes,
    is_fresh,
    normalize_etag,
    parse_if_match,
    parse_if_none_match,
    set_response_etag,
)

Scope = typing.MutableMapping[str, typing.Any]
Message = typing.MutableMapping[str, typing.Any]
Receive = typing.Callable[[], typing.Awaitable[Message]]
Send = typing.Callable[[Message], typing.Awaitable[None]]


async def mock_receive() -> Message:
    """Mock receive function for ASGI."""
    return {"type": "http.request", "body": b"", "more_body": False}


async def mock_send(message: Message) -> None:
    """Mock send function for ASGI."""
    pass


def create_mock_scope(
    method: str = "GET",
    path: str = "/",
    headers: typing.Optional[typing.Dict[str, str]] = None,
    query_string: bytes = b""
) -> Scope:
    """Create a mock ASGI scope for testing."""
    return {
        "type": "http",
        "method": method,
        "path": path,
        "raw_path": path.encode("utf-8"),
        "query_string": query_string,
        "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
        "server": ("testserver", 80),
        "client": ("testclient", 12345),
        "scheme": "http",
        "root_path": "",
        "extensions": {},
        "state": {},
        "global_state": {},
    }


class TestGenerateEtagFromBytes:
    """Test generate_etag_from_bytes function."""

    def test_generate_etag_from_bytes_weak(self):
        """Test generating weak ETag."""
        data = b"Hello, World!"
        etag = generate_etag_from_bytes(data, weak=True)
        assert etag.startswith('W/"')
        assert etag.endswith('"')
        # Should be consistent for same input
        etag2 = generate_etag_from_bytes(data, weak=True)
        assert etag == etag2

    def test_generate_etag_from_bytes_strong(self):
        """Test generating strong ETag."""
        data = b"Hello, World!"
        etag = generate_etag_from_bytes(data, weak=False)
        assert not etag.startswith('W/')
        assert etag.endswith('"')
        # Should be consistent for same input
        etag2 = generate_etag_from_bytes(data, weak=False)
        assert etag == etag2

    def test_generate_etag_from_bytes_different_data(self):
        """Test that different data produces different ETags."""
        data1 = b"Hello, World!"
        data2 = b"Hello, World! "
        etag1 = generate_etag_from_bytes(data1)
        etag2 = generate_etag_from_bytes(data2)
        assert etag1 != etag2

    def test_generate_etag_from_bytes_empty_data(self):
        """Test generating ETag from empty data."""
        etag = generate_etag_from_bytes(b"")
        assert etag.startswith('W/"')
        assert etag.endswith('"')

    def test_generate_etag_from_bytes_unicode(self):
        """Test generating ETag from unicode data."""
        data = "Hello, 世界!".encode('utf-8')
        etag = generate_etag_from_bytes(data)
        assert etag.startswith('W/"')
        assert etag.endswith('"')


class TestNormalizeEtag:
    """Test normalize_etag function."""

    def test_normalize_etag_valid_weak(self):
        """Test normalizing valid weak ETag."""
        etag = 'W/"abc123"'
        normalized = normalize_etag(etag)
        assert normalized == 'W/"abc123"'

    def test_normalize_etag_valid_strong(self):
        """Test normalizing valid strong ETag."""
        etag = '"abc123"'
        normalized = normalize_etag(etag)
        assert normalized == '"abc123"'

    def test_normalize_etag_unquoted(self):
        """Test normalizing unquoted ETag."""
        etag = "abc123"
        normalized = normalize_etag(etag)
        assert normalized == '"abc123"'

    def test_normalize_etag_weak_unquoted(self):
        """Test normalizing weak unquoted ETag."""
        etag = "W/abc123"
        normalized = normalize_etag(etag)
        assert normalized == 'W/"abc123"'

    def test_normalize_etag_with_spaces(self):
        """Test normalizing ETag with spaces."""
        etag = '  "abc123"  '
        normalized = normalize_etag(etag)
        assert normalized == '"abc123"'

    


class TestSetResponseEtag:
    """Test set_response_etag function."""

    def test_set_response_etag_new(self):
        """Test setting ETag on response without existing ETag."""
        scope = create_mock_scope()
        request = Request(scope, mock_receive, mock_send)
        response = Response(request)
        set_response_etag(response, '"abc123"')
        assert response.headers.get("etag") == '"abc123"'

    def test_set_response_etag_override_true(self):
        """Test setting ETag with override=True."""
        scope = create_mock_scope()
        request = Request(scope, mock_receive, mock_send)
        response = Response(request)
        response.set_header("etag", '"old123"')
        set_response_etag(response, '"new123"', override=True)
        assert response.headers.get("etag") == '"new123"'

    def test_set_response_etag_normalize(self):
        """Test that ETag is normalized when set."""
        scope = create_mock_scope()
        request = Request(scope, mock_receive, mock_send)
        response = Response(request)
        set_response_etag(response, "abc123")  # unquoted
        assert response.headers.get("etag") == '"abc123"'  # quoted


class TestComputeAndSetEtag:
    """Test compute_and_set_etag function."""

    def test_compute_and_set_etag_new(self):
        """Test computing and setting ETag on response without existing."""
        scope = create_mock_scope()
        request = Request(scope, mock_receive, mock_send)
        response = Response(request)
        etag = compute_and_set_etag(response, body=b"Hello, World!")
        assert etag.startswith('W/"')
        assert response.headers.get("etag") == etag

    def test_compute_and_set_etag_override_false(self):
        """Test not overriding existing ETag when override=False."""
        scope = create_mock_scope()
        request = Request(scope, mock_receive, mock_send)
        response = Response(request)
        response.set_header("etag", '"existing"')
        etag = compute_and_set_etag(response, body=b"Hello, World!", override=False)
        assert response.headers.get("etag") == '"existing"'
        # Should still compute and return the etag even if not set
        assert etag.startswith('W/"')

    def test_compute_and_set_etag_override_true(self):
        """Test overriding existing ETag when override=True."""
        scope = create_mock_scope()
        request = Request(scope, mock_receive, mock_send)
        response = Response(request)
        response.set_header("etag", '"existing"')
        etag = compute_and_set_etag(response, body=b"Hello, World!", override=True)
        assert response.headers.get("etag") == etag
        assert etag.startswith('W/"')

    def test_compute_and_set_etag_weak_false(self):
        """Test computing strong ETag."""
        scope = create_mock_scope()
        request = Request(scope, mock_receive, mock_send)
        response = Response(request)
        etag = compute_and_set_etag(response, body=b"Hello, World!", weak=False)
        assert not etag.startswith('W/')
        assert response.headers.get("etag") == etag


class TestParseIfNoneMatch:
    """Test parse_if_none_match function."""

    def test_parse_if_none_match_single(self):
        """Test parsing single ETag in If-None-Match."""
        scope = create_mock_scope(headers={"if-none-match": '"abc123"'})
        request = Request(scope, mock_receive, mock_send)
        etags = parse_if_none_match(request)
        assert etags == ['"abc123"']

    def test_parse_if_none_match_multiple(self):
        """Test parsing multiple ETags in If-None-Match."""
        scope = create_mock_scope(headers={"if-none-match": '"abc123", "def456"'})
        request = Request(scope, mock_receive, mock_send)
        etags = parse_if_none_match(request)
        assert etags == ['"abc123"', '"def456"']

    def test_parse_if_none_match_weak(self):
        """Test parsing weak ETags in If-None-Match."""
        scope = create_mock_scope(headers={"if-none-match": 'W/"abc123"'})
        request = Request(scope, mock_receive, mock_send)
        etags = parse_if_none_match(request)
        assert etags == ['W/"abc123"']

    def test_parse_if_none_match_unquoted(self):
        """Test parsing unquoted ETags in If-None-Match."""
        scope = create_mock_scope(headers={"if-none-match": "abc123"})
        request = Request(scope, mock_receive, mock_send)
        etags = parse_if_none_match(request)
        assert etags == ['"abc123"']

    def test_parse_if_none_match_empty(self):
        """Test parsing empty If-None-Match."""
        scope = create_mock_scope()
        request = Request(scope, mock_receive, mock_send)
        etags = parse_if_none_match(request)
        assert etags == []

   

class TestParseIfMatch:
    """Test parse_if_match function."""

    def test_parse_if_match_single(self):
        """Test parsing single ETag in If-Match."""
        scope = create_mock_scope(headers={"if-match": '"abc123"'})
        request = Request(scope, mock_receive, mock_send)
        etags = parse_if_match(request)
        assert etags == ['"abc123"']

    def test_parse_if_match_multiple(self):
        """Test parsing multiple ETags in If-Match."""
        scope = create_mock_scope(headers={"if-match": '"abc123", "def456"'})
        request = Request(scope, mock_receive, mock_send)
        etags = parse_if_match(request)
        assert etags == ['"abc123"', '"def456"']

    def test_parse_if_match_empty(self):
        """Test parsing empty If-Match."""
        scope = create_mock_scope()
        request = Request(scope, mock_receive, mock_send)
        etags = parse_if_match(request)
        assert etags == []

  


class TestEtagMatches:
    """Test etag_matches function."""

    def test_etag_matches_exact_strong(self):
        """Test exact match with strong ETags."""
        assert etag_matches('"abc123"', ['"abc123"'], weak_compare=False)
        assert not etag_matches('"abc123"', ['"def456"'], weak_compare=False)

    def test_etag_matches_exact_weak(self):
        """Test exact match with weak ETags."""
        assert etag_matches('W/"abc123"', ['W/"abc123"'], weak_compare=False)
        assert not etag_matches('W/"abc123"', ['W/"def456"'], weak_compare=False)

    def test_etag_matches_weak_compare_true(self):
        """Test weak comparison mode."""
        assert etag_matches('"abc123"', ['"abc123"'], weak_compare=True)
        assert etag_matches('W/"abc123"', ['"abc123"'], weak_compare=True)
        assert etag_matches('"abc123"', ['W/"abc123"'], weak_compare=True)
        assert not etag_matches('"abc123"', ['"def456"'], weak_compare=True)

    def test_etag_matches_multiple_candidates(self):
        """Test matching against multiple candidates."""
        assert etag_matches('"abc123"', ['"def456"', '"abc123"', '"ghi789"'], weak_compare=False)
        assert not etag_matches('"abc123"', ['"def456"', '"xyz123"'], weak_compare=False)

    def test_etag_matches_invalid_etag(self):
        """Test matching with invalid ETag."""
        assert not etag_matches("invalid", ['"abc123"'], weak_compare=True)

    def test_etag_matches_invalid_candidate(self):
        """Test matching with invalid candidate."""
        assert not etag_matches('"abc123"', ["invalid"], weak_compare=True)


class TestIsFresh:
    """Test is_fresh function."""

    def test_is_fresh_matching_etag(self):
        """Test freshness when ETag matches."""
        scope = create_mock_scope(headers={"if-none-match": '"abc123"'})
        request = Request(scope, mock_receive, mock_send)
        response = Response(request)
        response.set_header("etag", '"abc123"')
        assert is_fresh(request, response) is True

    def test_is_fresh_non_matching_etag(self):
        """Test freshness when ETag doesn't match."""
        scope = create_mock_scope(headers={"if-none-match": '"def456"'})
        request = Request(scope, mock_receive, mock_send)
        response = Response(request)
        response.set_header("etag", '"abc123"')
        assert is_fresh(request, response) is False

    def test_is_fresh_weak_compare(self):
        """Test freshness with weak comparison."""
        scope = create_mock_scope(headers={"if-none-match": 'W/"abc123"'})
        request = Request(scope, mock_receive, mock_send)
        response = Response(request)
        response.set_header("etag", '"abc123"')
        assert is_fresh(request, response, weak_compare=True) is True

    def test_is_fresh_no_etag(self):
        """Test freshness when response has no ETag."""
        scope = create_mock_scope(headers={"if-none-match": '"abc123"'})
        request = Request(scope, mock_receive, mock_send)
        response = Response(request)
        assert is_fresh(request, response) is False

    def test_is_fresh_no_if_none_match(self):
        """Test freshness when request has no If-None-Match."""
        scope = create_mock_scope()
        request = Request(scope, mock_receive, mock_send)
        response = Response(request)
        response.set_header("etag", '"abc123"')
        assert is_fresh(request, response) is False

    def test_is_fresh_multiple_if_none_match(self):
        """Test freshness with multiple If-None-Match values."""
        scope = create_mock_scope(headers={"if-none-match": '"def456", "abc123"'})
        request = Request(scope, mock_receive, mock_send)
        response = Response(request)
        response.set_header("etag", '"abc123"')
        assert is_fresh(request, response) is True
