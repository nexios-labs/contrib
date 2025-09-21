"""
Proxy contrib module for Nexios.

This module provides proxy header handling and security for applications
running behind proxy servers, load balancers, or CDNs.
"""
from __future__ import annotations

from .helper import (
    parse_forwarded_header,
    parse_x_forwarded_for,
    parse_x_forwarded_proto,
    parse_x_forwarded_host,
    parse_x_forwarded_port,
    get_client_ip_from_headers,
    get_protocol_from_headers,
    get_host_from_headers,
    is_trusted_proxy,
    validate_proxy_headers,
    build_forwarded_header,
)
from .middleware import ProxyMiddleware, Proxy, TrustedProxyMiddleware

__all__ = [
    "ProxyMiddleware",
    "Proxy",
    "TrustedProxyMiddleware",
    "parse_forwarded_header",
    "parse_x_forwarded_for",
    "parse_x_forwarded_proto",
    "parse_x_forwarded_host",
    "parse_x_forwarded_port",
    "get_client_ip_from_headers",
    "get_protocol_from_headers",
    "get_host_from_headers",
    "is_trusted_proxy",
    "validate_proxy_headers",
    "build_forwarded_header",
]
