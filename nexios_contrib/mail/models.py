"""
Mail Models Module

This module contains data models for email messages and results.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


@dataclass
class EmailAttachment:
    """Represents an email attachment."""
    
    filename: str
    content: Union[bytes, str]
    content_type: Optional[str] = None
    content_id: Optional[str] = None  # For inline images
    
    def __post_init__(self) -> None:
        """Validate and process attachment after initialization."""
        if isinstance(self.content, str):
            # If content is a string, assume it's a file path
            path = Path(self.content)
            if path.exists():
                self.content = path.read_bytes()
                if not self.content_type:
                    # Guess content type from file extension
                    import mimetypes
                    self.content_type, _ = mimetypes.guess_type(str(path))
            else:
                raise FileNotFoundError(f"Attachment file not found: {self.content}")
        
        if not self.content_type:
            self.content_type = "application/octet-stream"


@dataclass
class EmailMessage:
    """Represents an email message."""
    
    # Required fields
    to: Union[str, List[str]]
    subject: str
    
    # Content fields
    body: Optional[str] = None
    html_body: Optional[str] = None
    template_name: Optional[str] = None
    template_context: Optional[Dict[str, Any]] = None
    
    # Optional fields
    from_email: Optional[str] = None
    reply_to: Optional[Union[str, List[str]]] = None
    cc: Optional[Union[str, List[str]]] = None
    bcc: Optional[Union[str, List[str]]] = None
    attachments: Optional[List[EmailAttachment]] = None
    
    # Metadata
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    headers: Optional[Dict[str, str]] = None
    priority: Optional[int] = None  # 1 (high), 3 (normal), 5 (low)
    
    def __post_init__(self) -> None:
        """Normalize and validate email addresses after initialization."""
        # Normalize single addresses to lists
        if isinstance(self.to, str):
            self.to = [self.to]
        
        if isinstance(self.cc, str):
            self.cc = [self.cc]
        elif self.cc is None:
            self.cc = []
            
        if isinstance(self.bcc, str):
            self.bcc = [self.bcc]
        elif self.bcc is None:
            self.bcc = []
            
        if isinstance(self.reply_to, str):
            self.reply_to = [self.reply_to]
        elif self.reply_to is None:
            self.reply_to = []
        
        # Initialize empty lists/dicts if None
        if self.attachments is None:
            self.attachments = []
        if self.headers is None:
            self.headers = {}
        if self.template_context is None:
            self.template_context = {}
    
    def add_attachment(
        self,
        filename: str,
        content: Union[bytes, str],
        content_type: Optional[str] = None,
        content_id: Optional[str] = None
    ) -> None:
        """Add an attachment to the email.
        
        Args:
            filename: Name of the attachment file.
            content: File content as bytes or file path string.
            content_type: MIME content type.
            content_id: Content ID for inline images.
        """
        if self.attachments is None:
            self.attachments = []
        
        attachment = EmailAttachment(
            filename=filename,
            content=content,
            content_type=content_type,
            content_id=content_id
        )
        self.attachments.append(attachment)
    
    def set_template(self, template_name: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Set the template for the email.
        
        Args:
            template_name: Name of the template file.
            context: Template context variables.
        """
        self.template_name = template_name
        if context:
            self.template_context = {**self.template_context, **context}
    
    def add_header(self, name: str, value: str) -> None:
        """Add a custom header to the email.
        
        Args:
            name: Header name.
            value: Header value.
        """
        if self.headers is None:
            self.headers = {}
        self.headers[name] = value
    
    def to_mime_message(self, from_email: Optional[str] = None) -> MIMEMultipart:
        """Convert the email message to a MIME message.
        
        Args:
            from_email: Override the from email address.
            
        Returns:
            MIMEMultipart message ready for sending.
        """
        # Create the main message
        msg = MIMEMultipart("alternative")
        
        # Set headers
        msg["Subject"] = self.subject
        msg["To"] = ", ".join(self.to)
        msg["From"] = from_email or self.from_email or ""
        msg["Message-ID"] = self.message_id
        
        # Set optional headers
        if self.cc:
            msg["Cc"] = ", ".join(self.cc)
        
        if self.reply_to:
            msg["Reply-To"] = ", ".join(self.reply_to)
        
        if self.priority:
            priority_map = {1: "High", 3: "Normal", 5: "Low"}
            msg["X-Priority"] = str(self.priority)
            msg["Priority"] = priority_map.get(self.priority, "Normal")
        
        # Add custom headers
        if self.headers:
            for name, value in self.headers.items():
                msg[name] = value
        
        # Add body parts
        if self.body:
            text_part = MIMEText(self.body, "plain", "utf-8")
            msg.attach(text_part)
        
        if self.html_body:
            html_part = MIMEText(self.html_body, "html", "utf-8")
            msg.attach(html_part)
        
        # Add attachments
        if self.attachments:
            for attachment in self.attachments:
                part = MIMEBase(*attachment.content_type.split("/", 1))
                part.set_payload(attachment.content)
                import email.encoders
                email.encoders.encode_base64(part)
                
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={attachment.filename}"
                )
                
                if attachment.content_id:
                    part.add_header("Content-ID", f"<{attachment.content_id}>")
                
                msg.attach(part)
        
        return msg


@dataclass
class EmailResult:
    """Represents the result of sending an email."""
    
    success: bool
    message_id: str
    to: List[str]
    subject: str
    sent_at: datetime = field(default_factory=datetime.utcnow)
    error: Optional[str] = None
    provider_response: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary.
        
        Returns:
            Dictionary representation of the result.
        """
        return {
            "success": self.success,
            "message_id": self.message_id,
            "to": self.to,
            "subject": self.subject,
            "sent_at": self.sent_at.isoformat(),
            "error": self.error,
            "provider_response": self.provider_response,
        }


@dataclass
class EmailError:
    """Represents an email sending error."""
    
    message: str
    error_code: Optional[str] = None
    provider: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    
    def __str__(self) -> str:
        """String representation of the error."""
        if self.error_code:
            return f"{self.provider} Error [{self.error_code}]: {self.message}"
        return self.message
