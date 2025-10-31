"""
ETag helper utilities for Nexios.

This module provides functions for generating, validating, and setting ETag headers.
It is designed to work with Nexios's Request and Response abstractions.
"""
from __future__ import annotations

import re
from base64 import b64encode
from hashlib import sha1
from typing import Iterable, Optional

from nexios.http import Request, Response

_WEAK_PREFIX = 'W/'
_ETAG_TOKEN_RE = re.compile(r"^(W\/)?\s*\"[^\"]*\"\s*$")


def generate_etag_from_bytes(data: bytes, weak: bool = True) -> str:
    """
    Generate an ETag from raw bytes using SHA-1 + base64.

    Args:
        data: Raw bytes to hash.
        weak: If True, prefixes with Weak validator (W/).

    Returns:
        The ETag string including quotes and optional weak prefix.
    """
    h = sha1()
    h.update(data)
    tag = f'"{b64encode(h.digest()).decode("utf-8")}"'
    return f"{_WEAK_PREFIX}{tag}" if weak else tag


def normalize_etag(tag: str) -> str:
    """Normalize an ETag token to the canonical quoted form keeping its weakness.

    If the value is not a valid ETag token, raises ValueError.
    """
    tag = tag.strip()
    if not _ETAG_TOKEN_RE.match(tag):
        # Try to coerce when unquoted simple tokens are passed
        if not tag.startswith('W/'):
            clean = tag.strip('"')
            tag = f'"{clean}"'
        else:
            core = tag[2:].strip()
            clean_core = core.strip('"')
            tag = f'W/"{clean_core}"'

        if not _ETAG_TOKEN_RE.match(tag):
            raise ValueError(f"Invalid ETag token: {tag}")
    return tag


def set_response_etag(response: Response, etag: str, override: bool = True) -> None:
    """Set the ETag header on the response.

    Args:
        response: Nexios Response wrapper.
        etag: The ETag value; will be normalized.
        override: Whether to override an existing ETag header.
    """
    tag = normalize_etag(etag)
    response.set_header("etag", tag, overide=override)


def compute_and_set_etag(response: Response, body :bytes = b'' ,weak: bool = True, override: bool = False) -> str:
    """
    Compute an ETag for the current response body and set it if not present (or if override=True).

    Returns the ETag value used.
    """
    # Response.body returns bytes
    
    tag = generate_etag_from_bytes(body, weak=weak)
    set_response_etag(response, tag, override=override)
    return tag


def parse_if_none_match(request: Request) -> list[str]:
    """Parse the If-None-Match header into a list of ETag tokens (normalized)."""
    inm = request.headers.get("if-none-match")
    if not inm:
        return []
    # Split on commas while respecting that tokens don't contain commas
    parts = [p.strip() for p in inm.split(",") if p.strip()]
    tags: list[str] = []
    for p in parts:
        try:
            tags.append(normalize_etag(p))
        except ValueError:
            # Ignore invalid tokens per robustness principles
            continue
    return tags


def parse_if_match(request: Request) -> list[str]:
    """Parse the If-Match header into a list of ETag tokens (normalized)."""
    im = request.headers.get("if-match")
    if not im:
        return []
    parts = [p.strip() for p in im.split(",") if p.strip()]
    tags: list[str] = []
    for p in parts:
        try:
            tags.append(normalize_etag(p))
        except ValueError:
            continue
    return tags


def etag_matches(etag: str, candidates: Iterable[str], weak_compare: bool = True) -> bool:
    """
    Check if an ETag matches any in candidates.

    If weak_compare is True, weakness (W/) is ignored during comparison, otherwise strict.
    """
    try:
        normalized = normalize_etag(etag)
    except ValueError:
        return False

    def strip_weak(t: str) -> str:
        return t[2:] if t.startswith(_WEAK_PREFIX) else t

    if weak_compare:
        norm_val = strip_weak(normalized)
        for c in candidates:
            try:
                if strip_weak(normalize_etag(c)) == norm_val:
                    return True
            except ValueError:
                continue
        return False
    else:
        for c in candidates:
            try:
                if normalize_etag(c) == normalized:
                    return True
            except ValueError:
                continue
        return False


def is_fresh(request: Request, response: Response, weak_compare: bool = True) -> bool:
    """
    Determine if the response is "fresh" given request preconditions using ETag validators.

    Currently considers If-None-Match logic. If there is a matching ETag, the response is fresh.
    """
    current = response.headers.get("etag")
    if not current:
        return False
    inm = parse_if_none_match(request)
    if not inm:
        return False
    return etag_matches(current, inm, weak_compare=weak_compare)
