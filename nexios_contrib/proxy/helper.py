"""
Proxy helper functions for Nexios.

This module provides utilities for handling proxy headers and managing
applications behind proxy servers.
"""
from __future__ import annotations

import ipaddress
from typing import List, Optional, Union
from urllib.parse import urlparse

from nexios.http import Request


def parse_forwarded_header(forwarded_header: str) -> dict:
    """
    Parse the Forwarded header according to RFC 7239.

    Args:
        forwarded_header: The Forwarded header value.

    Returns:
        dict: Parsed forwarded parameters.
    """
    result = {}
    if not forwarded_header:
        return result

    # Split by comma and semicolon
    for forwarded in forwarded_header.split(','):
        forwarded = forwarded.strip()
        if not forwarded:
            continue

        params = {}
        current_param = ""
        current_value = ""

        i = 0
        while i < len(forwarded):
            char = forwarded[i]

            if char == '=':
                current_param = current_value.strip()
                current_value = ""
            elif char == ';':
                if current_param:
                    params[current_param] = current_value.strip()
                current_param = ""
                current_value = ""
            else:
                current_value += char

            i += 1

        if current_param:
            params[current_param] = current_value.strip()

        # Process standard forwarded parameters
        for key, value in params.items():
            if key.lower() == 'for':
                result['for'] = value
            elif key.lower() == 'by':
                result['by'] = value
            elif key.lower() == 'host':
                result['host'] = value
            elif key.lower() == 'proto':
                result['proto'] = value

    return result


def parse_x_forwarded_for(x_forwarded_for: str) -> List[str]:
    """
    Parse the X-Forwarded-For header.

    Args:
        x_forwarded_for: The X-Forwarded-For header value.

    Returns:
        List[str]: List of IP addresses in order.
    """
    if not x_forwarded_for:
        return []

    return [ip.strip() for ip in x_forwarded_for.split(',') if ip.strip()]


def parse_x_forwarded_proto(x_forwarded_proto: str) -> Optional[str]:
    """
    Parse the X-Forwarded-Proto header.

    Args:
        x_forwarded_proto: The X-Forwarded-Proto header value.

    Returns:
        Optional[str]: The protocol (http/https).
    """
    if not x_forwarded_proto:
        return None

    proto = x_forwarded_proto.strip().lower()
    return proto if proto in ['http', 'https'] else None


def parse_x_forwarded_host(x_forwarded_host: str) -> Optional[str]:
    """
    Parse the X-Forwarded-Host header.

    Args:
        x_forwarded_host: The X-Forwarded-Host header value.

    Returns:
        Optional[str]: The host value.
    """
    if not x_forwarded_host:
        return None

    return x_forwarded_host.strip()


def parse_x_forwarded_port(x_forwarded_port: str) -> Optional[int]:
    """
    Parse the X-Forwarded-Port header.

    Args:
        x_forwarded_port: The X-Forwarded-Port header value.

    Returns:
        Optional[int]: The port number.
    """
    if not x_forwarded_port:
        return None

    try:
        port = int(x_forwarded_port.strip())
        if 1 <= port <= 65535:
            return port
    except ValueError:
        pass

    return None


def get_client_ip_from_headers(request: Request, trusted_proxies: List[str] = None) -> Optional[str]:
    """
    Extract the real client IP from proxy headers.

    Args:
        request: The HTTP request object.
        trusted_proxies: List of trusted proxy IP addresses.

    Returns:
        Optional[str]: The real client IP address.
    """
    trusted_proxies = trusted_proxies or []

    # Try X-Forwarded-For first
    x_forwarded_for = request.headers.get('X-Forwarded-For')
    if x_forwarded_for:
        forwarded_ips = parse_x_forwarded_for(x_forwarded_for)
        if forwarded_ips:
            # Return the first non-trusted IP
            for ip in forwarded_ips:
                if ip not in trusted_proxies:
                    return ip

    # Try Forwarded header
    forwarded = request.headers.get('Forwarded')
    if forwarded:
        parsed = parse_forwarded_header(forwarded)
        if 'for' in parsed:
            for_value = parsed['for']
            if for_value not in trusted_proxies:
                return for_value

    # Fall back to direct client IP
    return getattr(request, 'client_ip', None)


