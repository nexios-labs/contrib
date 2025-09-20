"""
Nexios JSON-RPC contrib package.
"""

from .client import JsonRpcClient
from .server import JsonRpcPlugin
from .registry import JsonRpcRegistry, get_registry
from .exceptions import JsonRpcError, JsonRpcMethodNotFound, JsonRpcInvalidParams, JsonRpcInvalidRequest, JsonRpcClientError

__all__ = [
    "JsonRpcClient",
    "JsonRpcPlugin",
    "JsonRpcRegistry",
    "get_registry",
    "JsonRpcError",
    "JsonRpcMethodNotFound",
    "JsonRpcInvalidParams",
    "JsonRpcInvalidRequest",
    "JsonRpcClientError",
]
