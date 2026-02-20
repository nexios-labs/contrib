"""
Mail Configuration Module

This module provides configuration classes for the mail client,
including SMTP settings and template configuration.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Union


@dataclass
class MailConfig:
    """Configuration for the mail client.
    
    This class contains all the settings needed to configure
    the SMTP connection and email sending behavior.
    """
    
    # SMTP Configuration
    smtp_host: str = field(default_factory=lambda: os.getenv("SMTP_HOST", "localhost"))
    smtp_port: int = field(default_factory=lambda: int(os.getenv("SMTP_PORT", "587")))
    smtp_username: Optional[str] = field(default_factory=lambda: os.getenv("SMTP_USERNAME"))
    smtp_password: Optional[str] = field(default_factory=lambda: os.getenv("SMTP_PASSWORD"))
    use_tls: bool = field(default_factory=lambda: os.getenv("SMTP_USE_TLS", "true").lower() == "true")
    use_ssl: bool = field(default_factory=lambda: os.getenv("SMTP_USE_SSL", "false").lower() == "true")
    
    # Email defaults
    default_from: Optional[str] = field(default_factory=lambda: os.getenv("MAIL_DEFAULT_FROM"))
    default_reply_to: Optional[str] = field(default_factory=lambda: os.getenv("MAIL_DEFAULT_REPLY_TO"))
    default_cc: Optional[List[str]] = None
    default_bcc: Optional[List[str]] = None
    
    # Connection settings
    smtp_timeout: float = field(default_factory=lambda: float(os.getenv("SMTP_TIMEOUT", "30")))
    max_connections: int = field(default_factory=lambda: int(os.getenv("SMTP_MAX_CONNECTIONS", "10")))
    
    # Template settings
    template_directory: Optional[str] = field(default_factory=lambda: os.getenv("MAIL_TEMPLATE_DIR"))
    template_auto_escape: bool = True
    
    # Background task settings
    use_background_tasks: bool = True
    task_timeout: Optional[float] = field(default_factory=lambda: float(os.getenv("MAIL_TASK_TIMEOUT", "300")))
    
    # Debug settings
    debug: bool = field(default_factory=lambda: os.getenv("MAIL_DEBUG", "false").lower() == "true")
    suppress_send: bool = field(default_factory=lambda: os.getenv("MAIL_SUPPRESS_SEND", "false").lower() == "true")
    
    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.use_ssl and self.use_tls:
            raise ValueError("Cannot use both SSL and TLS. Choose one.")
        
        if self.smtp_port == 465 and not self.use_ssl:
            # Port 465 is typically used for SSL
            self.use_ssl = True
            self.use_tls = False
        elif self.smtp_port == 587 and not self.use_tls:
            # Port 587 is typically used for TLS
            self.use_tls = True
            self.use_ssl = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.
        
        Returns:
            Dictionary representation of the configuration.
        """
        return {
            "smtp_host": self.smtp_host,
            "smtp_port": self.smtp_port,
            "smtp_username": self.smtp_username,
            "smtp_password": "***" if self.smtp_password else None,
            "use_tls": self.use_tls,
            "use_ssl": self.use_ssl,
            "default_from": self.default_from,
            "default_reply_to": self.default_reply_to,
            "default_cc": self.default_cc,
            "default_bcc": self.default_bcc,
            "smtp_timeout": self.smtp_timeout,
            "max_connections": self.max_connections,
            "template_directory": self.template_directory,
            "template_auto_escape": self.template_auto_escape,
            "use_background_tasks": self.use_background_tasks,
            "task_timeout": self.task_timeout,
            "debug": self.debug,
            "suppress_send": self.suppress_send,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MailConfig:
        """Create configuration from dictionary.
        
        Args:
            data: Dictionary containing configuration values.
            
        Returns:
            MailConfig instance.
        """
        return cls(**data)
    
    @classmethod
    def for_gmail(cls, username: str, password: str, **kwargs: Any) -> MailConfig:
        """Create configuration for Gmail SMTP.
        
        Args:
            username: Gmail username or email address.
            password: Gmail app password (not regular password).
            **kwargs: Additional configuration options.
            
        Returns:
            MailConfig configured for Gmail.
        """
        return cls(
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_username=username,
            smtp_password=password,
            use_tls=True,
            **kwargs
        )
    
    @classmethod
    def for_outlook(cls, username: str, password: str, **kwargs: Any) -> MailConfig:
        """Create configuration for Outlook/Office 365 SMTP.
        
        Args:
            username: Outlook username or email address.
            password: Outlook password.
            **kwargs: Additional configuration options.
            
        Returns:
            MailConfig configured for Outlook.
        """
        return cls(
            smtp_host="smtp-mail.outlook.com",
            smtp_port=587,
            smtp_username=username,
            smtp_password=password,
            use_tls=True,
            **kwargs
        )
    
    @classmethod
    def for_sendgrid(cls, api_key: str, **kwargs: Any) -> MailConfig:
        """Create configuration for SendGrid SMTP.
        
        Args:
            api_key: SendGrid API key.
            **kwargs: Additional configuration options.
            
        Returns:
            MailConfig configured for SendGrid.
        """
        return cls(
            smtp_host="smtp.sendgrid.net",
            smtp_port=587,
            smtp_username="apikey",
            smtp_password=api_key,
            use_tls=True,
            **kwargs
        )
