<p align="center">
  <a href="https://github.com/nexios-labs">
    <img alt="Nexios Logo" height="220" src="https://nexios-labs.github.io/nexios/logo.png">
  </a>
</p>

<h1 align="center">URL Normalization Middleware for Nexios</h1>

A lightweight, production‑ready URL normalization middleware for the Nexios ASGI framework.

It automatically handles trailing slashes, double slashes, and other common URL normalization issues to ensure consistent and clean URLs across your application.

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
import nexios_contrib.slashes as slashes

app = NexiosApp()

# Add URL normalization middleware
app.add_middleware(slashes.Slashes(
    slash_action=slashes.SlashAction.REDIRECT_REMOVE,  # Redirect to remove trailing slashes
    auto_remove_double_slashes=True,                   # Clean up double slashes
    redirect_status_code=301                           # Use permanent redirects
))

@app.get("/users")
async def users(request, response):
    return {"users": ["alice", "bob", "charlie"]}

@app.get("/posts")
async def posts(request, response):
    return {"posts": ["post1", "post2", "post3"]}
```

Requests to `/users/` will redirect to `/users`, and URLs with double slashes like `/users//123` will be cleaned to `/users/123`.

---

## Configuration

### Slash Action Options

The middleware supports several modes for handling trailing slashes:

- `SlashAction.REDIRECT_REMOVE` (default): Redirect to remove trailing slashes
- `SlashAction.REDIRECT_ADD`: Redirect to add trailing slashes
- `SlashAction.REMOVE`: Remove trailing slashes without redirect
- `SlashAction.ADD`: Add trailing slashes without redirect
- `SlashAction.IGNORE`: Leave trailing slashes as-is (only clean double slashes)

### Parameters

- `slash_action: SlashAction` - How to handle trailing slashes (default: REDIRECT_REMOVE)
- `auto_remove_double_slashes: bool` - Remove double slashes automatically (default: True)
- `redirect_status_code: int` - HTTP status code for redirects (default: 301)

---

## Examples

### SEO-Friendly Setup (Remove Trailing Slashes)

```python
app.add_middleware(slashes.Slashes(
    slash_action=slashes.SlashAction.REDIRECT_REMOVE,
    redirect_status_code=301  # SEO-friendly permanent redirect
))
```

### Directory-Style URLs (Add Trailing Slashes)

```python
app.add_middleware(slashes.Slashes(
    slash_action=slashes.SlashAction.REDIRECT_ADD,
    redirect_status_code=301
))
```

### Silent Normalization (No Redirects)

```python
app.add_middleware(slashes.Slashes(
    slash_action=slashes.SlashAction.REMOVE,  # Just remove, no redirect
    auto_remove_double_slashes=True
))
```

### Minimal Processing

```python
app.add_middleware(slashes.Slashes(
    slash_action=slashes.SlashAction.IGNORE,  # Don't touch slashes
    auto_remove_double_slashes=True           # Only clean double slashes
))
```

---

## How it works

1. **Path Analysis**: Examines the request path for normalization issues
2. **Skip Logic**: Intelligently skips processing for files, API paths, and query parameters
3. **Double Slash Removal**: Cleans up double slashes (// becomes /)
4. **Trailing Slash Handling**: Applies the configured slash action
5. **Redirect or Modify**: Either redirects the client or modifies the request path

---

## Skip Patterns

The middleware automatically skips processing for paths containing:
- File extensions (e.g., `.css`, `.js`, `.jpg`)
- Query parameters (e.g., `?param=value`)
- URL fragments (e.g., `#section`)

This ensures that:
- Static files are served correctly
- API endpoints with parameters work properly
- Client-side routing isn't interfered with

---

## URL Normalization Features

- **Double Slash Removal**: `//api/users` → `/api/users`
- **Trailing Slash Handling**: Configurable add/remove/redirect behavior
- **Smart Skipping**: Preserves file extensions and query parameters
- **SEO Optimization**: Uses 301 redirects for permanent URL changes
- **Proxy Compatible**: Works correctly behind reverse proxies
- **Standards Compliant**: Follows web standards for URL normalization

---

## Use Cases

### SEO & Consistency
```python
# Ensure all URLs have consistent trailing slash behavior
slashes.Slashes(slash_action=slashes.SlashAction.REDIRECT_REMOVE)
```

### Clean URLs
```python
# Remove double slashes and normalize paths
slashes.Slashes(auto_remove_double_slashes=True)
```

### API Design
```python
# API routes without trailing slashes
slashes.Slashes(
    slash_action=slashes.SlashAction.REMOVE,
    auto_remove_double_slashes=True
)
```

### Legacy URL Support
```python
# Redirect old URLs to new format
slashes.Slashes(
    slash_action=slashes.SlashAction.REDIRECT_REMOVE,
    redirect_status_code=301
)
```

---

## Advanced Usage

### Custom Skip Logic

```python
import nexios_contrib.slashes as slashes

class CustomSlashesMiddleware(slashes.SlashesMiddleware):
    def _should_skip_processing(self, path: str) -> bool:
        # Custom logic for skipping paths
        if super()._should_skip_processing(path):
            return True

        # Skip specific paths
        if path.startswith("/api/v2/"):
            return True

        return False
```

### Programmatic URL Normalization

```python
from nexios_contrib.slashes.helpers import normalize_path, clean_url_path

# Normalize a path
clean_path = normalize_path("/api//users//123")  # "/api/users/123"

# Clean a full URL
clean_url = clean_url_path("https://example.com/api//users")  # "https://example.com/api/users"
```

---

## Notes & Best Practices

- **Choose one slash behavior**: Be consistent across your application
- **Use 301 for permanent changes**: Better for SEO than 302
- **Test with your routing**: Ensure compatibility with your route definitions
- **Consider API endpoints**: May need different behavior for API vs pages
- **Monitor redirects**: Use appropriate redirect status codes
- **File serving**: Static files are automatically skipped from processing

---

## Migration Guide

If you're migrating from inconsistent URLs:

1. **Audit your URLs**: Check current URL patterns
2. **Choose a strategy**: Decide on trailing slash behavior
3. **Implement gradually**: Add middleware and monitor
4. **Update internal links**: Ensure all internal links follow the new pattern
5. **Update documentation**: Document the new URL conventions

---

Built with ❤️ by the [@nexios-labs](https://github.com/nexios-labs) community.
