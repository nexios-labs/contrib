"""
Accepts middleware for Nexios.

This middleware provides automatic content negotiation and Accept header
processing for Nexios applications.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Union

from nexios.http import Request, Response
from nexios.middleware.base import BaseMiddleware

from .helper import (
    get_best_match,
    negotiate_content_type,
    negotiate_language,
    negotiate_charset,
    negotiate_encoding,
    get_accepts_info,
    create_vary_header,
    parse_accept_header,
    parse_accept_language,
    parse_accept_charset,
    parse_accept_encoding,
)


class AcceptsMiddleware(BaseMiddleware):
    """
    Middleware for automatic content negotiation and Accept header processing.

    This middleware automatically:
    - Parses Accept headers and stores them in the request object
    - Provides content negotiation utilities
    - Sets appropriate Vary headers
    - Handles default content type negotiation

    Options:
    - default_content_type (str): Default content type when no match found
    - default_language (str): Default language when no match found
    - default_charset (str): Default charset when no match found
    - set_vary_header (bool): Automatically set Vary headers
    - store_accepts_info (bool): Store parsed accepts info in request object
    """

    def __init__(
        self,
        *,
        default_content_type: str = "application/json",
        default_language: str = "en",
        default_charset: str = "utf-8",
        set_vary_header: bool = True,
        store_accepts_info: bool = True,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the AcceptsMiddleware.

        Args:
            default_content_type: Default content type when no match found.
            default_language: Default language when no match found.
            default_charset: Default charset when no match found.
            set_vary_header: Automatically set Vary headers.
            store_accepts_info: Store parsed accepts info in request object.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(**kwargs)
        self.default_content_type = default_content_type
        self.default_language = default_language
        self.default_charset = default_charset
        self.set_vary_header = set_vary_header
        self.store_accepts_info = store_accepts_info
        self.vary = []

    async def process_request(
        self,
        request: Request,
        response: Response,
        call_next: Any,
    ) -> Any:
        """
        Process incoming request to handle Accept headers.

        Args:
            request: The HTTP request object.
            response: The HTTP response object.
            call_next: The next middleware or handler to call.

        Returns:
            Any: The result from the next middleware or handler.
        """
        # Store accepts information in request
        if self.store_accepts_info:
            accepts_info = get_accepts_info(request)
            request.accepts = accepts_info

        # Set Vary header if requested
        if self.set_vary_header:
            if request.headers.get('Accept'):
                self.vary.append('Accept')
            if request.headers.get('Accept-Language'):
                self.vary.append('Accept-Language')
            if request.headers.get('Accept-Charset'):
                self.vary.append('Accept-Charset')
            if request.headers.get('Accept-Encoding'):
                self.vary.append('Accept-Encoding')

            
                

        return await call_next()

    async def process_response(
        self,
        request: Request,
        response: Response,
    ) -> Any:
        """
        Process response to potentially set content negotiation headers.

        Args:
            request: The HTTP request object.
            response: The HTTP response object.

        Returns:
            Any: The response object.
        """
        if self.vary:
            existing_vary = response.headers.get('Vary')
            response.set_header('Vary', create_vary_header(existing_vary, self.vary),overide=True)
        # Set default content type if not already set and Content-Type header is missing
        if not response.headers.get('Content-Type') and self.default_content_type:
            # Try to negotiate content type based on Accept header
            accept_header = request.headers.get('Accept')
            if accept_header:
                negotiated_type = negotiate_content_type(
                    accept_header,
                    [self.default_content_type]
                )
                if negotiated_type:
                    response.set_header('Content-Type', negotiated_type,overide=True)
            else:
                response.set_header('Content-Type', self.default_content_type,overide=True)

        return response


def Accepts(
    default_content_type: str = "application/json",
    default_language: str = "en",
    default_charset: str = "utf-8",
    set_vary_header: bool = True,
    store_accepts_info: bool = True,
) -> AcceptsMiddleware:
    """
    Convenience function to create an AcceptsMiddleware instance.

    Args:
        default_content_type: Default content type when no match found.
        default_language: Default language when no match found.
        default_charset: Default charset when no match found.
        set_vary_header: Automatically set Vary headers.
        store_accepts_info: Store parsed accepts info in request object.

    Returns:
        AcceptsMiddleware: Configured AcceptsMiddleware instance.
    """
    return AcceptsMiddleware(
        default_content_type=default_content_type,
        default_language=default_language,
        default_charset=default_charset,
        set_vary_header=set_vary_header,
        store_accepts_info=store_accepts_info,
    )


class ContentNegotiationMiddleware(AcceptsMiddleware):
    """
    Enhanced middleware with explicit content negotiation support.

    This middleware provides methods for explicit content negotiation
    and is useful when you need more control over the negotiation process.
    """

    def __init__(self, *args, **kwargs):
        """Initialize with same options as AcceptsMiddleware."""
        super().__init__(*args, **kwargs)

    def negotiate_content_type(
        self,
        request: Request,
        available_types: List[str],
        default_type: Optional[str] = None
    ) -> str:
        """
        Negotiate the best content type for this request.

        Args:
            request: The HTTP request object.
            available_types: List of available content types.
            default_type: Default type if no match found.

        Returns:
            str: The best matching content type.
        """
        accept_header = request.headers.get('Accept')
        if accept_header:
            negotiated = negotiate_content_type(accept_header, available_types)
            if negotiated:
                return negotiated

        return default_type or self.default_content_type

    def negotiate_language(
        self,
        request: Request,
        available_languages: List[str],
        default_language: Optional[str] = None
    ) -> str:
        """
        Negotiate the best language for this request.

        Args:
            request: The HTTP request object.
            available_languages: List of available languages.
            default_language: Default language if no match found.

        Returns:
            str: The best matching language.
        """
        accept_language = request.headers.get('Accept-Language')
        if accept_language:
            negotiated = negotiate_language(accept_language, available_languages)
            if negotiated:
                return negotiated

        return default_language or self.default_language

    def get_accepted_types(self, request: Request) -> List[str]:
        """
        Get all accepted content types for this request.

        Args:
            request: The HTTP request object.

        Returns:
            List[str]: List of accepted content types.
        """
        accepts_info = getattr(request, 'accepts', {})
        accept_items = accepts_info.get('accept', [])

        return [item.value for item in accept_items if item.quality > 0]

    def get_accepted_languages(self, request: Request) -> List[str]:
        """
        Get all accepted languages for this request.

        Args:
            request: The HTTP request object.

        Returns:
            List[str]: List of accepted languages.
        """
        accepts_info = getattr(request, 'accepts', {})
        accept_items = accepts_info.get('accept_language', [])

        return [item.value for item in accept_items if item.quality > 0]


class StrictContentNegotiationMiddleware(ContentNegotiationMiddleware):
    """
    Strict content negotiation middleware that enforces content type matching.

    This middleware will return 406 Not Acceptable if the client doesn't accept
    any of the available content types.
    """

    def __init__(
        self,
        *,
        available_types: List[str],
        available_languages: Optional[List[str]] = None,
        **kwargs
    ):
        """
        Initialize the StrictContentNegotiationMiddleware.

        Args:
            available_types: List of content types this application can serve.
            available_languages: List of languages this application supports.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(**kwargs)
        self.available_types = available_types
        self.available_languages = available_languages or ['en']

    async def process_request(
        self,
        request: Request,
        response: Response,
        call_next: Any,
    ) -> Any:
        """
        Process request with strict content negotiation.
        """
        # Perform strict content negotiation
        best_type = self.negotiate_content_type(
            request,
            self.available_types,
            self.default_content_type
        )

        # Check if client accepts the best available type
        accept_header = request.headers.get('Accept')
        if accept_header and best_type not in self.available_types:
            # Client doesn't accept any of our available types
            response.status(406)
            response.set_header('Content-Type', 'application/json')
            return response.json({
                "error": "Not Acceptable",
                "message": "Client does not accept any available content types",
                "available_types": self.available_types
            })

        # Store negotiation results in request
        setattr(request, 'negotiated_content_type', best_type)

        best_language = self.negotiate_language(
            request,
            self.available_languages,
            self.default_language
        )
        setattr(request, 'negotiated_language', best_language)

        return await call_next()
