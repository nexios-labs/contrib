# Nexios Mail

A powerful and easy-to-use email sending solution for Nexios applications with SMTP support, template integration, and background task processing.

## Features

- **SMTP Support**: Full SMTP configuration with TLS/SSL support
- **Template Integration**: Jinja2-based HTML email templates
- **Background Tasks**: Async email sending with nexios-contrib tasks
- **Dependency Injection**: Easy integration with Nexios applications
- **Multiple Providers**: Pre-configured settings for Gmail, Outlook, SendGrid
- **Attachments**: Support for file attachments and inline images
- **Error Handling**: Comprehensive error reporting and logging
- **Testing**: Full test coverage with mocking support

## Installation

```bash
# Basic installation
pip install nexios-contrib[mail]

# With template support
pip install nexios-contrib[mail,templating]

# With all features
pip install nexios-contrib[all]
```

## Quick Start

### Basic Setup

```python
from nexios import NexiosApp
from nexios_contrib.mail import setup_mail, MailConfig

app = NexiosApp()

# Setup with environment variables
mail_client = setup_mail(app)

# Or with custom configuration
config = MailConfig(
    smtp_host="smtp.gmail.com",
    smtp_port=587,
    smtp_username="your-email@gmail.com",
    smtp_password="your-app-password",
    use_tls=True,
    default_from="Your Name <your-email@gmail.com>"
)
mail_client = setup_mail(app, config=config)
```

### Environment Variables

```bash
# SMTP Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
SMTP_USE_SSL=false

# Email Defaults
MAIL_DEFAULT_FROM=Your Name <your-email@gmail.com>
MAIL_DEFAULT_REPLY_TO=support@yourcompany.com

# Template Directory
MAIL_TEMPLATE_DIR=templates/emails

# Debug Settings
MAIL_DEBUG=false
MAIL_SUPPRESS_SEND=false
```

## Usage Examples

### Sending Basic Emails

```python
from nexios import Request
from nexios_contrib.mail import MailDepend

@app.post("/send-email")
async def send_email(
    request: Request,
    mail_client: MailClient = MailDepend()
):
    result = await mail_client.send_email(
        to="user@example.com",
        subject="Welcome to Our Service",
        body="Thank you for joining our platform!",
        html_body="<h1>Welcome!</h1><p>Thank you for joining our platform!</p>"
    )
    
    return {
        "success": result.success,
        "message_id": result.message_id,
        "sent_at": result.sent_at.isoformat()
    }
```

### Using Email Templates

Create templates in your `templates/emails/` directory:

**templates/emails/welcome.html**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Welcome {{ name }}!</title>
</head>
<body>
    <h1>Welcome {{ name }}!</h1>
    <p>Thank you for joining {{ company_name }}.</p>
    <p>Your account has been created with email: {{ email }}</p>
    <a href="{{ activation_url }}">Activate Your Account</a>
</body>
</html>
```

**templates/emails/welcome.txt**
```text
Welcome {{ name }}!

Thank you for joining {{ company_name }}.
Your account has been created with email: {{ email }}.

Activate Your Account: {{ activation_url }}
```

Send template emails:

```python
@app.post("/send-welcome")
async def send_welcome_email(
    request: Request,
    mail_client: MailClient = MailDepend()
):
    result = await mail_client.send_template_email(
        to="newuser@example.com",
        subject="Welcome to Our Platform!",
        template_name="welcome",
        context={
            "name": "John Doe",
            "email": "newuser@example.com",
            "company_name": "Acme Corp",
            "activation_url": "https://example.com/activate/12345"
        }
    )
    
    return {"success": result.success, "message_id": result.message_id}
```

### Sending Emails with Attachments

```python
@app.post("/send-with-attachment")
async def send_with_attachment(
    request: Request,
    mail_client: MailClient = MailDepend()
):
    # Add file attachments
    result = await mail_client.send_email(
        to="user@example.com",
        subject="Your Document",
        body="Please find your document attached.",
        attachments=[
            {
                "filename": "document.pdf",
                "content": b"PDF content here",
                "content_type": "application/pdf"
            },
            {
                "filename": "image.png",
                "content": "path/to/image.png",  # File path also works
                "content_id": "logo"  # For inline images
            }
        ]
    )
    
    return {"success": result.success}
```

### Background Email Sending

Send emails asynchronously without blocking your API responses:

```python
from nexios_contrib.mail import send_email_async

@app.post("/send-async")
async def send_async_email(request: Request):
    task = await send_email_async(
        request=request,
        to="user@example.com",
        subject="Processing Your Request",
        body="We're processing your request and will notify you when complete."
    )
    
    return {
        "message": "Email queued for sending",
        "task_id": task.id if task else None
    }
```

### Bulk Email Sending

```python
@app.post("/send-bulk")
async def send_bulk_emails(
    request: Request,
    mail_client: MailClient = MailDepend()
):
    emails = [
        {
            "to": "user1@example.com",
            "subject": "Newsletter #1",
            "body": "Latest news...",
            "html_body": "<h1>Latest News</h1>..."
        },
        {
            "to": "user2@example.com",
            "subject": "Newsletter #1",
            "body": "Latest news...",
            "html_body": "<h1>Latest News</h1>..."
        }
    ]
    
    tasks = await mail_client.tasks.send_bulk_emails_async(emails)
    
    return {
        "queued_emails": len(tasks),
        "task_ids": [task.id for task in tasks if task]
    }
