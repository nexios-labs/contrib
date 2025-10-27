"""
Request ID helper functions for Nexios.

This module provides utilities for generating, managing, and working with request IDs
in the Nexios framework.
"""
from __future__ import annotations

import uuid
from typing import Optional

from nexios.http import Request, Response


def generate_request_id() -> str:
    """
    Generate a unique request ID using UUID4.

    Returns:
        str: A unique request ID string.
    """
    return str(uuid.uuid4())


def get_request_id_from_header(
    request: Request,
    header_name: str = "X-Request-ID"
) -> Optional[str]:
    """
    Extract request ID from request headers.

    Args:
        request: The HTTP request object.
        header_name: The header name to look for (default: "X-Request-ID").

    Returns:
        Optional[str]: The request ID if found, None otherwise.
    """
    return request.headers.get(header_name)


def set_request_id_header(
    response: Response,
    request_id: str,
    header_name: str = "X-Request-ID"
) -> None:
    """
    Set the request ID in the response headers.

    Args:
        response: The HTTP response object.
        request_id: The request ID to set.
        header_name: The header name to use (default: "X-Request-ID").
    """
    response.set_header(header_name, request_id,overide=True)


def get_or_generate_request_id(
    request: Request,
    header_name: str = "X-Request-ID"
) -> str:
    """
    Get request ID from request headers or generate a new one.

    Args:
        request: The HTTP request object.
        header_name: The header name to look for (default: "X-Request-ID").

    Returns:
        str: The request ID (either from headers or newly generated).
    """
    request_id = get_request_id_from_header(request, header_name)
    if not request_id:
        request_id = generate_request_id()
    return request_id


def validate_request_id(request_id: str) -> bool:
    """
    Validate a request ID format.

    Args:
        request_id: The request ID to validate.

    Returns:
        bool: True if valid, False otherwise.
    """
    try:
        uuid.UUID(request_id)
        return True
    except (ValueError, TypeError):
        return False


def store_request_id_in_request(
    request: Request,
    request_id: str,
    attribute_name: str = "request_id"
) -> None:
    """
    Store request ID in the request object for later access.

    Args:
        request: The HTTP request object.
        request_id: The request ID to store.
        attribute_name: The attribute name to use (default: "request_id").
    """
    request.state.update({attribute_name: request_id})


def get_request_id_from_request(
    request: Request,
    attribute_name: str = "request_id"
) -> Optional[str]:
    """
    Retrieve request ID from the request object.

    Args:
        request: The HTTP request object.
        attribute_name: The attribute name to look for (default: "request_id").

    Returns:
        Optional[str]: The stored request ID if found, None otherwise.
    """
    return getattr(request.state,attribute_name,None)
