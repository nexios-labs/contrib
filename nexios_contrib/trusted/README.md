<p align="center">
  <a href="https://github.com/nexios-labs">
    <img alt="Nexios Logo" height="220" src="https://nexios-docs.netlify.app/logo.png">
  </a>
</p>

<h1 align="center">Trusted Host Middleware for Nexios</h1>

A lightweight, production‑ready trusted host middleware for the Nexios ASGI framework.

It automatically validates the `Host` header of incoming requests against a configurable list of allowed hosts to prevent Host header attacks and ensure requests only come from trusted domains.

---

## Installation

```bash
pip install nexios_contrib
```

Or add it to your project’s `pyproject.toml` dependencies as `nexios_contrib`.

---

## Quickstart

```python
from nexios import NexiosApp
import nexios_contrib.trusted as trusted

app = NexiosApp()

# Add the Trusted Host middleware
app.add_middleware(
    trusted.TrustedHost(
        allowed_hosts=[
            "example.com",
            "api.example.com",
            "*.example.com",  # Wildcard support
            "127.0.0.1",
            "localhost"
        ],
        allowed_ports=[80, 443, 8000],  # Optional: restrict ports
        www_redirect=True               # Redirect www.example.com to example.com
    )
)

@app.get("/")
async def home(request, response):
    return {"message": "Hello from trusted host!"}
```

---

## Configuration

### Required Parameters

- `allowed_hosts: List[str]`
  - List of allowed hostnames, IP addresses, or patterns. Supports wildcards (e.g., `"*.example.com"`)

### Optional Parameters

- `allowed_ports: Optional[List[int]] = None`
  - List of allowed ports. If specified, only requests to these ports will be allowed. If `None`, all ports are allowed.

- `www_redirect: bool = True`
  - If `True`, automatically allows requests from `www.domain.com` if `domain.com` is in the allowed hosts list.

---

## Host Patterns

The middleware supports several types of host patterns:

### Exact Hosts
```python
allowed_hosts = ["example.com", "api.example.com"]
```

### IP Addresses
```python
allowed_hosts = ["127.0.0.1", "192.168.1.100"]
```

### Wildcard Patterns
```python
allowed_hosts = ["*.example.com", "*.api.example.com"]
```

### Port Restrictions
```python
allowed_hosts = ["example.com"]
allowed_ports = [80, 443]  # Only HTTP and HTTPS
```

---

## How it works

1. **Host Extraction**: Extracts the host from request headers with proper precedence:
   - `X-Forwarded-Host` (for proxies/load balancers)
   - `X-Host` (some proxies)
   - `Host` header (standard)

2. **Validation**: Checks the extracted host against the allowed patterns:
   - Normalizes hosts to lowercase
   - Validates against exact matches and wildcard patterns
   - Checks port restrictions if specified

3. **Security**: Rejects requests with untrusted hosts using `400 Bad Request`

4. **WWW Handling**: Optionally allows `www.domain.com` if `domain.com` is trusted

---

## Security Features

- **Host Header Attack Prevention**: Blocks requests with malicious Host headers
- **Proxy Support**: Properly handles forwarded headers from reverse proxies
- **Port Security**: Optional port restrictions for additional security
- **Case Insensitive**: All host validation is case insensitive
- **Wildcard Support**: Flexible pattern matching for subdomains

---

## Examples

### Basic Setup
```python
trusted.TrustedHost(allowed_hosts=["example.com", "api.example.com"])
```

### Development Environment
```python
trusted.TrustedHost(
    allowed_hosts=["localhost", "127.0.0.1", "*.local"],
    allowed_ports=[3000, 8000, 8080]
)
```

### Production with CDN
```python
trusted.TrustedHost(
    allowed_hosts=[
        "example.com",
        "www.example.com",
        "*.example.com",
        "cdn.example.com"
    ],
    allowed_ports=[80, 443]
)
```

### Multiple Domains
```python
trusted.TrustedHost(
    allowed_hosts=[
        "example.com",
        "myapp.com",
        "staging.example.com",
        "api.myapp.com"
    ]
)
```

---

## Error Handling

When a request comes from an untrusted host, the middleware raises:
- `BadRequest` exception with a descriptive message
- HTTP 400 status code is returned to the client

---

## Notes & Best Practices

- **Always specify allowed_hosts**: Never leave this empty or use wildcards like `["*"]` in production
- **Use HTTPS ports**: In production, typically restrict to ports 80 and 443
- **Consider your deployment**: Behind load balancers? Use `X-Forwarded-Host` support
- **Environment specific**: Use different configurations for development vs production
- **Subdomain handling**: Use wildcards for flexible subdomain support
- **IP restrictions**: Include your server's IP addresses in allowed hosts for health checks

---

Built with ❤️ by the [@nexios-labs](https://github.com/nexios-labs) community.
