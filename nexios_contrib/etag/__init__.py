from .helper import (
    compute_and_set_etag,
    etag_matches,
    generate_etag_from_bytes,
    is_fresh,
    normalize_etag,
    parse_if_match,
    parse_if_none_match,
    set_response_etag,
)
from .middleware import ETagMiddleware
from typing import Iterable

__all__ = [
    "ETagMiddleware",
    "generate_etag_from_bytes",
    "normalize_etag",
    "set_response_etag",
    "compute_and_set_etag",
    "parse_if_none_match",
    "parse_if_match",
    "etag_matches",
    "is_fresh",
]

def  ETag(weak: bool = True, methods: Iterable[str] = ("GET", "HEAD"), override: bool = False) -> ETagMiddleware:
    return ETagMiddleware(weak=weak, methods=methods, override=override)