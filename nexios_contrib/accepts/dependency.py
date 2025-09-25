"""
Dependency injection for accepts middleware in Nexios.

This module provides dependency injection utilities for accessing
parsed Accept header information from requests.
"""
from __future__ import annotations

from typing import Any
from nexios.dependencies import Depend, Context
from nexios.http import Request
from .helpers import AcceptsInfo






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


def AcceptsDepend(attribute_name: str = "accepts") -> AcceptsInfo:
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
