"""
Proxy middleware for Nexios.

This middleware handles applications running behind proxy servers by properly
processing X-Forwarded-* headers and managing proxy-related security.
"""
from __future__ import annotations

from typing import Any, List, Optional

from nexios.http import Request, Response
from nexios.middleware.base import BaseMiddleware

from .helper import (
    get_client_ip_from_headers,
    get_protocol_from_headers,
    get_host_from_headers,
    is_trusted_proxy,
    validate_proxy_headers,
    parse_x_forwarded_for,
    parse_forwarded_header,
)


class ProxyMiddleware(BaseMiddleware):
    """
    Middleware to handle applications running behind proxy servers.

    This middleware processes X-Forwarded-* headers and other proxy-related headers
    to determine the real client information when the application is behind a proxy,
    load balancer, or CDN.

    Features:
    - Extracts real client IP from X-Forwarded-For or Forwarded headers
    - Determines correct protocol from X-Forwarded-Proto
    - Handles X-Forwarded-Host for proper host resolution
    - Security controls to prevent header spoofing
    - Configurable trusted proxy list

    Options:
    - trusted_proxies (List[str]): List of trusted proxy IP addresses/CIDRs
    - trust_forwarded_headers (bool): Whether to trust X-Forwarded-* headers (default: True)
    - trust_forwarded_header (bool): Whether to trust Forwarded header (default: True)
    - preserve_host_header (bool): Whether to preserve original Host header (default: False)
    - store_proxy_info (bool): Store proxy information in request object (default: True)
    """

    def __init__(
        self,
        *,
        trusted_proxies: Optional[List[str]] = None,
        trust_forwarded_headers: bool = True,
        trust_forwarded_header: bool = True,
        preserve_host_header: bool = False,
        store_proxy_info: bool = True,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the ProxyMiddleware.

        Args:
            trusted_proxies: List of trusted proxy IP addresses/CIDRs.
            trust_forwarded_headers: Whether to trust X-Forwarded-* headers.
            trust_forwarded_header: Whether to trust Forwarded header.
            preserve_host_header: Whether to preserve original Host header.
            store_proxy_info: Store proxy information in request object.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(**kwargs)
        self.trusted_proxies = trusted_proxies or []
        self.trust_forwarded_headers = trust_forwarded_headers
        self.trust_forwarded_header = trust_forwarded_header
        self.preserve_host_header = preserve_host_header
        self.store_proxy_info = store_proxy_info

    async def process_request(
        self,
        request: Request,
        response: Response,
        call_next: Any,
    ) -> Any:
        """
        Process incoming request to handle proxy headers.

        Args:
            request: The HTTP request object.
            response: The HTTP response object.
            call_next: The next middleware or handler to call.

        Returns:
            Any: The result from the next middleware or handler.
        """
        original_client_ip = getattr(request, 'client_ip', None)
        original_host = getattr(request, 'host', None)
        original_url = getattr(request, 'url', '')

        # Validate proxy headers and extract real client information
        proxy_info = validate_proxy_headers(request, self.trusted_proxies)

        # Update request with real client IP if from trusted proxy
        if proxy_info['trusted_proxy'] and proxy_info['client_ip']:
            setattr(request, 'client_ip', proxy_info['client_ip'])

        # Update request URL scheme if protocol changed
        if proxy_info['protocol'] and proxy_info['protocol'] != original_url.split('://')[0]:
            if original_url:
                # Reconstruct URL with correct scheme
                new_scheme = proxy_info['protocol']
                rest_of_url = original_url.split('://', 1)[1] if '://' in original_url else original_url
                setattr(request, 'url', f"{new_scheme}://{rest_of_url}")

        # Update host if provided and not preserving original
        if not self.preserve_host_header and proxy_info['host']:
            setattr(request, 'host', proxy_info['host'])

        # Store proxy information in request for later access
        if self.store_proxy_info:
            setattr(request, 'proxy_info', proxy_info)
            setattr(request, 'x_forwarded_for', parse_x_forwarded_for(
                request.headers.get('X-Forwarded-For', '')
            ))

            if self.trust_forwarded_header:
                forwarded_data = parse_forwarded_header(request.headers.get('Forwarded', ''))
                if forwarded_data:
                    setattr(request, 'forwarded_header', forwarded_data)

        return await call_next()

    async def process_response(
        self,
        request: Request,
        response: Response,
    ) -> Any:
        """
        Process response to potentially add proxy-related headers.

        Args:
            request: The HTTP request object.
            response: The HTTP response object.

        Returns:
            Any: The response object.
        """
        # Add X-Client-IP header if we have real client IP info
        proxy_info = getattr(request, 'proxy_info', None)
        if proxy_info and proxy_info['client_ip'] != getattr(request, 'client_ip', None):
            response.set_header('X-Client-IP', proxy_info['client_ip'])

        return response


def Proxy(
    trusted_proxies: Optional[List[str]] = None,
    trust_forwarded_headers: bool = True,
    trust_forwarded_header: bool = True,
    preserve_host_header: bool = False,
    store_proxy_info: bool = True,
) -> ProxyMiddleware:
    """
    Convenience function to create a ProxyMiddleware instance.

    Args:
        trusted_proxies: List of trusted proxy IP addresses/CIDRs.
        trust_forwarded_headers: Whether to trust X-Forwarded-* headers.
        trust_forwarded_header: Whether to trust Forwarded header.
        preserve_host_header: Whether to preserve original Host header.
        store_proxy_info: Store proxy information in request object.

    Returns:
        ProxyMiddleware: Configured ProxyMiddleware instance.
    """
    return ProxyMiddleware(
        trusted_proxies=trusted_proxies,
        trust_forwarded_headers=trust_forwarded_headers,
        trust_forwarded_header=trust_forwarded_header,
        preserve_host_header=preserve_host_header,
        store_proxy_info=store_proxy_info,
    )


class TrustedProxyMiddleware(ProxyMiddleware):
    """
    Enhanced proxy middleware with stricter security controls.

    This middleware only processes proxy headers from explicitly trusted proxies
    and provides additional security features.
    """

    def __init__(
        self,
        *,
        trusted_proxies: List[str],
        require_https: bool = False,
        max_forwards: int = 10,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the TrustedProxyMiddleware.

        Args:
            trusted_proxies: List of trusted proxy IP addresses/CIDRs (required).
            require_https: Whether to require HTTPS when behind proxy.
            max_forwards: Maximum number of proxy hops to allow.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(
            trusted_proxies=trusted_proxies,
            trust_forwarded_headers=True,
            trust_forwarded_header=True,
            **kwargs
        )
        self.require_https = require_https
        self.max_forwards = max_forwards

    async def process_request(
        self,
        request: Request,
        response: Response,
        call_next: Any,
    ) -> Any:
        """
        Process request with enhanced security checks.
        """
        # Check if client is from trusted proxy
        client_ip = getattr(request, 'client_ip', None)
        if not client_ip or not is_trusted_proxy(client_ip, self.trusted_proxies):
            # Not from trusted proxy, don't process proxy headers
            if self.store_proxy_info:
                setattr(request, 'proxy_info', {'trusted_proxy': False})
            return await call_next()

        # Process proxy headers
        result = await super().process_request(request, response, call_next)

        # Additional security checks
        if self.require_https:
            proxy_info = getattr(request, 'proxy_info', {})
            if proxy_info.get('protocol') != 'https':
                # Could redirect to HTTPS or return error
                response.status_code = 400
                return {"error": "HTTPS required when behind proxy"}

        # Check for too many forwards
        x_forwarded_for = parse_x_forwarded_for(request.headers.get('X-Forwarded-For', ''))
        if len(x_forwarded_for) > self.max_forwards:
            response.status_code = 400
            return {"error": "Too many proxy hops"}

        return result
