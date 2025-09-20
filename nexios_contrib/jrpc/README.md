<p align="center">
  <a href="https://github.com/nexios-labs">
    <img alt="Nexios Logo" height="220" src="https://nexios-docs.netlify.app/logo.png">
  </a>
</p>

<h1 align="center">JSON-RPC Contrib for Nexios</h1>

Lightweight helpers for running JSON-RPC 2.0 over HTTP with Nexios.

This contrib provides:

- A JSON-RPC 2.0 server implementation
- A JSON-RPC client for making remote calls
- Method registration and error handling
- No external dependencies required

---

## Installation

Install the JSON-RPC contrib with Nexios:

```bash
pip install nexios_contrib
```

This contrib uses only standard library modules for maximum compatibility.

---

## Quickstart (Server)

```python
# server.py
from nexios import NexiosApp
from nexios_contrib.jrpc.server import JsonRpcPlugin
from nexios_contrib.jrpc.registry import get_registry

def main():
    # Create Nexios app
    app = NexiosApp()

    # Get the global registry and register methods
    registry = get_registry()

    @registry.register("add")
    def add(a: int, b: int) -> int:
        """Add two numbers together."""
        return a + b

    @registry.register("echo")
    async def echo(msg: str) -> str:
        """Echo back the input message."""
        return f"Server says: {msg}"

    # Mount the JSON-RPC plugin
    JsonRpcPlugin(app, {"path_prefix": "/rpc"})

    print("🚀 JSON-RPC Server starting on port 3020...")
    print("📋 Available JSON-RPC methods:")
    print("   - add(a, b) -> int")
    print("   - echo(msg) -> str")
    print("\n🔗 JSON-RPC endpoint: http://localhost:3020/rpc")

    # Start the server
    app.run(host="0.0.0.0", port=3020)

if __name__ == "__main__":
    main()
```

---

## Quickstart (Client)

```python
# client.py
import asyncio
from nexios_contrib.jrpc.client import JsonRpcClient

async def main() -> None:
    async with JsonRpcClient("http://localhost:3020/rpc") as client:
        result = await client.call("add", a=2, b=3)
        print(result)  # Output: 5

        result = await client.call("echo", msg="Hello, server!")
        print(result)  # Output: Server says: Hello, server!

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Using with Nexios

Run your Nexios app and your JSON-RPC server side‑by‑side. For local dev you might start them in separate processes. In production you can deploy them separately or run the JSON-RPC server in its own service.

Example: simple Nexios app with JSON-RPC running in another process:

```python
from nexios import NexiosApp

app = NexiosApp()

@app.get("/")
async def index(request, response):
    return {"status": "ok", "jsonrpc": "available on :3020/rpc"}
```

---

## API Reference

- `JsonRpcPlugin(app, options) -> None`
- `JsonRpcClient(url, *, options=None) -> JsonRpcClient`
- `get_registry() -> Registry`

---

## License

BSD-3-Clause. See the repository `LICENSE` file.

---

Built with ❤️ by the [@nexios-labs](https://github.com/nexios-labs) community.
