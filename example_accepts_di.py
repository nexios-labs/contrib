"""
Example demonstrating the accepts contrib module usage with dependency injection.

This example shows how to use the new AcceptsDepend() function to inject
parsed accepts information into route handlers.
"""
from nexios import NexiosApp
from nexios.http import Request, Response
from nexios_contrib.accepts import Accepts, AcceptsDepend, AcceptsInfo

# Create Nexios app
app = NexiosApp()

# Add Accepts middleware
app.add_middleware(Accepts())

@app.get("/")
async def home(request: Request, response: Response):
    """Home endpoint that shows basic accepts information."""
    return {
        "message": "Hello from Nexios with Accepts middleware!",
        "accept_header": request.headers.get("Accept", "Not specified"),
        "accept_language": request.headers.get("Accept-Language", "Not specified"),
        "user_agent": request.headers.get("User-Agent", "Not specified"),
    }

@app.get("/api/content")
async def content_types(
    request: Request,
    response: Response,
    accepts: AcceptsInfo = AcceptsDepend()
):
    """API endpoint demonstrating accepts dependency injection."""
    # Using the injected AcceptsInfo object
    accepted_types = accepts.get_accepted_types()
    accepted_languages = accepts.get_accepted_languages()

    return {
        "message": "Content negotiation example",
        "accepted_content_types": accepted_types,
        "accepted_languages": accepted_languages,
        "available_formats": ["application/json", "text/html", "application/xml"],
        "recommended_format": accepts.get_accepted_types()[0] if accepts.get_accepted_types() else "application/json"
    }

@app.get("/api/languages")
async def languages(
    request: Request,
    response: Response,
    accepts: AcceptsInfo = AcceptsDepend()
):
    """Endpoint showing language negotiation."""
    available_languages = ["en", "es", "fr", "de"]
    best_language = accepts.get_accepted_languages()[0] if accepts.get_accepted_languages() else "en"

    return {
        "message": "Language negotiation example",
        "accepted_languages": accepts.get_accepted_languages(),
        "available_languages": available_languages,
        "best_match": best_language,
        "content_language": best_language
    }

@app.get("/api/encoding")
async def encoding(
    request: Request,
    response: Response,
    accepts: AcceptsInfo = AcceptsDepend()
):
    """Endpoint showing encoding negotiation."""
    available_encodings = ["gzip", "deflate", "br", "compress", "identity"]
    accepted_encodings = accepts.get_accepted_encodings()

    return {
        "message": "Encoding negotiation example",
        "accepted_encodings": accepted_encodings,
        "available_encodings": available_encodings,
        "supports_compression": len(accepted_encodings) > 1 or (len(accepted_encodings) == 1 and accepted_encodings[0] != "identity")
    }

@app.get("/api/charset")
async def charset(
    request: Request,
    response: Response,
    accepts: AcceptsInfo = AcceptsDepend()
):
    """Endpoint showing charset negotiation."""
    available_charsets = ["utf-8", "iso-8859-1", "us-ascii"]
    accepted_charsets = accepts.get_accepted_charsets()

    return {
        "message": "Charset negotiation example",
        "accepted_charsets": accepted_charsets,
        "available_charsets": available_charsets,
        "recommended_charset": accepted_charsets[0] if accepted_charsets else "utf-8"
    }

@app.get("/api/parsed")
async def parsed_info(request: Request, response: Response):
    """Endpoint showing parsed accepts information stored in request state."""
    # Access parsed information directly from request state
    accepts_parsed = getattr(request.state, 'accepts_parsed', {})
    accepts_info = getattr(request.state, 'accepts', {})

    return {
        "message": "Parsed accepts information",
        "parsed_components": {
            "accept": [item.value for item in accepts_parsed.get('accept', [])],
            "accept_language": [item.value for item in accepts_parsed.get('accept_language', [])],
            "accept_charset": [item.value for item in accepts_parsed.get('accept_charset', [])],
            "accept_encoding": [item.value for item in accepts_parsed.get('accept_encoding', [])],
        },
        "raw_headers": {
            "accept": accepts_info.get('raw_accept', ''),
            "accept_language": accepts_info.get('raw_accept_language', ''),
            "accept_charset": accepts_info.get('raw_accept_charset', ''),
            "accept_encoding": accepts_info.get('raw_accept_encoding', ''),
        }
    }

@app.get("/api/negotiation")
async def negotiation(
    request: Request,
    response: Response,
    accepts: AcceptsInfo = AcceptsDepend()
):
    """Advanced content negotiation example."""
    # Simulate available content types and languages
    available_types = ["application/json", "text/html", "application/xml", "text/plain"]
    available_languages = ["en", "es", "fr", "de", "it"]

    # Get best matches
    best_content_type = accepts.get_accepted_types()[0] if accepts.get_accepted_types() else "application/json"
    best_language = accepts.get_accepted_languages()[0] if accepts.get_accepted_languages() else "en"

    # Set response headers based on negotiation
    response.set_header("Content-Type", best_content_type)
    response.set_header("Content-Language", best_language)

    return {
        "message": "Advanced content negotiation",
        "negotiated_content_type": best_content_type,
        "negotiated_language": best_language,
        "available_content_types": available_types,
        "available_languages": available_languages,
        "client_accepted_types": accepts.get_accepted_types(),
        "client_accepted_languages": accepts.get_accepted_languages(),
    }

if __name__ == "__main__":
    print("Starting Nexios app with Accepts middleware and dependency injection...")
    print("Visit: http://localhost:8000/")
    print("\nAvailable endpoints:")
    print("- GET / (basic accepts information)")
    print("- GET /api/content (content type negotiation with DI)")
    print("- GET /api/languages (language negotiation with DI)")
    print("- GET /api/encoding (encoding negotiation with DI)")
    print("- GET /api/charset (charset negotiation with DI)")
    print("- GET /api/parsed (direct access to parsed information)")
    print("- GET /api/negotiation (advanced negotiation example)")
    print("\nTry these with different Accept headers:")
    print("- curl -H 'Accept: application/xml' http://localhost:8000/api/content")
    print("- curl -H 'Accept-Language: es' http://localhost:8000/api/languages")
    print("- curl -H 'Accept-Encoding: gzip, deflate' http://localhost:8000/api/encoding")

    app.run(host="localhost", port=8000)
