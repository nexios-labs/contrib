"""
Nexios Mail - Email Sending with Background Task Support

This module provides a robust and easy-to-use email sending solution for Nexios applications.
It includes features like SMTP configuration, template-based HTML emails, background task integration,
and dependency injection support.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from nexios import NexiosApp
from nexios.http import Request

from .client import MailClient
from .config import MailConfig
from .dependency import MailDepend, get_mail_client
from .models import EmailMessage, EmailResult
from .tasks import MailTaskManager, add_task_support, send_email_async, send_template_email_async

__all__ = [
    # Main classes
    'MailClient',
    'MailConfig',
    'EmailMessage',
    'EmailResult',
    
    # Dependency injection
    'MailDepend',
    'get_mail_client',
    
    # Background tasks
    'MailTaskManager',
    'add_task_support',
    'send_email_async',
    'send_template_email_async',
    
    # Setup functions
    'setup_mail',
    'get_mail_from_request',
]

def setup_mail(
    app: NexiosApp,
    config: Optional[MailConfig] = None
) -> MailClient:
    """Set up the mail client for a Nexios application.
    
    This function initializes the mail client and registers it with the Nexios app.
    It should be called during application startup.
    
    Args:
        app: The Nexios application instance.
        config: Optional configuration for the mail client.
        
    Returns:
        The initialized MailClient instance.
        
    Example:
        ```python
        from nexios import NexiosApp
        from nexios_contrib.mail import setup_mail, MailConfig
        
        app = NexiosApp()
        
        # Initialize with default configuration
        mail_client = setup_mail(app)
        
        # Or with custom configuration
        config = MailConfig(
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_username="your-email@gmail.com",
            smtp_password="your-app-password",
            use_tls=True
        )
        mail_client = setup_mail(app, config=config)
        ```
    """
    if not hasattr(app, 'mail_client'):
        mail_client = MailClient(config=config)
        app.mail_client = mail_client
        app.on_startup(mail_client.start)
        app.on_shutdown(mail_client.stop)
        
        # Add background task support if available
        try:
            add_task_support(mail_client)
        except Exception:
            # Tasks not available, continue without them
            pass
    
    return app.mail_client

def get_mail_from_request(request: Request) -> MailClient:
    """Get the mail client from a request.
    
    This is a convenience function to get the mail client instance
    from a request object.
    
    Args:
        request: The current request object.
        
    Returns:
        The MailClient instance.
        
    Raises:
        AttributeError: If the mail client is not initialized.
        
    Example:
        ```python
        from nexios import Request
        from nexios_contrib.mail import get_mail_from_request
        
        @app.post("/send-email")
        async def send_email_endpoint(request: Request):
            mail_client = get_mail_from_request(request)
            result = await mail_client.send_email(
                to="recipient@example.com",
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
    return mail_client
