"""
Mail Dependency Injection Module

This module provides dependency injection support for the mail client,
allowing it to be easily integrated with Nexios applications.
"""

from __future__ import annotations

from typing import Optional, TypeVar, cast

from nexios.dependencies import Depend, current_context
from nexios.http import Request

from .client import MailClient

T = TypeVar("T")


class MailDepend(Depend[MailClient]):
    """Dependency provider for the mail client.
    
    This class provides a dependency injection wrapper for the mail client,
    allowing it to be easily injected into route handlers and other components.
    
    Example:
        ```python
        from nexios_contrib.mail import MailDepend
        
        @app.post("/send-email")
        async def send_email(
            mail_client: MailClient = MailDepend()
        ):
            result = await mail_client.send_email(
                to="user@example.com",
                subject="Hello",
                body="This is a test email"
            )
            return {"status": "sent", "message_id": result.message_id}
        ```
    """
    
    def __init__(self) -> None:
        """Initialize the mail dependency."""
        super().__init__(self._get_mail_client)
    
    async def _get_mail_client(self) -> MailClient:
        """Get the mail client from the current context.
        
        Returns:
            The MailClient instance from the current request context.
            
        Raises:
            RuntimeError: If no mail client is found in the context.
        """
        try:
            ctx = current_context.get()
            if ctx and ctx.request:
                return get_mail_from_request(ctx.request)
        except LookupError:
            pass
        
        raise RuntimeError(
            "Mail client not found in current context. "
            "Make sure setup_mail(app) was called during application startup."
        )


def get_mail_client(request: Request) -> MailClient:
    """Get the mail client from a request.
    
    This is a convenience function that retrieves the mail client
    from the Nexios application instance attached to the request.
    
    Args:
        request: The current request object.
        
    Returns:
        The MailClient instance.
        
    Raises:
        AttributeError: If the mail client is not initialized.
        
    Example:
        ```python
        from nexios import Request
        from nexios_contrib.mail import get_mail_client
        
        @app.post("/send-email")
        async def send_email(request: Request):
            mail_client = get_mail_client(request)
            result = await mail_client.send_email(
                to="user@example.com",
                subject="Hello",
                body="This is a test email"
            )
            return {"status": "sent", "message_id": result.message_id}
        ```
    """
    mail_client = getattr(request.base_app, 'mail_client', None)
    if mail_client is None:
        raise AttributeError(
            "Mail client not initialized. Call setup_mail(app) during application startup."
        )
    return cast(MailClient, mail_client)


def get_mail_from_request(request: Request) -> MailClient:
    """Alias for get_mail_client for backward compatibility.
    
    Args:
        request: The current request object.
        
    Returns:
        The MailClient instance.
    """
    return get_mail_client(request)
