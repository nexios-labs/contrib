"""
Mail Background Tasks Module

This module provides background task integration for email sending,
allowing emails to be sent asynchronously without blocking the main application.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Union

from nexios.http import Request

try:
    from ..tasks import create_task, Task
    TASKS_AVAILABLE = True
except ImportError:
    TASKS_AVAILABLE = False

from .client import MailClient
from .models import EmailMessage, EmailResult

logger = logging.getLogger(__name__)


class MailTaskManager:
    """Manager for email background tasks.
    
    This class provides methods to send emails in the background
    using the nexios-contrib tasks system.
    """
    
    def __init__(self, mail_client: MailClient) -> None:
        """Initialize the mail task manager.
        
        Args:
            mail_client: The mail client instance.
        """
        self.mail_client = mail_client
    
    async def send_email_async(
        self,
        to: Union[str, List[str]],
        subject: str,
        body: Optional[str] = None,
        html_body: Optional[str] = None,
        from_email: Optional[str] = None,
        reply_to: Optional[Union[str, List[str]]] = None,
        cc: Optional[Union[str, List[str]]] = None,
        bcc: Optional[Union[str, List[str]]] = None,
        attachments: Optional[List[Any]] = None,
        template_name: Optional[str] = None,
        template_context: Optional[Dict[str, Any]] = None,
        priority: str = "normal",
        timeout: Optional[float] = None,
        **kwargs: Any
    ) -> Optional[Task]:
        """Send an email in the background.
        
        Args:
            to: Recipient email address(es).
            subject: Email subject.
            body: Plain text email body.
            html_body: HTML email body.
            from_email: Sender email address.
            reply_to: Reply-to email address(es).
            cc: CC recipient(s).
            bcc: BCC recipient(s).
            attachments: List of file attachments.
            template_name: Name of the template to use.
            template_context: Context variables for the template.
            priority: Task priority ("low", "normal", "high").
            timeout: Task timeout in seconds.
            **kwargs: Additional email parameters.
            
        Returns:
            Task instance if tasks are available, None otherwise.
        """
        if not TASKS_AVAILABLE:
            logger.warning("Background tasks not available, sending email synchronously")
            await self.mail_client.send_email(
                to=to,
                subject=subject,
                body=body,
                html_body=html_body,
                from_email=from_email,
                reply_to=reply_to,
                cc=cc,
                bcc=bcc,
                attachments=attachments,
                template_name=template_name,
                template_context=template_context,
                **kwargs
            )
            return None
        
        # Create the background task
        task = await create_task(
            self._send_email_task,
            to=to,
            subject=subject,
            body=body,
            html_body=html_body,
            from_email=from_email,
            reply_to=reply_to,
            cc=cc,
            bcc=bcc,
            attachments=attachments,
            template_name=template_name,
            template_context=template_context,
            name=f"send_email_{subject}",
            timeout=timeout or self.mail_client.config.task_timeout
        )
        
        logger.info(f"Email task created: {task.id} for {subject}")
        return task
    
    async def send_message_async(
        self,
        message: EmailMessage,
        priority: str = "normal",
        timeout: Optional[float] = None
    ) -> Optional[Task]:
        """Send an EmailMessage in the background.
        
        Args:
            message: The EmailMessage to send.
            priority: Task priority ("low", "normal", "high").
            timeout: Task timeout in seconds.
            
        Returns:
            Task instance if tasks are available, None otherwise.
        """
        if not TASKS_AVAILABLE:
            logger.warning("Background tasks not available, sending message synchronously")
            await self.mail_client.send_message(message)
            return None
        
        # Create the background task
        task = await create_task(
            self._send_message_task,
            message,
            name=f"send_message_{message.subject}",
            timeout=timeout or self.mail_client.config.task_timeout
        )
        
        logger.info(f"Email message task created: {task.id} for {message.subject}")
        return task
    
    async def send_template_email_async(
        self,
        to: Union[str, List[str]],
        subject: str,
        template_name: str,
        context: Optional[Dict[str, Any]] = None,
        from_email: Optional[str] = None,
        priority: str = "normal",
        timeout: Optional[float] = None,
        **kwargs: Any
    ) -> Optional[Task]:
        """Send a template email in the background.
        
        Args:
            to: Recipient email address(es).
            subject: Email subject.
            template_name: Name of the template to use.
            context: Template context variables.
            from_email: Sender email address.
            priority: Task priority ("low", "normal", "high").
            timeout: Task timeout in seconds.
            **kwargs: Additional email parameters.
            
        Returns:
            Task instance if tasks are available, None otherwise.
        """
        if not TASKS_AVAILABLE:
            logger.warning("Background tasks not available, sending template email synchronously")
            await self.mail_client.send_template_email(
                to=to,
                subject=subject,
                template_name=template_name,
                context=context,
                from_email=from_email,
                **kwargs
            )
            return None
        
        # Create the background task
        task = await create_task(
            self._send_template_email_task,
            to=to,
            subject=subject,
            template_name=template_name,
            context=context,
            from_email=from_email,
            name=f"send_template_email_{subject}",
            timeout=timeout or self.mail_client.config.task_timeout,
            **kwargs
        )
        
        logger.info(f"Template email task created: {task.id} for {subject}")
        return task
    
    async def _send_email_task(self, *args: Any, **kwargs: Any) -> EmailResult:
        """Background task for sending emails.
        
        Args:
            *args: Positional arguments for send_email.
            **kwargs: Keyword arguments for send_email.
            
        Returns:
            EmailResult from the mail client.
        """
        try:
            result = await self.mail_client.send_email(*args, **kwargs)
            if result.success:
                logger.info(f"Background email sent successfully: {result.message_id}")
            else:
                logger.error(f"Background email failed: {result.error}")
            return result
        except Exception as e:
            logger.error(f"Background email task error: {e}")
            raise
    
    async def _send_message_task(self, message: EmailMessage) -> EmailResult:
        """Background task for sending EmailMessage.
        
        Args:
            message: The EmailMessage to send.
            
        Returns:
            EmailResult from the mail client.
        """
        try:
            result = await self.mail_client.send_message(message)
            if result.success:
                logger.info(f"Background message sent successfully: {result.message_id}")
            else:
                logger.error(f"Background message failed: {result.error}")
            return result
        except Exception as e:
            logger.error(f"Background message task error: {e}")
            raise
    
    async def _send_template_email_task(
        self,
        to: Union[str, List[str]],
        subject: str,
        template_name: str,
        context: Optional[Dict[str, Any]] = None,
        from_email: Optional[str] = None,
        **kwargs: Any
    ) -> EmailResult:
        """Background task for sending template emails.
        
        Args:
            to: Recipient email address(es).
            subject: Email subject.
            template_name: Name of the template to use.
            context: Template context variables.
            from_email: Sender email address.
            **kwargs: Additional email parameters.
            
        Returns:
            EmailResult from the mail client.
        """
        try:
            result = await self.mail_client.send_template_email(
                to=to,
                subject=subject,
                template_name=template_name,
                context=context,
                from_email=from_email,
                **kwargs
            )
            if result.success:
                logger.info(f"Background template email sent successfully: {result.message_id}")
            else:
                logger.error(f"Background template email failed: {result.error}")
            return result
        except Exception as e:
            logger.error(f"Background template email task error: {e}")
            raise


# Add task manager to mail client
def add_task_support(mail_client: MailClient) -> MailTaskManager:
    """Add background task support to a mail client.
    
    Args:
        mail_client: The mail client to extend.
        
    Returns:
        MailTaskManager instance.
    """
    task_manager = MailTaskManager(mail_client)
    mail_client.tasks = task_manager
    return task_manager


# Convenience functions for background email sending
async def send_email_async(
    request: Request,
    to: Union[str, List[str]],
    subject: str,
    **kwargs: Any
) -> Optional[Task]:
    """Send an email in the background from a request context.
    
    Args:
        request: The current request object.
        to: Recipient email address(es).
        subject: Email subject.
        **kwargs: Additional email parameters.
        
    Returns:
        Task instance if tasks are available, None otherwise.
    """
    from . import get_mail_from_request
    
    mail_client = get_mail_from_request(request)
    
    if not hasattr(mail_client, 'tasks'):
        add_task_support(mail_client)
    
    return await mail_client.tasks.send_email_async(to=to, subject=subject, **kwargs)


async def send_template_email_async(
    request: Request,
    to: Union[str, List[str]],
    subject: str,
    template_name: str,
    context: Optional[Dict[str, Any]] = None,
    **kwargs: Any
) -> Optional[Task]:
    """Send a template email in the background from a request context.
    
    Args:
        request: The current request object.
        to: Recipient email address(es).
        subject: Email subject.
        template_name: Name of the template to use.
        context: Template context variables.
        **kwargs: Additional email parameters.
        
    Returns:
        Task instance if tasks are available, None otherwise.
    """
    from . import get_mail_from_request
    
    mail_client = get_mail_from_request(request)
    
    if not hasattr(mail_client, 'tasks'):
        add_task_support(mail_client)
    
    return await mail_client.tasks.send_template_email_async(
        to=to,
        subject=subject,
        template_name=template_name,
        context=context,
        **kwargs
    )
