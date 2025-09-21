"""
Accepts contrib module for Nexios.

This module provides content negotiation and Accept header processing
for Nexios applications.
"""
from __future__ import annotations

from .helper import (
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
from .middleware import (
    AcceptsMiddleware,
    Accepts,
    ContentNegotiationMiddleware,
    StrictContentNegotiationMiddleware,
)

__all__ = [
    "AcceptItem",
    "parse_accept_header",
    "parse_accept_language",
    "parse_accept_charset",
    "parse_accept_encoding",
    "negotiate_content_type",
    "negotiate_language",
    "negotiate_charset",
    "negotiate_encoding",
    "matches_media_type",
    "get_best_match",
    "get_accepts_info",
    "create_vary_header",
    "AcceptsMiddleware",
    "Accepts",
    "ContentNegotiationMiddleware",
    "StrictContentNegotiationMiddleware",
]
