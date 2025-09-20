"""
Helper functions for URL normalization and path handling.
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional
from urllib.parse import urlparse, urlunparse


class SlashAction(Enum):
    """Actions for handling trailing slashes."""
    ADD = "add"
    REMOVE = "remove"
    REDIRECT_ADD = "redirect_add"
    REDIRECT_REMOVE = "redirect_remove"
    IGNORE = "ignore"


def normalize_path(path: str, remove_double_slashes: bool = True) -> str:
    """
    Normalize a path by removing double slashes and other issues.

    Args:
        path: The path to normalize
        remove_double_slashes: Whether to remove double slashes

    Returns:
        Normalized path
    """
    if remove_double_slashes:
        # Remove double slashes
        while "//" in path:
            path = path.replace("//", "/")

    # Remove leading/trailing whitespace
    path = path.strip()

    return path


def has_trailing_slash(path: str) -> bool:
    """Check if path has a trailing slash (excluding root /)."""
    return len(path) > 1 and path.endswith("/")


def add_trailing_slash(path: str) -> str:
    """Add trailing slash to path if not present."""
    if not has_trailing_slash(path):
        path += "/"
    return path


def remove_trailing_slash(path: str) -> str:
    """Remove trailing slash from path if present."""
    if has_trailing_slash(path):
        path = path[:-1]
    return path


def should_skip_path_processing(path: str) -> bool:
    """
    Check if path should be skipped from slash processing.

    This skips paths with file extensions, query parameters, fragments, etc.
    """
    skip_patterns = [
        ".",  # File extensions
        "?",  # Query parameters
        "#",  # Fragments
    ]

    return any(pattern in path for pattern in skip_patterns)


def build_normalized_url(
    base_url: str,
    path: str,
    preserve_query: bool = True,
    preserve_fragment: bool = True
) -> str:
    """
    Build a normalized URL from components.

    Args:
        base_url: Base URL to use
        path: Path component
        preserve_query: Whether to preserve query parameters
        preserve_fragment: Whether to preserve fragments

    Returns:
        Complete normalized URL
    """
    parsed = urlparse(base_url)

    # Build new URL components
    components = [
        parsed.scheme,
        parsed.netloc,
        path,
        parsed.params,
        parsed.query if preserve_query else "",
        parsed.fragment if preserve_fragment else ""
    ]

    return urlunparse(components)


def clean_url_path(url: str) -> str:
    """
    Clean a URL path by removing double slashes and normalizing.

    Args:
        url: URL to clean

    Returns:
        Cleaned URL
    """
    parsed = urlparse(url)

    # Normalize the path
    normalized_path = normalize_path(parsed.path)

    # Rebuild URL with normalized path
    return urlunparse((
        parsed.scheme,
        parsed.netloc,
        normalized_path,
        parsed.params,
        parsed.query,
        parsed.fragment
    ))


def get_path_segments(path: str) -> List[str]:
    """
    Get path segments from a path.

    Args:
        path: Path to split

    Returns:
        List of path segments
    """
    # Remove leading/trailing slashes and split
    path = path.strip("/")
    if not path:
        return []

    return path.split("/")


def join_path_segments(segments: List[str], trailing_slash: bool = False) -> str:
    """
    Join path segments into a path.

    Args:
        segments: List of path segments
        trailing_slash: Whether to add trailing slash

    Returns:
        Joined path
    """
    path = "/" + "/".join(segments)

    if trailing_slash and not path.endswith("/"):
        path += "/"

    return path


def is_absolute_url(url: str) -> bool:
    """
    Check if URL is absolute (has scheme and netloc).

    Args:
        url: URL to check

    Returns:
        True if absolute URL
    """
    parsed = urlparse(url)
    return bool(parsed.scheme and parsed.netloc)


def normalize_url(url: str, preserve_case: bool = True) -> str:
    """
    Normalize a URL comprehensively.

    Args:
        url: URL to normalize
        preserve_case: Whether to preserve case (default True for URLs)

    Returns:
        Normalized URL
    """
    if not is_absolute_url(url):
        # For relative URLs, just normalize path
        return normalize_path(url)

    parsed = urlparse(url)

    # Normalize path component
    normalized_path = normalize_path(parsed.path)

    # Build normalized URL
    return urlunparse((
        parsed.scheme,
        parsed.netloc,
        normalized_path,
        parsed.params,
        parsed.query,
        parsed.fragment
    ))
