<p align="center">
  <a href="https://github.com/nexios-labs">
    <img alt="Nexios Logo" height="220" src="https://nexios-docs.netlify.app/logo.png">
  </a>
</p>

<h1 align="center">Request ID Middleware for Nexios</h1>

A lightweight, production‑ready request ID middleware for the Nexios ASGI framework.

It automatically:

- Generates unique request IDs for all incoming requests
- Extracts request IDs from incoming request headers (`X-Request-ID`)
- Stores request IDs in request objects for later access
- Includes request IDs in response headers for better tracing
- Supports custom header names and configuration options

---

## Installation

```bash
pip install nexios_contrib
```

Or add it to your project's `pyproject.toml` dependencies as `nexios_contrib`.

---

## Quickstart

```python
from nexios import NexiosApp
import nexios_contrib.request_id as request_id

app = NexiosApp()

# Add the Request ID middleware (defaults shown)
app.add_middleware(
    request_id.RequestId(
        header_name="X-Request-ID",    # Header name for request ID
        force_generate=False,          # Use existing request ID if provided
        store_in_request=True,         # Store request ID in request object
        include_in_response=True       # Include request ID in response headers
    )
)

@app.get("/")
async def home(request, response):
    # Access request ID from request object
    req_id = getattr(request, 'request_id', None)
    return {"message": "Hello with Request ID!", "request_id": req_id}
```

That's it. Every request will now have a unique request ID that can be used for tracing and debugging.

---

## Usage

### Basic Usage

```python
from nexios import NexiosApp
from nexios_contrib.request_id import RequestId

app = NexiosApp()

# Add middleware with default settings
app.add_middleware(RequestId())
```

### Custom Configuration

```python
from nexios import NexiosApp
from nexios_contrib.request_id import RequestId

app = NexiosApp()

# Custom configuration
app.add_middleware(
    RequestId(
        header_name="X-Correlation-ID",  # Use different header name
        force_generate=True,             # Always generate new request ID
        store_in_request=True,           # Store in request object
        include_in_response=True,        # Include in response headers
        request_attribute_name="req_id"  # Custom attribute name
    )
)
```

### Using Helper Functions

```python
from nexios_contrib.request_id import (
    generate_request_id,
    get_or_generate_request_id,
    validate_request_id
)

# Generate a new request ID
new_id = generate_request_id()

# Get or generate request ID from request
req_id = get_or_generate_request_id(request)

# Validate request ID format
is_valid = validate_request_id(some_request_id)
```

### Accessing Request ID in Handlers

```python
@app.get("/api/users")
async def get_users(request, response):
    # Method 1: Get from request object
    request_id = getattr(request, 'request_id', None)

    # Method 2: Extract from headers
    request_id = request.headers.get('X-Request-ID')

    # Method 3: Use helper function
    from nexios_contrib.request_id import get_request_id_from_request
    request_id = get_request_id_from_request(request)

    return {"users": [], "request_id": request_id}
```

---

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `header_name` | `str` | `"X-Request-ID"` | Header name to use for request ID extraction and setting |
| `force_generate` | `bool` | `False` | Always generate new request ID instead of using existing one |
| `store_in_request` | `bool` | `True` | Store request ID in request object for later access |
| `request_attribute_name` | `str` | `"request_id"` | Attribute name to store request ID in request object |
| `include_in_response` | `bool` | `True` | Include request ID in response headers |

---

## Features

- **Automatic Generation**: Generates UUID4-based request IDs automatically
- **Header Support**: Extracts request IDs from incoming request headers
- **Request Storage**: Stores request IDs in request objects for easy access
- **Response Headers**: Includes request IDs in response headers for client-side tracing
- **Customizable**: Highly configurable with various options for different use cases
- **Validation**: Built-in validation for request ID format
- **Thread Safe**: Safe for use in concurrent ASGI applications

---

## Best Practices

1. **Always include request IDs in logs** for better debugging and tracing
2. **Use consistent header names** across your microservices
3. **Store request IDs early** in the middleware chain to ensure they're available to all handlers
4. **Consider using different header names** for internal vs external request IDs
5. **Validate request IDs** from external sources before using them

---

## Examples

### Logging with Request ID

```python
import logging
from nexios_contrib.request_id import RequestId

app = NexiosApp()
app.add_middleware(RequestId())

@app.get("/api/data")
async def get_data(request, response):
    request_id = getattr(request, 'request_id', None)
    logging.info(f"Processing request {request_id}")

    # Your handler logic here
    return {"data": "example", "request_id": request_id}
```

### Custom Request ID Format

```python
from nexios_contrib.request_id import RequestIdMiddleware

class CustomRequestIdMiddleware(RequestIdMiddleware):
    def __init__(self, prefix: str = "req", **kwargs):
        super().__init__(**kwargs)
        self.prefix = prefix

    async def process_request(self, request, response, call_next):
        # Generate custom request ID with prefix
        import uuid
        request_id = f"{self.prefix}-{uuid.uuid4().hex[:8]}"

        # Store in request object
        setattr(request, 'request_id', request_id)

        # Set in response headers
        response.headers['X-Request-ID'] = request_id

        return await call_next()

app.add_middleware(CustomRequestIdMiddleware(prefix="api"))
```

---

## Contributing

Contributions are welcome! Please see the main Nexios contrib repository for contribution guidelines.

---

## License

This module is part of the Nexios contrib package and follows the same license as the main Nexios framework.
