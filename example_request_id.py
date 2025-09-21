"""
Example demonstrating the request_id contrib module usage.
"""
from nexios import NexiosApp
from nexios.http import Request, Response
from nexios_contrib.request_id import RequestId, generate_request_id, get_request_id_from_request

# Create Nexios app
app = NexiosApp()

# Add Request ID middleware
app.add_middleware(RequestId())

@app.get("/")
async def home(request: Request, response: Response):
    """Home endpoint that shows request ID usage."""
    request_id = getattr(request, 'request_id', 'No request ID')

    return {
        "message": "Hello from Nexios with Request ID!",
        "request_id": request_id,
        "generated_id": generate_request_id()  # Example of generating a new ID
    }

@app.get("/api/users")
async def get_users(request: Request, response: Response):
    """API endpoint demonstrating request ID access."""
    # Multiple ways to access request ID
    req_id_1 = getattr(request, 'request_id', None)
    req_id_2 = get_request_id_from_request(request)

    return {
        "users": [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"}
        ],
        "request_id_method1": req_id_1,
        "request_id_method2": req_id_2,
        "header_request_id": request.headers.get("X-Request-ID")
    }

@app.get("/custom-header")
async def custom_header(request: Request, response: Response):
    """Endpoint showing custom header name usage."""
    return {
        "message": "This uses X-Correlation-ID header",
        "correlation_id": request.headers.get("X-Correlation-ID")
    }

if __name__ == "__main__":
    print("Starting Nexios app with Request ID middleware...")
    print("Visit: http://localhost:8000/")
    print("Try these endpoints:")
    print("- GET / (shows basic request ID usage)")
    print("- GET /api/users (shows multiple ways to access request ID)")
    print("- GET /custom-header (shows X-Correlation-ID header)")

    app.run(host="localhost", port=8000)
