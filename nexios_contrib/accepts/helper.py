"""
Accepts helper functions for Nexios.

This module provides utilities for parsing Accept headers and performing
content negotiation for HTTP requests.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple, Union

from nexios.http import Request


class AcceptItem:
    """
    Represents a single item in an Accept header with type/subtype and parameters.
    """

    def __init__(self, value: str, quality: float = 1.0, params: Optional[Dict[str, str]] = None):
        """
        Initialize an AcceptItem.

        Args:
            value: The media type or other value (e.g., "text/html", "en-US")
            quality: The quality value (q parameter, 0.0 to 1.0)
            params: Additional parameters
        """
        self.value = value
        self.quality = quality
        self.params = params or {}

    def __repr__(self) -> str:
        return f"AcceptItem(value={self.value}, quality={self.quality})"


def parse_accept_header(accept_header: str) -> List[AcceptItem]:
    """
    Parse an Accept header into a list of AcceptItems sorted by quality.

    Args:
        accept_header: The Accept header value.

    Returns:
        List[AcceptItem]: Sorted list of accept items (highest quality first).
    """
    if not accept_header:
        return []

    items = []

    for part in accept_header.split(','):
        part = part.strip()
        if not part:
            continue

        # Parse quality parameter
        quality = 1.0
        params = {}

        if ';' in part:
            media_range, param_str = part.split(';', 1)
            media_range = media_range.strip()

            # Parse parameters
            for param in param_str.split(';'):
                param = param.strip()
                if '=' in param:
                    key, value = param.split('=', 1)
                    key = key.strip().lower()
                    value = value.strip()

                    if key == 'q':
                        try:
                            quality = max(0.0, min(1.0, float(value)))
                        except ValueError:
                            quality = 0.0
                    else:
                        params[key] = value
                else:
                    # Malformed parameter, treat as part of media range
                    media_range = f"{media_range};{param}"
        else:
            media_range = part

        items.append(AcceptItem(media_range, quality, params))

    # Sort by quality (highest first), then by specificity
    items.sort(key=lambda x: (-x.quality, x.value.count('/'), -len(x.value)))

    return items


def parse_accept_language(accept_language: str) -> List[AcceptItem]:
    """
    Parse Accept-Language header.

    Args:
        accept_language: The Accept-Language header value.

    Returns:
        List[AcceptItem]: Sorted list of language items.
    """
    return parse_accept_header(accept_language)


def parse_accept_charset(accept_charset: str) -> List[AcceptItem]:
    """
    Parse Accept-Charset header.

    Args:
        accept_charset: The Accept-Charset header value.

    Returns:
        List[AcceptItem]: Sorted list of charset items.
    """
    return parse_accept_header(accept_charset)


def parse_accept_encoding(accept_encoding: str) -> List[AcceptItem]:
    """
    Parse Accept-Encoding header.

    Args:
        accept_encoding: The Accept-Encoding header value.

    Returns:
        List[AcceptItem]: Sorted list of encoding items.
    """
    return parse_accept_header(accept_encoding)


def negotiate_content_type(accept_header: str, available_types: List[str]) -> Optional[str]:
    """
    Perform content negotiation for media types.

    Args:
        accept_header: The Accept header value.
        available_types: List of available media types.

    Returns:
        Optional[str]: The best matching media type, or None if no match.
    """
    if not accept_header or not available_types:
        return available_types[0] if available_types else None

    accept_items = parse_accept_header(accept_header)

    # First pass: exact matches
    for accept_item in accept_items:
        if accept_item.quality == 0:
            continue

        for available_type in available_types:
            if matches_media_type(accept_item.value, available_type):
                return available_type

    # Second pass: wildcard matches
    for accept_item in accept_items:
        if accept_item.quality == 0:
            continue

        # Check for */* or type/*
        if accept_item.value == '*/*':
            return available_types[0]  # Return first available type

        if '/*' in accept_item.value:
            accept_type = accept_item.value.split('/')[0]
            for available_type in available_types:
                if available_type.startswith(accept_type + '/'):
                    return available_type

    return None


def negotiate_language(accept_language: str, available_languages: List[str]) -> Optional[str]:
    """
    Perform language negotiation.

    Args:
        accept_language: The Accept-Language header value.
        available_languages: List of available languages.

    Returns:
        Optional[str]: The best matching language, or None if no match.
    """
    if not accept_language or not available_languages:
        return available_languages[0] if available_languages else None

    accept_items = parse_accept_language(accept_language)

    for accept_item in accept_items:
        if accept_item.quality == 0:
            continue

        # Exact match
        if accept_item.value in available_languages:
            return accept_item.value

        # Language prefix match (e.g., "en" matches "en-US")
        if '-' in accept_item.value:
            lang_prefix = accept_item.value.split('-')[0]
            for available_lang in available_languages:
                if available_lang.startswith(lang_prefix + '-'):
                    return available_lang
                if available_lang == lang_prefix:
                    return available_lang

    return available_languages[0] if available_languages else None


def negotiate_charset(accept_charset: str, available_charsets: List[str]) -> Optional[str]:
    """
    Perform charset negotiation.

    Args:
        accept_charset: The Accept-Charset header value.
        available_charsets: List of available charsets.

    Returns:
        Optional[str]: The best matching charset, or None if no match.
    """
    if not accept_charset or not available_charsets:
        return available_charsets[0] if available_charsets else None

    accept_items = parse_accept_charset(accept_charset)

    for accept_item in accept_items:
        if accept_item.quality == 0:
            continue

        if accept_item.value in available_charsets:
            return accept_item.value

        # Handle * wildcard
        if accept_item.value == '*':
            return available_charsets[0]

    return available_charsets[0] if available_charsets else None


def negotiate_encoding(accept_encoding: str, available_encodings: List[str]) -> List[str]:
    """
    Perform encoding negotiation.

    Args:
        accept_encoding: The Accept-Encoding header value.
        available_encodings: List of available encodings.

    Returns:
        List[str]: List of accepted encodings in order of preference.
    """
    if not accept_encoding or not available_encodings:
        return []

    accept_items = parse_accept_encoding(accept_encoding)
    accepted_encodings = []

    for accept_item in accept_items:
        if accept_item.quality == 0:
            continue

        # Handle identity encoding
        if accept_item.value == 'identity' or accept_item.value == '*':
            accepted_encodings.extend([enc for enc in available_encodings if enc != 'identity'])
            continue

        # Check for specific encoding match
        if accept_item.value in available_encodings:
            accepted_encodings.append(accept_item.value)

    return accepted_encodings


def matches_media_type(pattern: str, media_type: str) -> bool:
    """
    Check if a media type matches a pattern (e.g., "text/*" matches "text/html").

    Args:
        pattern: The pattern to match against (e.g., "text/*", "application/json")
        media_type: The media type to test (e.g., "text/html", "application/json")

    Returns:
        bool: True if the media type matches the pattern.
    """
    if pattern == media_type:
        return True

    if pattern == '*/*':
        return True

    if pattern.endswith('/*'):
        pattern_type = pattern[:-2]
        return media_type.startswith(pattern_type + '/')

    return False


def get_best_match(accept_header: str, options: List[str]) -> Optional[str]:
    """
    Get the best match from a list of options based on an Accept header.

    Args:
        accept_header: The Accept header value.
        options: List of available options.

    Returns:
        Optional[str]: The best matching option, or None if no match.
    """
    if not accept_header or not options:
        return options[0] if options else None

    accept_items = parse_accept_header(accept_header)

    for accept_item in accept_items:
        if accept_item.quality == 0:
            continue

        for option in options:
            if matches_media_type(accept_item.value, option):
                return option

    return options[0] if options else None


def get_accepts_info(request: Request) -> Dict[str, any]:
    """
    Extract and parse all Accept-related headers from a request.

    Args:
        request: The HTTP request object.

    Returns:
        Dict[str, any]: Dictionary containing parsed accept information.
    """
    return {
        'accept': parse_accept_header(request.headers.get('Accept', '')),
        'accept_language': parse_accept_language(request.headers.get('Accept-Language', '')),
        'accept_charset': parse_accept_charset(request.headers.get('Accept-Charset', '')),
        'accept_encoding': parse_accept_encoding(request.headers.get('Accept-Encoding', '')),
        'raw_accept': request.headers.get('Accept', ''),
        'raw_accept_language': request.headers.get('Accept-Language', ''),
        'raw_accept_charset': request.headers.get('Accept-Charset', ''),
        'raw_accept_encoding': request.headers.get('Accept-Encoding', ''),
    }


def create_vary_header(existing_vary: Optional[str], new_fields: List[str]) -> str:
    """
    Create or update a Vary header to include additional fields.

    Args:
        existing_vary: Existing Vary header value.
        new_fields: List of fields to add to Vary header.

    Returns:
        str: Updated Vary header value.
    """
    if not existing_vary:
        return ', '.join(new_fields)

    existing_fields = [field.strip() for field in existing_vary.split(',')]

    for field in new_fields:
        if field not in existing_fields:
            existing_fields.append(field)

    return ', '.join(existing_fields)
