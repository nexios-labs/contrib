<p align="center">
  <a href="https://github.com/nexios-labs">
    <img alt="Nexios Logo" height="220" src="https://nexios-docs.netlify.app/logo.png">
  </a>
</p>
<h1 align="center">Timeout for Nexios</h1>

Timeout middleware and utilities for [Nexios](https://nexios-docs.netlify.app/) web framework, providing flexible request timeout handling, duration tracking, and timeout-based control flow.

## Features

- ⏱️ **Global and Per-Request Timeouts**: Set timeouts at both application and request levels
- 🔍 **Automatic Timeout Extraction**: Extract timeout values from headers or query parameters
- ⚡ **Async Timeout Control**: Built-in support for async/await patterns
- 📊 **Request Duration Tracking**: Monitor how long requests take to process
- 🛠️ **Flexible Error Handling**: Customize timeout responses or raise exceptions
- 🔄 **Timeout Utilities**: Helper functions for common timeout-related tasks

## Installation

```bash
# Install with pip
pip install nexios-contrib

# Or with uv (recommended)
uv add nexios-contrib
```

## Quick Start

### Basic Usage

```python
from nexios import NexiosApp
from nexios_contrib.timeout import Timeout

app = NexiosApp()

# Add timeout middleware with default 30s timeout
app.add_middleware(Timeout(default_timeout=30.0))

@app.get("/slow-endpoint")
async def slow_endpoint():
    # This will be automatically interrupted if it takes longer than 30 seconds
    await asyncio.sleep(35)
    return {"message": "This will never be reached"}
```

### Per-Request Timeout

```python
from nexios import NexiosApp, Request
from nexios_contrib.timeout import Timeout, get_timeout_from_request

app = NexiosApp()
app.add_middleware(Timeout())

@app.get("/api/data")
async def get_data(request: Request):
    # Get timeout from request headers or query params
    timeout = get_timeout_from_request(request, default_timeout=10.0)
    
    # Use the timeout for your operations
    try:
        result = await some_operation()
        return {"data": result}
    except asyncio.TimeoutError:
        return {"error": "Operation timed out"}
```

## Configuration Options

### Timeout Middleware

The `Timeout` middleware accepts the following parameters:

```python
app.add_middleware(
    Timeout(
        default_timeout=30.0,      # Default timeout in seconds
        max_timeout=300.0,         # Maximum allowed timeout (None for no limit)
        min_timeout=0.1,           # Minimum allowed timeout
        timeout_header="X-Request-Timeout",  # Header to check for timeout
        timeout_param="timeout",   # Query parameter to check for timeout
        track_duration=True,       # Add X-Request-Duration header
        timeout_response_enabled=True,  # Return timeout responses
        exception_on_timeout=False  # Raise exception instead of returning response
    )
)
```

### Timeout Sources

Timeouts can be specified in multiple ways (in order of precedence):

1. **Request Header**: `X-Request-Timeout: 5.0`
2. **Query Parameter**: `?timeout=5.0`
3. **Default Timeout**: As specified in middleware configuration

## Advanced Usage

### Using the Timeout Decorator

```python
from nexios_contrib.timeout import timeout_after, TimeoutException

@timeout_after(5.0)  # 5 second timeout
async def fetch_data():
    # This will raise TimeoutException if it takes longer than 5 seconds
    return await some_long_running_operation()

# In your route handler
@app.get("/fetch")
async def get_data():
    try:
        data = await fetch_data()
        return {"data": data}
    except TimeoutException as e:
        return {"error": str(e)}
```

### Timeout with Fallback

```python
from nexios_contrib.timeout import timeout_with_fallback

@app.get("/cached-data")
async def get_cached_data():
    # Try to get fresh data, fall back to cache if it takes too long
    data = await timeout_with_fallback(
        fetch_fresh_data(),  # Primary data source
        timeout=2.0,         # 2 second timeout
        fallback_value=get_cached_version(),  # Fallback value
        fallback_exception=None  # Or raise an exception instead
    )
    return {"data": data}
```

### Custom Timeout Response

```python
from nexios.http import Response
from nexios_contrib.timeout import create_timeout_response

@app.exception_handler(TimeoutException)
async def timeout_exception_handler(request, exc):
    return create_timeout_response(
        timeout=exc.timeout,
        detail={
            "error": "Request Timeout",
            "message": f"The request took longer than {exc.timeout} seconds",
            "status_code": 408
        }
    )
```

## Request Duration Tracking

When `track_duration` is enabled, the middleware adds an `X-Request-Duration` header to responses:

```
X-Request-Duration: 1.234s
```

## Best Practices

1. **Set Reasonable Timeouts**: Always set appropriate timeouts for your application's needs.
2. **Graceful Degradation**: Use fallbacks when operations time out.
3. **Monitor Timeouts**: Track timeout occurrences to identify performance issues.
4. **Document Timeout Behavior**: Let API consumers know about timeout behavior and limits.

## API Reference

### Classes

- `Timeout`: Middleware for request timeout handling
- `TimeoutException`: Exception raised on timeouts

### Functions

- `timeout_after`: Decorator for adding timeouts to async functions
- `timeout_with_fallback`: Execute with timeout and fallback
- `get_timeout_from_request`: Extract timeout from request
- `create_timeout_response`: Create a timeout error response
- `is_timeout_error`: Check if an exception is timeout-related
- `format_timeout_duration`: Format duration in human-readable format
- `get_request_duration`: Get request processing duration
- `set_request_start_time`: Set request start time for duration tracking
