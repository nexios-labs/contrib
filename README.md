<p align="center">
  <a href="https://github.com/nexios-labs">
    <img alt="Nexios Logo" height="350" src="https://nexios-docs.netlify.app/logo.png"> 
  </a>
</p>

<h1 align="center">Nexios Contrib</h1>

Community-driven extensions and add‑ons for the **[Nexios](https://nexios-docs.netlify.app/)** ASGI framework. This repository hosts independently versioned packages that you can install a‑la‑carte or together via the meta package.

---

## Packages

- **URL Normalization Middleware**: `nexios_contrib.slashes`
  - README: [nexios_contrib/slashes/README.md](./nexios_contrib/slashes/README.md)
  - Handles trailing slashes, double slashes, and URL normalization for consistent, clean URLs.

- **Trusted Host Middleware**: `nexios_contrib.trusted`
  - README: [nexios_contrib/trusted/README.md](./nexios_contrib/trusted/README.md)
  - Validates the `Host` header against allowed hosts to prevent Host header attacks and ensure requests come from trusted domains.

- **ETag Middleware**: `nexios_contrib.etag`
  - README: [nexios_contrib/etag/README.md](./nexios_contrib/etag/README.md)
  - Provides automatic `ETag` generation and conditional request handling (`If-None-Match` → `304`).

- **JSON-RPC**: `nexios_contrib.jrpc`
  - README: [nexios_contrib/jrpc/README.md](./nexios_contrib/jrpc/README.md)
  - JSON-RPC 2.0 server and client implementation for building RPC APIs.

More contribs will be added over time. Contributions welcome!

---

## Installation

Install the meta package (brings in all contribs):

```bash
pip install nexios_contrib
```

Or install directly from a specific package as they become available on PyPI.

---

## Quick Example (ETag)

```python
from nexios import NexiosApp
import nexios_contrib.etag as etag

app = NexiosApp()
app.add_middleware(etag.ETag())

@app.get("/")
async def home(request, response):
    return {"message": "Hello with ETag!"}
```

See the full guide in the [ETag README](./nexios_contrib/etag/README.md).

---

## Development

This repo uses **[uv](https://github.com/astral-sh/uv)** workspaces and **hatchling** for builds.

Common tasks:

```bash
# Sync workspace deps
uv sync

# Run tests
pytest -q

# Build wheel/sdist
python -m build
```

---

## Project Structure

```
./
├── nexios_contrib/
│   └── etag/                 # ETag middleware package
├── tests/
├── docs/
├── pyproject.toml
└── README.md
```

Each contrib package is versioned and released independently.

---

## Releasing

1. Update the package’s version in its `pyproject.toml` (SemVer).
2. Commit and push to `main`.
3. Create a release/tag.
4. Publish to PyPI.

---

Built with ❤️ by [@nexios-labs](https://github.com/nexios-labs)
