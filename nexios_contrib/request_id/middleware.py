"""
Request ID middleware for Nexios.

This middleware automatically generates or extracts request IDs from incoming requests
and includes them in response headers for better request tracing and debugging.
"""
from __future__ import annotations

from typing import Any, Optional

from nexios.http import Request, Response
from nexios.middleware.base import BaseMiddleware

from .helper import (
    get_or_generate_request_id,
    get_request_id_from_header,
    set_request_id_header,
    store_request_id_in_request,
    get_request_id_from_request,
)


class RequestIdMiddleware(BaseMiddleware):
    """
    Middleware to automatically manage request IDs for better tracing and debugging.

    This middleware:
    1. Extracts request ID from incoming request headers (X-Request-ID) or generates a new one
    2. Stores the request ID in the request object for later access
    3. Adds the request ID to response headers
    4. Optionally forces regeneration of request IDs

    Options:
    - header_name (str): Header name to use for request ID (default: "X-Request-ID")
    - force_generate (bool): Always generate new request ID instead of using existing one (default: False)
    - store_in_request (bool): Store request ID in request object for later access (default: True)
    - request_attribute_name (str): Attribute name to store request ID in request (default: "request_id")
    - include_in_response (bool): Include request ID in response headers (default: True)
    """

    def __init__(
        self,
        *,
        header_name: str = "X-Request-ID",
        force_generate: bool = False,
        store_in_request: bool = True,
        request_attribute_name: str = "request_id",
        include_in_response: bool = True,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the RequestIdMiddleware.

        Args:
            header_name: Header name to use for request ID extraction/setting.
            force_generate: Always generate new request ID instead of using existing one.
            store_in_request: Store request ID in request object for later access.
            request_attribute_name: Attribute name to store request ID in request.
            include_in_response: Include request ID in response headers.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(**kwargs)
        self.header_name = header_name
        self.force_generate = force_generate
        self.store_in_request = store_in_request
        self.request_attribute_name = request_attribute_name
        self.include_in_response = include_in_response

    async def process_request(
        self,
        request: Request,
        response: Response,
        call_next: Any,
    ) -> Any:
        """
        Process incoming request to handle request ID.

        Args:
            request: The HTTP request object.
            response: The HTTP response object.
            call_next: The next middleware or handler to call.

        Returns:
            Any: The result from the next middleware or handler.
        """
        # Get or generate request ID
        if self.force_generate:
            request_id = get_or_generate_request_id(request, self.header_name)
        else:
            request_id = get_request_id_from_header(request, self.header_name)
            if not request_id:
                request_id = get_or_generate_request_id(request, self.header_name)

        # Store request ID in request object if enabled
        if self.store_in_request:
            store_request_id_in_request(request, request_id, self.request_attribute_name)

        # Store request ID in response headers if enabled
        if self.include_in_response:
            set_request_id_header(response, request_id, self.header_name)

        return await call_next()

    async def process_response(
        self,
        request: Request,
        response: Response,
    ) -> Any:
        """
        Process response to ensure request ID is properly set.

        Args:
            request: The HTTP request object.
            response: The HTTP response object.

        Returns:
            Any: The response object.
        """
        # Get stored request ID from request object
        request_id = get_request_id_from_request(request, self.request_attribute_name)

        # If request ID is not in response headers but we have one stored, add it
        if request_id and self.include_in_response:
            existing_header = response.headers.get(self.header_name)
            if not existing_header:
                set_request_id_header(response, request_id, self.header_name)

        return response


def RequestId(
    header_name: str = "X-Request-ID",
    force_generate: bool = False,
    store_in_request: bool = True,
    request_attribute_name: str = "request_id",
    include_in_response: bool = True,
) -> RequestIdMiddleware:
    """
    Convenience function to create a RequestIdMiddleware instance.

    Args:
        header_name: Header name to use for request ID extraction/setting.
        force_generate: Always generate new request ID instead of using existing one.
        store_in_request: Store request ID in request object for later access.
        request_attribute_name: Attribute name to store request ID in request.
        include_in_response: Include request ID in response headers.

    Returns:
        RequestIdMiddleware: Configured RequestIdMiddleware instance.
    """
    return RequestIdMiddleware(
        header_name=header_name,
        force_generate=force_generate,
        store_in_request=store_in_request,
        request_attribute_name=request_attribute_name,
        include_in_response=include_in_response,
    )
