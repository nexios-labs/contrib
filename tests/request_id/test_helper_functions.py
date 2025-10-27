"""
Tests for Request ID helper functions.
"""

import uuid
import pytest

from nexios.http import Request, Response
from nexios_contrib.request_id.helper import (
    generate_request_id,
    get_request_id_from_header,
    set_request_id_header,
    get_or_generate_request_id,
    validate_request_id,
    store_request_id_in_request,
    get_request_id_from_request,
)


class TestRequestIdHelpers:
    """Test Request ID helper functions."""

    def test_generate_request_id(self):
        """Test request ID generation."""
        request_id = generate_request_id()

        # Should return a string
        assert isinstance(request_id, str)

        # Should be valid UUID
        uuid.UUID(request_id)  # Should not raise exception

        # Should generate different IDs on each call
        request_id2 = generate_request_id()
        assert request_id != request_id2

    def test_get_request_id_from_header_found(self):
        """Test getting request ID from header when present."""
        # Mock request object with headers
        class MockRequest:
            def __init__(self, headers):
                self.headers = headers

        request = MockRequest({"X-Request-ID": "550e8400-e29b-41d4-a716-446655440000"})

        result = get_request_id_from_header(request)
        assert result == "550e8400-e29b-41d4-a716-446655440000"

    def test_get_request_id_from_header_not_found(self):
        """Test getting request ID from header when not present."""
        # Mock request object without the header
        class MockRequest:
            def __init__(self, headers):
                self.headers = headers

        request = MockRequest({"Other-Header": "value"})

        result = get_request_id_from_header(request)
        assert result is None

    def test_get_request_id_from_header_custom_header(self):
        """Test getting request ID from custom header."""
        # Mock request object with custom header
        class MockRequest:
            def __init__(self, headers):
                self.headers = headers

        request = MockRequest({"X-Custom-Request-ID": "550e8400-e29b-41d4-a716-446655440000"})

        result = get_request_id_from_header(request, "X-Custom-Request-ID")
        assert result == "550e8400-e29b-41d4-a716-446655440000"

    

    

    def test_get_or_generate_request_id_from_header(self):
        """Test get_or_generate_request_id when header is present."""
        # Mock request object with header
        class MockRequest:
            def __init__(self, headers):
                self.headers = headers

        request = MockRequest({"X-Request-ID": "550e8400-e29b-41d4-a716-446655440000"})

        result = get_or_generate_request_id(request)
        assert result == "550e8400-e29b-41d4-a716-446655440000"

    def test_get_or_generate_request_id_generate_new(self):
        """Test get_or_generate_request_id when header is not present."""
        # Mock request object without header
        class MockRequest:
            def __init__(self, headers):
                self.headers = headers

        request = MockRequest({})

        result = get_or_generate_request_id(request)

        # Should generate a new UUID
        assert isinstance(result, str)
        uuid.UUID(result)  # Should not raise exception

    def test_validate_request_id_valid(self):
        """Test request ID validation with valid UUID."""
        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        assert validate_request_id(valid_uuid) is True

    def test_validate_request_id_invalid(self):
        """Test request ID validation with invalid UUID."""
        invalid_uuid = "not-a-uuid"
        assert validate_request_id(invalid_uuid) is False

    def test_validate_request_id_empty(self):
        """Test request ID validation with empty string."""
        assert validate_request_id("") is False

    def test_validate_request_id_none(self):
        """Test request ID validation with None."""
        assert validate_request_id(None) is False

    def test_store_request_id_in_request(self):
        """Test storing request ID in request object."""
        # Mock request object with state
        class MockState:
            def __init__(self):
                self.data = {}

            def update(self, data):
                self.data.update(data)

        class MockRequest:
            def __init__(self):
                self.state = MockState()

        request = MockRequest()
        request_id = "550e8400-e29b-41d4-a716-446655440000"

        store_request_id_in_request(request, request_id)

        assert request.state.data["request_id"] == request_id

    def test_store_request_id_in_request_custom_attribute(self):
        """Test storing request ID in request object with custom attribute name."""
        # Mock request object with state
        class MockState:
            def __init__(self):
                self.data = {}

            def update(self, data):
                self.data.update(data)

        class MockRequest:
            def __init__(self):
                self.state = MockState()

        request = MockRequest()
        request_id = "550e8400-e29b-41d4-a716-446655440000"

        store_request_id_in_request(request, request_id, "custom_request_id")

        assert request.state.data["custom_request_id"] == request_id
        assert "request_id" not in request.state.data

    

  
    

    def test_uuid_generation_consistency(self):
        """Test that generated UUIDs are unique."""
        uuids = [generate_request_id() for _ in range(100)]

        # All should be unique
        assert len(set(uuids)) == 100

        # All should be valid UUIDs
        for uid in uuids:
            uuid.UUID(uid)  # Should not raise exception

   
