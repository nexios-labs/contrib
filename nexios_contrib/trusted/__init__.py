"""
Nexios Trusted Host contrib package.
"""

from .middleware import TrustedHostMiddleware
from .helpers import (
    get_host_from_headers,
    is_www_host,
    normalize_host,
    strip_www_prefix,
    validate_host_against_patterns,
)

__all__ = [
    "TrustedHostMiddleware",
    "get_host_from_headers",
    "is_www_host",
    "normalize_host",
    "strip_www_prefix",
    "validate_host_against_patterns",
]

def TrustedHost(
    allowed_hosts: list[str],
    allowed_ports: list[int] = None,
    www_redirect: bool = True
) -> TrustedHostMiddleware:
    """Create a TrustedHostMiddleware instance with the given configuration."""
    return TrustedHostMiddleware(
        allowed_hosts=allowed_hosts,
        allowed_ports=allowed_ports,
        www_redirect=www_redirect
    )