```

## Configuration

### MailConfig Options

```python
from nexios_contrib.mail import MailConfig

config = MailConfig(
    # SMTP Settings
    smtp_host="smtp.gmail.com",
    smtp_port=587,
    smtp_username="your-email@gmail.com",
    smtp_password="your-app-password",
    use_tls=True,
    use_ssl=False,
    
    # Email Defaults
    default_from="Your Name <your-email@gmail.com>",
    default_reply_to="support@yourcompany.com",
    default_cc=["admin@yourcompany.com"],
    default_bcc=["backup@yourcompany.com"],
    
    # Connection Settings
    smtp_timeout=30.0,
    max_connections=10,
    
    # Template Settings
    template_directory="templates/emails",
    template_auto_escape=True,
    
    # Background Task Settings
    use_background_tasks=True,
    task_timeout=300.0,
    
    # Debug Settings
    debug=False,
    suppress_send=False
)
```

### Provider-Specific Configurations

#### Gmail
```python
config = MailConfig.for_gmail(
    username="your-email@gmail.com",
    password="your-app-password",  # Use app password, not regular password
    default_from="Your Name <your-email@gmail.com>"
)
```

#### Outlook/Office 365
```python
config = MailConfig.for_outlook(
    username="your-email@outlook.com",
    password="your-password",
    default_from="Your Name <your-email@outlook.com>"
)
```

#### SendGrid
```python
config = MailConfig.for_sendgrid(
    api_key="your-sendgrid-api-key",
    default_from="your-email@yourdomain.com"
)
```

## Advanced Usage

### Custom Email Messages

```python
from nexios_contrib.mail import EmailMessage

# Create detailed email message
message = EmailMessage(
    to="recipient@example.com",
    subject="Custom Email",
    body="Plain text content",
    html_body="<h1>HTML Content</h1>",
    cc="manager@example.com",
    bcc="archive@example.com",
    priority=1  # High priority
)

# Add custom headers
message.add_header("X-Campaign-ID", "summer-2024")
message.add_header("X-Mailer", "Nexios Mail")

# Add attachments
message.add_attachment("report.pdf", b"PDF content", "application/pdf")

# Send the message
result = await mail_client.send_message(message)
```

### Template Custom Filters

```python
# Add custom Jinja2 filters
def format_currency(value, currency="USD"):
    return f"{value:.2f} {currency}"

# In your mail client setup
mail_client._template_env.filters["currency"] = format_currency

# Use in templates
{{ price | currency }}
```

### Error Handling

```python
try:
    result = await mail_client.send_email(
        to="user@example.com",
        subject="Test Email",
        body="Test content"
    )
    
    if result.success:
        print(f"Email sent: {result.message_id}")
    else:
        print(f"Email failed: {result.error}")
        
except Exception as e:
    print(f"Mail client error: {e}")
```

### Testing

```python
# Use suppress_send for testing
test_config = MailConfig(
    suppress_send=True,  # Don't actually send emails
    debug=True
)

mail_client = MailClient(config=test_config)
await mail_client.start()

# Emails will be logged but not sent
result = await mail_client.send_email(
    to="test@example.com",
    subject="Test",
    body="This won't be sent"
)

assert result.success is True
```

## API Reference

### MailClient

The main mail client class for sending emails.

#### Methods

- `send_email(to, subject, body=None, html_body=None, **kwargs)` - Send an email
- `send_message(message)` - Send an EmailMessage object
- `send_template_email(to, subject, template_name, context=None, **kwargs)` - Send template email
- `create_message(to, subject, **kwargs)` - Create EmailMessage object

### EmailMessage

Represents an email message with all its components.

#### Properties

- `to` - Recipient email addresses
- `subject` - Email subject
- `body` - Plain text body
- `html_body` - HTML body
- `attachments` - List of attachments
- `headers` - Custom headers

#### Methods

- `add_attachment(filename, content, content_type=None, content_id=None)` - Add attachment
- `set_template(template_name, context=None)` - Set template
- `add_header(name, value)` - Add custom header

### MailConfig

Configuration for the mail client.

#### Class Methods

- `for_gmail(username, password, **kwargs)` - Gmail configuration
- `for_outlook(username, password, **kwargs)` - Outlook configuration
- `for_sendgrid(api_key, **kwargs)` - SendGrid configuration

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Check SMTP credentials
   - For Gmail, use an App Password instead of your regular password
   - Verify 2FA settings

2. **Connection Timeout**
   - Check SMTP host and port
   - Verify firewall settings
   - Increase `smtp_timeout` value

3. **Template Not Found**
   - Verify template directory path
   - Check template file names and extensions
   - Ensure template files exist

4. **Background Tasks Not Working**
   - Install nexios-contrib tasks: `pip install nexios-contrib[tasks]`
   - Setup tasks in your app: `setup_tasks(app)`

### Debug Mode

Enable debug mode to see SMTP communication:

```python
config = MailConfig(
    debug=True,  # Enables SMTP debug logging
    suppress_send=True  # Test mode - don't actually send
)
```

## License

This project is licensed under the BSD-3-Clause License.
