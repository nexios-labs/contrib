<p align="center">
  <a href="https://github.com/nexios-labs">
    <img alt="Nexios Logo" height="220" src="https://nexios-labs.github.io/nexios/logo.png">
  </a>
</p>

<h1 align="center">ETag Middleware for Nexios</h1>

A lightweight, production‑ready ETag middleware for the Nexios ASGI framework.

It automatically:

- Computes and sets an `ETag` header for responses that don’t already have one.
- Handles conditional `GET`/`HEAD` requests via `If-None-Match` and returns `304 Not Modified` when appropriate.

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
import nexios_contrib.etag as etag

app = NexiosApp()

# Add the ETag middleware (defaults shown)
app.add_middleware(
    etag.ETag(
        weak=True,                 # Generate weak validators (W/ prefixes)
        methods=("GET", "HEAD"),  # Methods to apply to
        override=False             # Don’t overwrite an existing ETag by default
    )
)

@app.get("/")
async def home(request, response):
    return {"message": "Hello with ETag!"}
```

That’s it. Responses to `GET`/`HEAD` will carry an `ETag` header. Clients sending `If-None-Match` will receive `304` when the ETag matches.

---

## Configuration

- `weak: bool = True`
  - Use weak validators (e.g. `W/"abc"`). Set `False` for strong validators when you know the body bytes are stable across platforms and encodings.

- `methods: Iterable[str] = ("GET", "HEAD")`
  - Limit conditional handling to idempotent methods. You can add others, but it’s not typical.

- `override: bool = False`
  - If `True`, overwrites an `ETag` already set by your handler.

---

## How it works

- If the handler doesn’t set an `ETag`, the middleware computes one from the response body and sets it.
- If the request includes `If-None-Match` and it matches the response’s `ETag` (weak compare by default), the middleware converts the response into `304 Not Modified` and removes the body, per RFC 9110.

---

## Notes & Best Practices

- Applies by default to `GET` and `HEAD`. Avoid applying to mutating methods like `POST`/`PUT` unless you know what you’re doing.
- Streaming or extremely large bodies may benefit from precomputed/strong ETags at your handler or via a hash of a stable resource version.
- When returning `304`, the middleware ensures the body is empty and relies on the underlying response type to handle headers correctly.

---



Built with ❤️ by the [@nexios-labs](https://github.com/nexios-labs) community.
