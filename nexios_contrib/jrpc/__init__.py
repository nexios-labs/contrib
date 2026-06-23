"""
Nexios JSON-RPC contrib package.
"""

from .client import JsonRpcClient
from .exceptions import (
    JsonRpcClientError,
    JsonRpcError,
    JsonRpcInvalidParams,
    JsonRpcInvalidRequest,
    JsonRpcMethodNotFound,
)
from .registry import JsonRpcRegistry, get_registry
from .server import JsonRpcPlugin

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
