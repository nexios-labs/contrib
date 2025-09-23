# Nexios Accepts Middleware with Dependency Injection

This document describes the enhanced accepts middleware for Nexios that includes dependency injection capabilities, similar to the request_id middleware pattern.

## Overview

The accepts middleware now provides a dependency injection system that allows you to easily access parsed Accept header information in your route handlers. This follows the same pattern as the request_id middleware, making it consistent and easy to use.

## Key Features

- **Dependency Injection**: Use `AcceptsDepend()` to inject parsed accepts information into route handlers
- **Easy Access**: Access parsed Accept headers, Accept-Language, Accept-Charset, and Accept-Encoding
- **Content Negotiation**: Built-in methods for negotiating content types, languages, charsets, and encodings
- **Consistent API**: Follows the same pattern as other Nexios contrib modules

## Installation

The accepts middleware is part of the `nexios_contrib` package:

```python
from nexios_contrib.accepts import Accepts, AcceptsDepend, AcceptsInfo
```

## Basic Usage

### 1. Add Middleware

```python
from nexios import NexiosApp
from nexios_contrib.accepts import Accepts

app = NexiosApp()
app.add_middleware(Accepts())
```

### 2. Use Dependency Injection in Routes

```python
@app.get("/api/content")
async def content_endpoint(
    request: Request,
    response: Response,
    accepts: AcceptsInfo = AcceptsDepend()
):
    # Access parsed accepts information
    accepted_types = accepts.get_accepted_types()
    accepted_languages = accepts.get_accepted_languages()

    return {
        "accepted_types": accepted_types,
        "accepted_languages": accepted_languages
    }
```

## API Reference

### AcceptsInfo Class

The `AcceptsInfo` class provides access to parsed accepts information:

```python
class AcceptsInfo:
    def __init__(self, request: Request)

    @property
    def accept(self) -> List[AcceptItem]
    @property
    def accept_language(self) -> List[AcceptItem]
    @property
    def accept_charset(self) -> List[AcceptItem]
    @property
    def accept_encoding(self) -> List[AcceptItem]

    def get_accepted_types(self) -> List[str]
    def get_accepted_languages(self) -> List[str]
    def get_accepted_charsets(self) -> List[str]
    def get_accepted_encodings(self) -> List[str]
```

### Dependency Injection Function

```python
def AcceptsDepend(attribute_name: str = "accepts") -> Any
```

Parameters:
- `attribute_name`: The attribute name where accepts info is stored in the request object (default: "accepts")

### Helper Functions

```python
# Get accepted content types
get_accepted_content_types(request: Request) -> List[str]

# Get accepted languages
get_accepted_languages(request: Request) -> List[str]

# Get accepted charsets
get_accepted_charsets(request: Request) -> List[str]

# Get accepted encodings
get_accepted_encodings(request: Request) -> List[str]

# Get best matching content type
get_best_accepted_content_type(request: Request, available_types: List[str]) -> Optional[str]

# Get best matching language
get_best_accepted_language(request: Request, available_languages: List[str]) -> Optional[str]
```

## Examples

### Content Negotiation

```python
@app.get("/api/users")
async def get_users(
    request: Request,
    response: Response,
    accepts: AcceptsInfo = AcceptsDepend()
):
    available_formats = ["application/json", "text/html", "application/xml"]
    best_format = accepts.get_accepted_types()[0] if accepts.get_accepted_types() else "application/json"

    response.set_header("Content-Type", best_format)

    if best_format == "application/json":
        return {"users": users_data}
    elif best_format == "text/html":
        return render_html_template(users_data)
    else:
        return serialize_to_xml(users_data)
```

### Language Negotiation

```python
@app.get("/api/messages")
async def get_messages(
    request: Request,
    response: Response,
    accepts: AcceptsInfo = AcceptsDepend()
):
    available_languages = ["en", "es", "fr", "de"]
    best_language = accepts.get_accepted_languages()[0] if accepts.get_accepted_languages() else "en"

    response.set_header("Content-Language", best_language)

    messages = get_messages_for_language(best_language)
    return {"messages": messages, "language": best_language}
```

### Direct Access to Parsed Information

```python
@app.get("/api/debug")
async def debug_accepts(request: Request, response: Response):
    # Access parsed information directly from request state
    accepts_parsed = getattr(request.state, 'accepts_parsed', {})

    return {
        "parsed_accept": [item.value for item in accepts_parsed.get('accept', [])],
        "parsed_accept_language": [item.value for item in accepts_parsed.get('accept_language', [])],
        "parsed_accept_charset": [item.value for item in accepts_parsed.get('accept_charset', [])],
        "parsed_accept_encoding": [item.value for item in accepts_parsed.get('accept_encoding', [])],
    }
```

## Testing with curl

You can test the middleware with different Accept headers:

```bash
# Test content negotiation
curl -H "Accept: application/xml" http://localhost:8000/api/content

# Test language negotiation
curl -H "Accept-Language: es" http://localhost:8000/api/languages

# Test encoding negotiation
curl -H "Accept-Encoding: gzip, deflate" http://localhost:8000/api/encoding

# Test charset negotiation
curl -H "Accept-Charset: iso-8859-1" http://localhost:8000/api/charset
```

## Implementation Details

The middleware stores parsed accepts information in the request state:

1. **request.state.accepts**: The full parsed information dictionary (for backward compatibility)
2. **request.state.accepts_parsed**: Individual parsed components for easier access

The dependency injection system creates an `AcceptsInfo` object that provides lazy-loaded access to the parsed information, following the same pattern as the request_id middleware.

## Migration from Previous Version

If you're upgrading from a previous version:

1. The existing `request.state.accepts` attribute is available (moved from `request.accepts`)
2. The new `request.state.accepts_parsed` attribute provides easier access to individual components
3. The new `AcceptsDepend()` function provides dependency injection capabilities
4. All existing functionality remains unchanged

## Error Handling

The middleware gracefully handles malformed Accept headers and missing headers. If an Accept header cannot be parsed, it will be treated as if no specific types/languages are requested, and default values will be used.
