"""
Mail Client Module

This module provides the main mail client implementation with SMTP support,
template rendering, and background task integration.
"""

from __future__ import annotations

import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    import jinja2
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False

from .config import MailConfig
from .models import EmailMessage, EmailResult, EmailError

logger = logging.getLogger(__name__)


class MailClient:
    """Main mail client for sending emails with SMTP and template support.
    
    This client provides a high-level interface for sending emails through SMTP
    servers, with support for HTML templates, attachments, and background tasks.
    
    Example:
        ```python
        from nexios_contrib.mail import MailClient, MailConfig
        
        config = MailConfig(
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_username="your-email@gmail.com",
            smtp_password="your-app-password",
            use_tls=True
        )
        
        mail_client = MailClient(config=config)
        await mail_client.start()
        
        result = await mail_client.send_email(
            to="recipient@example.com",
            subject="Hello World",
            body="This is a test email"
        )
        ```
    """
    
    def __init__(self, config: Optional[MailConfig] = None) -> None:
        """Initialize the mail client.
        
        Args:
            config: Optional mail configuration. If not provided, uses default config.
        """
        self.config = config or MailConfig()
        self._smtp_pool: Optional[smtplib.SMTP] = None
        self._template_env: Optional[jinja2.Environment] = None
        self._is_started = False
        
        # Setup template environment if Jinja2 is available
        if JINJA2_AVAILABLE and self.config.template_directory:
            self._setup_template_environment()
    
    def _setup_template_environment(self) -> None:
        """Setup the Jinja2 template environment."""
        if not self.config.template_directory:
            return
        
        template_path = Path(self.config.template_directory)
        if not template_path.exists():
            logger.warning(f"Template directory not found: {template_path}")
            return
        
        loader = jinja2.FileSystemLoader(str(template_path))
        self._template_env = jinja2.Environment(
            loader=loader,
            autoescape=self.config.template_auto_escape,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters
        self._template_env.filters["format_date"] = self._format_date_filter
    
    def _format_date_filter(self, value: Any, format_str: str = "%Y-%m-%d") -> str:
        """Jinja2 filter for formatting dates.
        
        Args:
            value: Date value to format.
            format_str: Date format string.
            
        Returns:
            Formatted date string.
        """
        if hasattr(value, "strftime"):
            return value.strftime(format_str)
        return str(value)
    
    async def start(self) -> None:
        """Start the mail client and initialize SMTP connection."""
        if self._is_started:
            return
        
        try:
            if not self.config.suppress_send:
                await self._create_smtp_connection()
            self._is_started = True
            logger.info("Mail client started successfully")
        except Exception as e:
            logger.error(f"Failed to start mail client: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the mail client and close SMTP connection."""
        if not self._is_started:
            return
        
        try:
            if self._smtp_pool:
                self._smtp_pool.quit()
                self._smtp_pool = None
            self._is_started = False
            logger.info("Mail client stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping mail client: {e}")
    
    async def _create_smtp_connection(self) -> None:
        """Create and configure SMTP connection."""
        if self.config.use_ssl:
            self._smtp_pool = smtplib.SMTP_SSL(
                self.config.smtp_host,
                self.config.smtp_port,
                timeout=self.config.smtp_timeout
            )
        else:
            self._smtp_pool = smtplib.SMTP(
                self.config.smtp_host,
                self.config.smtp_port,
                timeout=self.config.smtp_timeout
            )
            
            if self.config.use_tls:
                self._smtp_pool.starttls()
        
        # Enable debug mode if configured
        if self.config.debug:
            self._smtp_pool.set_debuglevel(1)
        
        # Authenticate if credentials are provided
        if self.config.smtp_username and self.config.smtp_password:
            try:
                self._smtp_pool.login(
                    self.config.smtp_username,
                    self.config.smtp_password
                )
                logger.info(f"SMTP authentication successful for {self.config.smtp_username}")
            except Exception as e:
                logger.error(f"SMTP authentication failed: {e}")
                raise
    
    async def send_email(
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
        **kwargs: Any
    ) -> EmailResult:
        """Send an email.
        
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
            **kwargs: Additional email parameters.
            
        Returns:
            EmailResult indicating success or failure.
        """
        # Create email message
        message = EmailMessage(
            to=to,
            subject=subject,
            body=body,
            html_body=html_body,
            from_email=from_email,
            reply_to=reply_to,
            cc=cc,
            bcc=bcc,
            template_name=template_name,
            template_context=template_context,
            **kwargs
        )
        
        # Add attachments if provided
        if attachments:
            for attachment in attachments:
                if isinstance(attachment, dict):
                    message.add_attachment(**attachment)
                else:
                    message.add_attachment(attachment)
        
        return await self.send_message(message)
    
    async def send_message(self, message: EmailMessage) -> EmailResult:
        """Send an EmailMessage.
        
        Args:
            message: The EmailMessage to send.
            
        Returns:
            EmailResult indicating success or failure.
        """
        try:
            # Render template if specified
            if message.template_name and self._template_env:
                await self._render_template(message)
            
            # Use default from email if not specified
            from_email = message.from_email or self.config.default_from
            if not from_email:
                raise ValueError("No 'from' email address specified")
            
            # Create MIME message
            mime_message = message.to_mime_message(from_email)
            
            # Add default CC/BCC if not specified
            if self.config.default_cc and not message.cc:
                mime_message["Cc"] = ", ".join(self.config.default_cc)
                message.cc.extend(self.config.default_cc)
            
            if self.config.default_bcc and not message.bcc:
                message.bcc.extend(self.config.default_bcc)
            
            # Prepare recipient list
            recipients = list(message.to)
            if message.cc:
                recipients.extend(message.cc)
            if message.bcc:
                recipients.extend(message.bcc)
            
            # Send email
            if self.config.suppress_send:
                logger.info(f"Email sending suppressed: {message.subject} to {recipients}")
                return EmailResult(
                    success=True,
                    message_id=message.message_id,
                    to=recipients,
                    subject=message.subject,
                    provider_response={"suppressed": True}
                )
            
            # Send in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._send_mime_message,
                mime_message,
                recipients
            )
            
            logger.info(f"Email sent successfully: {message.message_id} to {recipients}")
            
            return EmailResult(
                success=True,
                message_id=message.message_id,
                to=recipients,
                subject=message.subject
            )
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to send email: {error_msg}")
            
            return EmailResult(
                success=False,
                message_id=message.message_id,
                to=list(message.to),
                subject=message.subject,
                error=error_msg
            )
    
    def _send_mime_message(self, mime_message: MIMEMultipart, recipients: List[str]) -> None:
        """Send MIME message using SMTP.
        
        Args:
            mime_message: The MIME message to send.
            recipients: List of recipient email addresses.
        """
        if not self._smtp_pool:
            raise RuntimeError("SMTP connection not established")
        
        self._smtp_pool.sendmail(
            mime_message["From"],
            recipients,
            mime_message.as_string()
        )
    
    async def _render_template(self, message: EmailMessage) -> None:
        """Render email template.
        
        Args:
            message: The email message to render template for.
        """
        if not self._template_env or not message.template_name:
            return
        
        try:
            # Try to render HTML template
            html_template = self._template_env.get_template(f"{message.template_name}.html")
            message.html_body = html_template.render(**message.template_context)
            
            # Try to render text template
            try:
                text_template = self._template_env.get_template(f"{message.template_name}.txt")
                message.body = text_template.render(**message.template_context)
            except jinja2.TemplateNotFound:
                # Text template is optional
                pass
                
        except jinja2.TemplateNotFound as e:
            logger.error(f"Template not found: {e}")
            raise
        except jinja2.TemplateError as e:
            logger.error(f"Template rendering error: {e}")
            raise
    
    async def send_template_email(
        self,
        to: Union[str, List[str]],
        subject: str,
        template_name: str,
        context: Optional[Dict[str, Any]] = None,
        from_email: Optional[str] = None,
        **kwargs: Any
    ) -> EmailResult:
        """Send an email using a template.
        
        Args:
            to: Recipient email address(es).
            subject: Email subject.
            template_name: Name of the template to use.
            context: Template context variables.
            from_email: Sender email address.
            **kwargs: Additional email parameters.
            
        Returns:
            EmailResult indicating success or failure.
        """
        return await self.send_email(
            to=to,
            subject=subject,
            template_name=template_name,
            template_context=context,
            from_email=from_email,
            **kwargs
        )
    
    def create_message(
        self,
        to: Union[str, List[str]],
        subject: str,
        **kwargs: Any
    ) -> EmailMessage:
        """Create an EmailMessage object.
        
        Args:
            to: Recipient email address(es).
            subject: Email subject.
            **kwargs: Additional message parameters.
            
        Returns:
            EmailMessage instance.
        """
        return EmailMessage(to=to, subject=subject, **kwargs)
