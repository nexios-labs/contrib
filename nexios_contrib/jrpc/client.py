import asyncio
import json
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Union

from .exceptions import JsonRpcClientError


class JsonRpcClient:
    """
    A client for the JSON-RPC server that doesn't require external packages.
    Uses only standard library modules.
    """

    def __init__(self, base_url: str):
        """
        Initialize the JSON-RPC client.

        Args:
            base_url: The base URL of the JSON-RPC server, including the path prefix
            (e.g., "http://localhost:8000/rpc")
        """
        self.base_url = base_url
        self.request_id = 0
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="jsonrpc-client")

    def _generate_request_id(self) -> int:
        """Generate a unique request ID."""
        self.request_id += 1
        return self.request_id

    def _make_request_sync(
        self, method: str, params: Union[Dict[str, Any], List[Any]]
    ) -> Dict[str, Any]:
        """
        Synchronous version of _make_request for use in thread executor.

        Args:
            method: The name of the JSON-RPC method to call
            params: The parameters to pass to the method (dict or list)

        Returns:
            The response from the server

        Raises:
            Exception: If there's an error in the response
        """
        # Create the request payload
        request_id = self._generate_request_id()
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": request_id,
        }

        # Convert the payload to JSON
        data = json.dumps(payload).encode("utf-8")

        # Create the request
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        req = urllib.request.Request(
            url=self.base_url, data=data, headers=headers, method="POST"
        )

        # Send the request and get the response
        try:
            with urllib.request.urlopen(req) as response:
                response_data = json.loads(response.read().decode("utf-8"))

                # Check if there's an error in the response
                if "error" in response_data:
                    error = response_data["error"]
                    raise JsonRpcClientError(
                        code=error.get("code", -32603),
                        message=error.get("message", "Unknown error"),
                        data=error.get("data"),
                    )

                # Return the result
                return response_data.get("result")
        except urllib.error.HTTPError as e:
            # Handle HTTP errors
            try:
                error_data = json.loads(e.read().decode("utf-8"))
                if "error" in error_data:
                    error = error_data["error"]
                    raise JsonRpcClientError(
                        code=error.get("code", -32603),
                        message=error.get("message", "Server error"),
                        data=error.get("data"),
                    )
            except json.JSONDecodeError:
                pass

            raise JsonRpcClientError(
                code=-32603, message=f"HTTP error: {e.code} {e.reason}", data=None
            )
        except Exception as e:
            raise JsonRpcClientError(
                code=-32603, message=f"Request error: {str(e)}", data=None
            )

    async def _make_request(
        self, method: str, params: Union[Dict[str, Any], List[Any]]
    ) -> Any:
        """
        Make a JSON-RPC request to the server asynchronously.

        Args:
            method: The name of the JSON-RPC method to call
            params: The parameters to pass to the method (dict or list)

        Returns:
            The response from the server

        Raises:
            Exception: If there's an error in the response
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor, self._make_request_sync, method, params
        )

    def __getattr__(self, method_name: str):
        """
        Enable calling JSON-RPC methods directly as attributes of the client.

        Example:
            client.add(a=1, b=2)
            client.get_user(user_id=1)
        """

        def method_caller(*args, **kwargs):
            # Determine whether to use positional or named parameters
            if args and kwargs:
                raise ValueError("Cannot mix positional and named parameters")

            params = kwargs if kwargs else list(args)
            return self._make_request_sync(method_name, params)

        return method_caller

    async def acall(self, method: str, params: Union[Dict[str, Any], List[Any]] = None) -> Any:
        """
        Call a JSON-RPC method asynchronously.

        Args:
            method: The name of the JSON-RPC method to call
            params: The parameters to pass to the method (default: None)

        Returns:
            The result of the JSON-RPC method call
        """
        if params is None:
            params = {}
        return await self._make_request(method, params)

    def call(self, method: str, params: Union[Dict[str, Any], List[Any]] = None) -> Any:
        """
        Call a JSON-RPC method synchronously (backward compatibility).

        Args:
            method: The name of the JSON-RPC method to call
            params: The parameters to pass to the method (default: None)

        Returns:
            The result of the JSON-RPC method call
        """
        if params is None:
            params = {}
        return self._make_request_sync(method, params)