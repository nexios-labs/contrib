from typing import Callable, Dict, Optional

from .exceptions import JsonRpcMethodNotFound


class JsonRpcRegistry:
    """Registry for JSON-RPC methods."""

    # Class variable to store the singleton instance
    _instance = None

    def __new__(cls):
        """Implement singleton pattern using __new__"""
        if cls._instance is None:
            cls._instance = super(JsonRpcRegistry, cls).__new__(cls)
            # Initialize the instance attributes
            cls._instance.methods = {}
        return cls._instance

    def register(self, name: Optional[str] = None) -> Callable:
        """Decorator to register a function as a JSON-RPC method."""

        def decorator(func: Callable) -> Callable:
            method_name = name if name else func.__name__
            self.methods[method_name] = func
            return func

        return decorator

    def get_method(self, name: str) -> Callable:
        """Get a registered method by name."""
        if name not in self.methods:
            raise JsonRpcMethodNotFound(name)
        return self.methods[name]


# Function to get the singleton registry instance
def get_registry() -> JsonRpcRegistry:
    """
    Get the singleton JsonRpcRegistry instance.
    This ensures only one registry exists throughout the application.

    Returns:
        JsonRpcRegistry: The singleton registry instance
    """
    return JsonRpcRegistry()