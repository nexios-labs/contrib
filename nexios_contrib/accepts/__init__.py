"""
Accepts contrib module for Nexios.

This module provides content negotiation and Accept header processing
for Nexios applications.
"""
from __future__ import annotations
from .helpers import (
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
    get_accepted_content_types,
    get_accepted_languages,
    get_accepted_charsets,
    get_accepted_encodings,
    get_best_accepted_content_type,
    get_best_accepted_language,
    get_accepts_from_request,
    AcceptsInfo,
    
)
from .middleware import (
    Accepts,
    
    AcceptsMiddleware,
    ContentNegotiationMiddleware,
    StrictContentNegotiationMiddleware,
)
from .dependency import  AcceptsDepend
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
