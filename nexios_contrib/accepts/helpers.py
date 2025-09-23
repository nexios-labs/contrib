"""
Helper functions for accessing accepts information from requests.

This module provides utility functions to extract and work with
parsed Accept header information stored in request objects.
"""
from __future__ import annotations

from typing import List, Optional

from nexios.http import Request

from .dependency import AcceptsInfo


def get_accepts_from_request(request: Request, attribute_name: str = "accepts") -> AcceptsInfo:
    """
    Get AcceptsInfo object from request.

    Args:
        request: The HTTP request object.
        attribute_name: The attribute name where accepts info is stored.

    Returns:
        AcceptsInfo: The accepts information object.
    """
    return AcceptsInfo(request)


def get_accepted_content_types(request: Request, attribute_name: str = "accepts_parsed") -> List[str]:
    """
    Get accepted content types from request.

    Args:
        request: The HTTP request object.
        attribute_name: The attribute name where parsed accepts info is stored.

    Returns:
        List[str]: List of accepted content types ordered by quality.
    """
    accepts_parsed = getattr(request, attribute_name, {})
    accept_items = accepts_parsed.get('accept', [])

    return [item.value for item in accept_items if item.quality > 0]


def get_accepted_languages(request: Request, attribute_name: str = "accepts_parsed") -> List[str]:
    """
    Get accepted languages from request.

    Args:
        request: The HTTP request object.
        attribute_name: The attribute name where parsed accepts info is stored.

    Returns:
        List[str]: List of accepted languages ordered by quality.
    """
    accepts_parsed = getattr(request.state, attribute_name, {})
    accept_items = accepts_parsed.get('accept_language', [])

    return [item.value for item in accept_items if item.quality > 0]


def get_accepted_charsets(request: Request, attribute_name: str = "accepts_parsed") -> List[str]:
    """
    Get accepted charsets from request.

    Args:
        request: The HTTP request object.
        attribute_name: The attribute name where parsed accepts info is stored.

    Returns:
        List[str]: List of accepted charsets ordered by quality.
    """
    accepts_parsed = getattr(request.state, attribute_name, {})
    accept_items = accepts_parsed.get('accept_charset', [])

    return [item.value for item in accept_items if item.quality > 0]


def get_accepted_encodings(request: Request, attribute_name: str = "accepts_parsed") -> List[str]:
    """
    Get accepted encodings from request.

    Args:
        request: The HTTP request object.
        attribute_name: The attribute name where parsed accepts info is stored.

    Returns:
        List[str]: List of accepted encodings ordered by quality.
    """
    accepts_parsed = getattr(request.state, attribute_name, {})
    accept_items = accepts_parsed.get('accept_encoding', [])

    return [item.value for item in accept_items if item.quality > 0]


def get_best_accepted_content_type(request: Request, available_types: List[str], attribute_name: str = "accepts_parsed") -> Optional[str]:
    """
    Get the best matching content type from available types.

    Args:
        request: The HTTP request object.
        available_types: List of available content types.
        attribute_name: The attribute name where parsed accepts info is stored.

    Returns:
        Optional[str]: The best matching content type, or None if no match.
    """
    accepted_types = get_accepted_content_types(request, attribute_name)

    for accepted_type in accepted_types:
        for available_type in available_types:
            if matches_media_type(accepted_type, available_type):
                return available_type

    # Fallback to first available type if no specific match
    return available_types[0] if available_types else None


def get_best_accepted_language(request: Request, available_languages: List[str], attribute_name: str = "accepts_parsed") -> Optional[str]:
    """
    Get the best matching language from available languages.

    Args:
        request: The HTTP request object.
        available_languages: List of available languages.
        attribute_name: The attribute name where parsed accepts info is stored.

    Returns:
        Optional[str]: The best matching language, or None if no match.
    """
    accepted_languages = get_accepted_languages(request, attribute_name)

    for accepted_lang in accepted_languages:
        # Exact match
        if accepted_lang in available_languages:
            return accepted_lang

        # Language prefix match (e.g., "en" matches "en-US")
        if '-' in accepted_lang:
            lang_prefix = accepted_lang.split('-')[0]
            for available_lang in available_languages:
                if available_lang.startswith(lang_prefix + '-'):
                    return available_lang
                if available_lang == lang_prefix:
                    return available_lang

    # Fallback to first available language if no specific match
    return available_languages[0] if available_languages else None


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