def get_protocol_from_headers(request: Request) -> str:
    """
    Extract the real protocol from proxy headers.

    Args:
        request: The HTTP request object.

    Returns:
        str: The protocol (http/https).
    """
    # Check X-Forwarded-Proto first
    proto = parse_x_forwarded_proto(request.headers.get('X-Forwarded-Proto'))
    if proto:
        return proto

    # Check Forwarded header
    forwarded = request.headers.get('Forwarded')
    if forwarded:
        parsed = parse_forwarded_header(forwarded)
        if 'proto' in parsed:
            return parsed['proto']

    # Fall back to request URL scheme
    return getattr(request, 'url', '').split('://')[0] if getattr(request, 'url', '') else 'http'


def get_host_from_headers(request: Request) -> Optional[str]:
    """
    Extract the real host from proxy headers.

    Args:
        request: The HTTP request object.

    Returns:
        Optional[str]: The real host.
    """
    # Check X-Forwarded-Host first
    host = parse_x_forwarded_host(request.headers.get('X-Forwarded-Host'))
    if host:
        return host

    # Check Forwarded header
    forwarded = request.headers.get('Forwarded')
    if forwarded:
        parsed = parse_forwarded_header(forwarded)
        if 'host' in parsed:
            return parsed['host']

    # Fall back to request host
    return getattr(request, 'host', None)


def is_trusted_proxy(client_ip: str, trusted_proxies: List[str]) -> bool:
    """
    Check if an IP address is in the trusted proxies list.

    Args:
        client_ip: The client IP address.
        trusted_proxies: List of trusted proxy IP addresses/CIDRs.

    Returns:
        bool: True if the IP is trusted.
    """
    try:
        client_addr = ipaddress.ip_address(client_ip)
    except ValueError:
        return False

    for proxy in trusted_proxies:
        try:
            if '/' in proxy:
                # CIDR notation
                network = ipaddress.ip_network(proxy, strict=False)
                if client_addr in network:
                    return True
            else:
                # Single IP
                if client_addr == ipaddress.ip_address(proxy):
                    return True
        except ValueError:
            continue

    return False


def validate_proxy_headers(request: Request, trusted_proxies: List[str] = None) -> dict:
    """
    Validate and extract proxy-related information from headers.

    Args:
        request: The HTTP request object.
        trusted_proxies: List of trusted proxy IP addresses.

    Returns:
        dict: Validated proxy information.
    """
    client_ip = getattr(request, 'client_ip', None)

    # Only process proxy headers if client is from trusted proxy
    if client_ip and trusted_proxies and is_trusted_proxy(client_ip, trusted_proxies):
        return {
            'client_ip': get_client_ip_from_headers(request, trusted_proxies),
            'protocol': get_protocol_from_headers(request),
            'host': get_host_from_headers(request),
            'trusted_proxy': True
        }

    return {
        'client_ip': client_ip,
        'protocol': getattr(request, 'url', '').split('://')[0] if getattr(request, 'url', '') else 'http',
        'host': getattr(request, 'host', None),
        'trusted_proxy': False
    }


def build_forwarded_header(
    client_ip: str,
    protocol: str = None,
    host: str = None,
    by: str = None
) -> str:
    """
    Build a Forwarded header according to RFC 7239.

    Args:
        client_ip: The client IP address.
        protocol: The protocol (http/https).
        host: The host.
        by: The proxy identifier.

    Returns:
        str: The formatted Forwarded header.
    """
    parts = []

    if client_ip:
        parts.append(f"for={client_ip}")

    if protocol:
        parts.append(f"proto={protocol}")

    if host:
        parts.append(f"host={host}")

    if by:
        parts.append(f"by={by}")

    return "; ".join(parts)
