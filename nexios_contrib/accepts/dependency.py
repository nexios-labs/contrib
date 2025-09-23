"""
Dependency injection for accepts middleware in Nexios.

This module provides dependency injection utilities for accessing
parsed Accept header information from requests.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from nexios.dependencies import Depend, Context
from nexios.http import Request

from .helper import (
    parse_accept_header,
    parse_accept_language,
    parse_accept_charset,
    parse_accept_encoding,
)


class AcceptsInfo:
    """
    Container for parsed accepts information from a request.

    This class provides easy access to parsed Accept headers and
    includes methods for content negotiation.
    """

    def __init__(self, request: Request):
        """
        Initialize AcceptsInfo with a request object.

        Args:
            request: The HTTP request object containing headers to parse.
        """
        self.request = request
        self._parsed_accept = None
        self._parsed_accept_language = None
        self._parsed_accept_charset = None
        self._parsed_accept_encoding = None
        self._state_accept = None
        self._state_accept_language = None
        self._state_accept_charset = None
        self._state_accept_encoding = None

    @property
    def accept(self) -> List[Dict[str, Any]]:
        """Get parsed Accept header items from state or parse fresh."""
        if self._state_accept is None:
            if hasattr(self.request.state, 'accepts_parsed'):
                self._state_accept = getattr(self.request.state, 'accepts_parsed', {}).get('accept', [])
            else:
                self._state_accept = parse_accept_header(self.request.headers.get('Accept', ''))
        return self._state_accept

    @property
    def accept_language(self) -> List[Dict[str, Any]]:
        """Get parsed Accept-Language header items from state or parse fresh."""
        if self._state_accept_language is None:
            if hasattr(self.request.state, 'accepts_parsed'):
                self._state_accept_language = getattr(self.request.state, 'accepts_parsed', {}).get('accept_language', [])
            else:
                self._state_accept_language = parse_accept_language(self.request.headers.get('Accept-Language', ''))
        return self._state_accept_language

    @property
    def accept_charset(self) -> List[Dict[str, Any]]:
        """Get parsed Accept-Charset header items from state or parse fresh."""
        if self._state_accept_charset is None:
            if hasattr(self.request.state, 'accepts_parsed'):
                self._state_accept_charset = getattr(self.request.state, 'accepts_parsed', {}).get('accept_charset', [])
            else:
                self._state_accept_charset = parse_accept_charset(self.request.headers.get('Accept-Charset', ''))
        return self._state_accept_charset

    @property
    def accept_encoding(self) -> List[Dict[str, Any]]:
        """Get parsed Accept-Encoding header items from state or parse fresh."""
        if self._state_accept_encoding is None:
            if hasattr(self.request.state, 'accepts_parsed'):
                self._state_accept_encoding = getattr(self.request.state, 'accepts_parsed', {}).get('accept_encoding', [])
            else:
                self._state_accept_encoding = parse_accept_encoding(self.request.headers.get('Accept-Encoding', ''))
        return self._state_accept_encoding

    def get_accepted_types(self) -> List[str]:
        """
        Get all accepted content types from the request.

        Returns:
            List[str]: List of accepted content types ordered by quality.
        """
        return [item.value for item in self.accept if item.quality > 0]

    def get_accepted_languages(self) -> List[str]:
        """
        Get all accepted languages from the request.

        Returns:
            List[str]: List of accepted languages ordered by quality.
        """
        return [item.value for item in self.accept_language if item.quality > 0]

    def get_accepted_charsets(self) -> List[str]:
        """
        Get all accepted charsets from the request.

        Returns:
            List[str]: List of accepted charsets ordered by quality.
        """
        return [item.value for item in self.accept_charset if item.quality > 0]

    def get_accepted_encodings(self) -> List[str]:
        """
        Get all accepted encodings from the request.

        Returns:
            List[str]: List of accepted encodings ordered by quality.
        """
        return [item.value for item in self.accept_encoding if item.quality > 0]


def get_accepts_info_from_request(request: Request, attribute_name: str = "accepts") -> AcceptsInfo:
    """
    Get AcceptsInfo object from request.

    Args:
        request: The HTTP request object.
        attribute_name: The attribute name where accepts info is stored.

    Returns:
        AcceptsInfo: The accepts information object.
    """
    return getattr(request, attribute_name, AcceptsInfo(request))


def AcceptsDepend(attribute_name: str = "accepts") -> Any:
    """
    Dependency injection function for accessing accepts information.

    This function can be used as a dependency in route handlers to
    automatically inject parsed accepts information.

    Args:
        attribute_name: The attribute name where accepts info is stored in request.

    Returns:
        Any: Dependency injection wrapper function.

    Example:
        @app.get("/api/users")
        async def get_users(
            request: Request,
            response: Response,
            accepts: AcceptsInfo = AcceptsDepend()
        ):
            # Use accepts object to access parsed accept headers
            accepted_types = accepts.get_accepted_types()
            return {"accepted_types": accepted_types}
    """
    def _wrap(request: Request = Context().request) -> AcceptsInfo:
        return get_accepts_info_from_request(request, attribute_name)

    return Depend(_wrap)
