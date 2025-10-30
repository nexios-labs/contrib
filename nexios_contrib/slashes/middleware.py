"""
URL normalization middleware for Nexios.

This middleware cleans up URLs by handling trailing slashes, double slashes,
and other common URL normalization issues.
"""
from __future__ import annotations

from enum import Enum
from typing import Any
from urllib.parse import urlparse, urlunparse

from nexios.http import Request, Response
from nexios.middleware.base import BaseMiddleware
from .helpers import is_double_slash


class SlashAction(Enum):
    """Actions for handling trailing slashes."""
    ADD = "add"           # Add trailing slash if missing
    REMOVE = "remove"     # Remove trailing slash if present
    REDIRECT_ADD = "redirect_add"      # Redirect to add trailing slash
    REDIRECT_REMOVE = "redirect_remove"  # Redirect to remove trailing slash
    IGNORE = "ignore"     # Leave as-is


class SlashesMiddleware(BaseMiddleware):
    """
    Middleware to normalize URLs and handle trailing slashes.

    This middleware can:
    - Remove double slashes (// becomes /)
    - Handle trailing slashes according to specified rules
    - Redirect or modify paths based on configuration

    Options:
    - slash_action: How to handle trailing slashes
    - auto_remove_double_slashes: Remove double slashes automatically
    - redirect_status_code: HTTP status code for redirects (default: 301)
    """

    def __init__(
        self,
        *,
        slash_action: SlashAction = SlashAction.REDIRECT_REMOVE,
        redirect_status_code: int = 301,
        **_: Any,
    ) -> None:
        self.slash_action = slash_action
        self.redirect_status_code = redirect_status_code

    def _normalize_path(self, path: str) -> str:
        """Normalize a path by removing double slashes."""
        

        # Remove double slashes
        while "//" in path:
            path = path.replace("//", "/")

        return path

    def _has_trailing_slash(self, path: str) -> bool:
        """Check if path has a trailing slash (excluding root /)."""
        return len(path) > 1 and path.endswith("/")

    def _add_trailing_slash(self, path: str) -> str:
        """Add trailing slash to path."""
        if not self._has_trailing_slash(path):
            path += "/"
        return path

    def _remove_trailing_slash(self, path: str) -> str:
        """Remove trailing slash from path."""
        if self._has_trailing_slash(path):
            path = path[:-1]
        return path

    def _should_skip_processing(self, path: str) -> bool:
        """Check if path should be skipped from processing."""
        # Skip API paths, file extensions, query parameters, etc.
        skip_patterns = [
            ".",  # File extensions
            "?",  # Query parameters
            "#",  # Fragments
        ]

        return any(pattern in path for pattern in skip_patterns)

    async def process_request(
        self,
        request: Request,
        response: Response,
        call_next: Any,
    ) -> None:
        original_path = request.url.path

        # Skip processing for certain paths
        if self._should_skip_processing(original_path):
            await call_next()
            return

        # Normalize path (remove double slashes)
        normalized_path = self._normalize_path(original_path)
        # Handle trailing slashes
        if self.slash_action == SlashAction.IGNORE:
            # Just normalize double slashes
            if normalized_path != original_path:
                # Update the request path
                request.scope["path"] = normalized_path


        elif self.slash_action == SlashAction.ADD:
            # Add trailing slash
            if not self._has_trailing_slash(normalized_path):
                new_path = self._add_trailing_slash(normalized_path)
                request.scope["path"] = new_path

        elif self.slash_action == SlashAction.REMOVE:
            # Remove trailing slash
            if self._has_trailing_slash(normalized_path):
                new_path = self._remove_trailing_slash(normalized_path)
                request.scope["path"] = new_path

        elif self.slash_action in [SlashAction.REDIRECT_ADD, SlashAction.REDIRECT_REMOVE]:
            # Handle redirects
            should_redirect = False
            redirect_path = normalized_path

            if self.slash_action == SlashAction.REDIRECT_ADD:
                if not self._has_trailing_slash(normalized_path):
                    redirect_path = self._add_trailing_slash(normalized_path)
                    should_redirect = True

            elif self.slash_action == SlashAction.REDIRECT_REMOVE:
                if self._has_trailing_slash(normalized_path):
                    redirect_path = self._remove_trailing_slash(normalized_path)
                    should_redirect = True
            
            if should_redirect:
                # Build the redirect URL
                redirect_url = urlunparse((
                    request.url.scheme,
                    request.url.netloc,
                    redirect_path,
                    request.url.params,
                    request.url.query,
                    request.url.fragment
                ))

                # Return redirect response
                return response.redirect(redirect_url, status_code=self.redirect_status_code)
            

        await call_next()
