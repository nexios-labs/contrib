"""
Example demonstrating the accepts contrib module usage.
"""
from nexios import NexiosApp
from nexios.http import Request, Response
from nexios_contrib.accepts import (
    Accepts,
    ContentNegotiationMiddleware,
    StrictContentNegotiationMiddleware,
    negotiate_content_type,
    negotiate_language,
    get_best_match
)

# Create Nexios app
app = NexiosApp()

# Example 1: Basic accepts middleware
app.add_middleware(Accepts())

# Example 2: Content negotiation middleware
app.add_middleware(ContentNegotiationMiddleware())

# Example 3: Strict content negotiation (returns 406 if no match)
app.add_middleware(
    StrictContentNegotiationMiddleware(
        available_types=["application/json", "text/html"],
        available_languages=["en", "es", "fr"]
    )
)

@app.get("/")
async def home(request: Request, response: Response):
    """Home endpoint showing basic accepts functionality."""
    accepts_info = getattr(request, 'accepts', {})

    return {
        "message": "Hello with Content Negotiation!",
        "accept_header": accepts_info.get('raw_accept', ''),
        "accepted_types": [item.value for item in accepts_info.get('accept', [])],
        "accept_language": accepts_info.get('raw_accept_language', ''),
        "note": "Try sending different Accept headers to see negotiation in action"
    }

@app.get("/api/data")
async def get_data(request: Request, response: Response):
    """API endpoint with automatic content negotiation."""
    data = {
        "users": [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"}
        ],
        "total": 2
    }

    # The middleware will automatically set Content-Type based on Accept header
    # Send Accept: application/json → gets JSON response
    # Send Accept: text/html → gets HTML response (if configured)

    return data

@app.get("/api/content")
async def get_content(request: Request, response: Response):
    """API endpoint with manual content negotiation."""
    available_types = ["application/json", "application/xml", "text/html"]

    # Manual content negotiation
    best_type = get_best_match(
        request.headers.get('Accept', ''),
        available_types
    )

    response.headers['Content-Type'] = best_type

    if best_type == "application/json":
        return {"message": "JSON format", "format": "json"}
    elif best_type == "application/xml":
        return "<message>XML format</message>"
    elif best_type == "text/html":
        return "<h1>HTML format</h1><p>This is HTML content</p>"

    return {"message": "Default format", "format": "json"}

@app.get("/greetings")
async def get_greetings(request: Request, response: Response):
    """Internationalized greetings with language negotiation."""
    available_languages = ["en", "es", "fr", "de"]

    best_language = negotiate_language(
        request.headers.get('Accept-Language', ''),
        available_languages
    )

    greetings = {
        "en": {"greeting": "Hello", "farewell": "Goodbye"},
        "es": {"greeting": "Hola", "farewell": "Adiós"},
        "fr": {"greeting": "Bonjour", "farewell": "Au revoir"},
        "de": {"greeting": "Guten Tag", "farewell": "Auf Wiedersehen"}
    }

    greeting_data = greetings.get(best_language, greetings["en"])
    response.headers['Content-Language'] = best_language

    return {
        "greeting": greeting_data["greeting"],
        "farewell": greeting_data["farewell"],
        "language": best_language,
        "note": "Try Accept-Language: es, fr to see different languages"
    }

@app.get("/debug/accepts")
async def debug_accepts(request: Request, response: Response):
    """Debug endpoint showing all accepts information."""
    accepts_info = getattr(request, 'accepts', {})

    return {
        "client_accepts": {
            "accept": accepts_info.get('raw_accept', ''),
            "accept_language": accepts_info.get('raw_accept_language', ''),
            "accept_charset": accepts_info.get('raw_accept_charset', ''),
            "accept_encoding": accepts_info.get('raw_accept_encoding', ''),
        },
        "parsed": {
            "accepted_types": [item.value for item in accepts_info.get('accept', [])],
            "accepted_languages": [item.value for item in accepts_info.get('accept_language', [])],
            "accepted_charsets": [item.value for item in accepts_info.get('accept_charset', [])],
            "accepted_encodings": [item.value for item in accepts_info.get('accept_encoding', [])],
        },
        "negotiated": {
            "content_type": getattr(request, 'negotiated_content_type', 'Not set'),
            "language": getattr(request, 'negotiated_language', 'Not set'),
        },
        "response_headers": dict(response.headers)
    }

@app.get("/api/strict")
async def strict_api(request: Request, response: Response):
    """Strict API that only accepts specific content types."""
    # This endpoint uses StrictContentNegotiationMiddleware
    # Will return 406 Not Acceptable if client doesn't accept JSON

    negotiated_type = getattr(request, 'negotiated_content_type', 'application/json')

    return {
        "message": "Strict API response",
        "content_type": negotiated_type,
        "data": {"items": [1, 2, 3]},
        "note": "Only accepts application/json content type"
    }

# Custom middleware example
class CustomAcceptsMiddleware(ContentNegotiationMiddleware):
    """Custom middleware with API versioning support."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_versions = {
            "application/vnd.myapi.v1+json": "v1",
            "application/vnd.myapi.v2+json": "v2",
            "application/vnd.myapi.v3+json": "v3"
        }

    def negotiate_content_type(self, request, available_types, default_type=None):
        """Support API versioning through Accept header."""
        accept_header = request.headers.get('Accept', '')

        # Check for versioned API types
        for versioned_type, version in self.api_versions.items():
            if versioned_type in accept_header:
                # Check if the base type is available
                base_type = versioned_type.replace("vnd.myapi.", "").replace("vnd.myapi.", "")
                if base_type in available_types:
                    return base_type

        return super().negotiate_content_type(request, available_types, default_type)

# Example usage of custom middleware
# app.add_middleware(CustomAcceptsMiddleware())

if __name__ == "__main__":
    print("Starting Nexios app with Accepts middleware...")
    print("Visit: http://localhost:8000/")
    print("Endpoints:")
    print("- GET / (basic accepts info)")
    print("- GET /api/data (automatic content negotiation)")
    print("- GET /api/content (manual content negotiation)")
    print("- GET /greetings (language negotiation)")
    print("- GET /debug/accepts (detailed accepts information)")
    print("- GET /api/strict (strict content negotiation)")
    print()
    print("Test with different Accept headers:")
    print("curl -H 'Accept: application/json' http://localhost:8000/api/content")
    print("curl -H 'Accept: text/html' http://localhost:8000/api/content")
    print("curl -H 'Accept-Language: es' http://localhost:8000/greetings")

    app.run(host="localhost", port=8000)
