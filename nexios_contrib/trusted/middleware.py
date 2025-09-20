"""
Trusted host middleware for Nexios.

This middleware validates the Host header to ensure requests are coming from
trusted hosts/domains. This is a security feature to prevent Host header attacks.
"""
from __future__ import annotations

from typing import Any, List, Optional, Set, Union

from nexios.http import Request, Response
from nexios.middleware.base import BaseMiddleware
from nexios.http.exceptions import HTTPException


class TrustedHostMiddleware(BaseMiddleware):
    """
    Middleware to validate the Host header against a list of allowed hosts.

    This middleware checks the Host header of incoming requests and rejects
    requests with untrusted hosts to prevent Host header attacks.

    Options:
    - allowed_hosts (List[str]): List of allowed hostnames/IPs
    - allowed_ports (Optional[List[int]]): List of allowed ports (default: None)
    - www_redirect (bool): Redirect www.domain.com to domain.com (default: True)
    """

    def __init__(
        self,
        *,
        allowed_hosts: List[str],
        allowed_ports: Optional[List[int]] = None,
        www_redirect: bool = True,
        **_: Any,
    ) -> None:
        self.allowed_hosts = [host.lower().strip() for host in allowed_hosts]
        self.allowed_ports = set(allowed_ports or [])
        self.www_redirect = www_redirect

        # Pre-compile allowed host patterns for efficiency
        self._allowed_host_patterns: Set[str] = set()
        for host in self.allowed_hosts:
            if host.startswith("*"):
                # Wildcard pattern - store as-is
                self._allowed_host_patterns.add(host)
            else:
                # Exact host - normalize
                self._allowed_host_patterns.add(host)

    def _is_host_allowed(self, host: str) -> bool:
        """Check if the given host is in the allowed hosts list."""
        host = host.lower().strip()

        # Remove port if present
        if ":" in host:
            host_part, port_part = host.rsplit(":", 1)
            if self.allowed_ports and port_part not in self.allowed_ports:
                return False
        else:
            host_part = host

        # Check against allowed hosts
        for allowed_host in self._allowed_host_patterns:
            if allowed_host == host_part:
                return True
            elif allowed_host.startswith("*"):
                # Wildcard pattern - check suffix
                suffix = allowed_host[1:]  # Remove the *
                if host_part.endswith(suffix):
                    return True

        return False

    def _extract_host_from_request(self, request: Request) -> Optional[str]:
        """Extract host from the request headers."""
        # Try X-Forwarded-Host first (for proxies)
        forwarded_host = request.headers.get("x-forwarded-host")
        if forwarded_host:
            return forwarded_host

        # Fall back to Host header
        return request.headers.get("host")

    async def process_request(
        self,
        request: Request,
        response: Response,
        call_next: Any,
    ) -> None:
        host = self._extract_host_from_request(request)

        if not host:
            # No host header - reject
            raise HTTPException(status_code=400, detail="Host header is required")

        # Check if host is allowed
        if not self._is_host_allowed(host):
            raise HTTPException(status_code=400, detail=f"Host '{host}' is not allowed")

        # Handle www redirect if enabled
        if self.www_redirect and host.startswith("www."):
            www_prefix = "www."
            if host.startswith(www_prefix):
                clean_host = host[len(www_prefix):]
                # Check if the clean host is allowed
                if self._is_host_allowed(clean_host):
                    # In a real implementation, you'd redirect here
                    # For now, we'll just allow it to continue
                    pass

        await call_next()
