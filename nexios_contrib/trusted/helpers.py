"""
Helper functions for trusted host validation.
"""
from __future__ import annotations

from typing import List, Optional, Set


def normalize_host(host: str) -> str:
    """Normalize a hostname to lowercase and strip whitespace."""
    return host.lower().strip()


def extract_host_and_port(host_header: str) -> tuple[str, Optional[int]]:
    """Extract host and port from a Host header value."""
    host_header = host_header.strip()

    if ":" in host_header:
        host, port_str = host_header.rsplit(":", 1)
        try:
            port = int(port_str)
            return host, port
        except ValueError:
            # Invalid port, treat as part of hostname
            return host_header, None
    else:
        return host_header, None


def is_wildcard_host(host: str) -> bool:
    """Check if a host pattern is a wildcard pattern."""
    return host.startswith("*")


def matches_wildcard_pattern(host: str, pattern: str) -> bool:
    """Check if a host matches a wildcard pattern."""
    if not is_wildcard_host(pattern):
        return False

    # Remove the wildcard prefix
    suffix = pattern[1:]

    # Check if host ends with the suffix
    return host.endswith(suffix)


def validate_host_against_patterns(
    host: str,
    allowed_patterns: List[str],
    allowed_ports: Optional[Set[int]] = None
) -> bool:
    """
    Validate a host against a list of allowed patterns.

    Args:
        host: The host to validate
        allowed_patterns: List of allowed host patterns (can include wildcards)
        allowed_ports: Optional set of allowed ports

    Returns:
        True if host is allowed, False otherwise
    """
    host = normalize_host(host)

    # Extract port if present
    if ":" in host:
        host_part, port_part = host.rsplit(":", 1)
        if allowed_ports and port_part not in allowed_ports:
            return False
    else:
        host_part = host

    # Check against each pattern
    for pattern in allowed_patterns:
        pattern = normalize_host(pattern)

        if pattern == host_part:
            return True
        elif is_wildcard_host(pattern):
            if matches_wildcard_pattern(host_part, pattern):
                return True

    return False


def get_host_from_headers(headers: dict) -> Optional[str]:
    """Extract host from request headers with proper precedence."""
    # Try X-Forwarded-Host first (for proxies/load balancers)
    forwarded_host = headers.get("x-forwarded-host")
    if forwarded_host:
        return forwarded_host.strip()

    # Try X-Host header (some proxies use this)
    x_host = headers.get("x-host")
    if x_host:
        return x_host.strip()

    # Fall back to Host header
    return headers.get("host")


def is_www_host(host: str) -> bool:
    """Check if a host starts with www."""
    return host.lower().startswith("www.")


def strip_www_prefix(host: str) -> str:
    """Remove www prefix from a host if present."""
    host = host.lower().strip()
    if is_www_host(host):
        return host[4:]  # Remove "www." prefix
    return host
