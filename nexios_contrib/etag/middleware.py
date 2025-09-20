"""
ETag middleware for Nexios.

This middleware computes an ETag for responses (if not already set) and
handles conditional GET/HEAD using the If-None-Match header to return 304
Not Modified when appropriate.
"""
from __future__ import annotations

from typing import Any, Iterable, Tuple

from nexios.http import Request, Response
from nexios.middleware.base import BaseMiddleware
from nexios.http.response import BaseResponse   

from .helper import compute_and_set_etag, is_fresh


class ETagMiddleware(BaseMiddleware):
    """
    Middleware to automatically manage ETag headers and conditional requests.

    Options:
    - weak (bool): whether to generate weak validators (default: True)
    - methods (Iterable[str]): HTTP methods to apply ETag/conditional handling to
      (default: ("GET", "HEAD"))
    - override (bool): override an existing ETag from the handler (default: False)
    """

    def __init__(
        self,
        *,
        weak: bool = True,
        methods: Iterable[str] = ("GET", "HEAD"),
        override: bool = False,
        **_: Any,
    ) -> None:
        self.weak = weak
        self.methods = tuple(m.upper() for m in methods)
        self.override = override

    async def process_request(
        self,
        request: Request,
        response: Response,
        call_next: Any,
    ) -> None:
        # Defer all logic to process_response after handler executes.
        await call_next()

    async def process_response(
        self,
        request: Request,
        response: Response,
    ) -> None:
        # Apply only to configured methods
        if request.method.upper() not in self.methods:
            return None

        # Compute/set ETag if missing (or override when requested)
        has_existing = bool(response.headers.get("etag"))
        if not has_existing or self.override:
            compute_and_set_etag(response, weak=self.weak, override=True)

        # Handle If-None-Match freshness for conditional requests
        if is_fresh(request, response, weak_compare=True):
            
            # Per RFC 9110, a 304 response must not include a message body
            # Ensure body is empty; BaseResponse avoids content-length for 304
            response.make_response(BaseResponse(
                status_code=304
            ))
           

        return None
