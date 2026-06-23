"""
Accepts contrib module for Nexios.

This module provides content negotiation and Accept header processing
for Nexios applications.
"""

from __future__ import annotations

from .dependency import AcceptsDepend
from .helpers import (
    AcceptItem,
    AcceptsInfo,
    create_vary_header,
    get_accepted_charsets,
    get_accepted_content_types,
    get_accepted_encodings,
    get_accepted_languages,
    get_accepts_from_request,
    get_accepts_info,
    get_best_accepted_content_type,
    get_best_accepted_language,
    get_best_match,
    matches_media_type,
    negotiate_charset,
    negotiate_content_type,
    negotiate_encoding,
    negotiate_language,
    parse_accept_charset,
    parse_accept_encoding,
    parse_accept_header,
    parse_accept_language,
)
from .middleware import (
    Accepts,
    AcceptsMiddleware,
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
    "get_accepted_content_types",
    "get_accepted_languages",
    "get_accepted_charsets",
    "get_accepted_encodings",
    "get_best_accepted_content_type",
    "get_best_accepted_language",
    "get_accepts_from_request",
    "AcceptsMiddleware",
    "Accepts",
    "ContentNegotiationMiddleware",
    "StrictContentNegotiationMiddleware",
    "AcceptsInfo",
    "AcceptsDepend",
]
