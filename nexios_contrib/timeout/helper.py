"""
Timeout helper functions for Nexios.

This module provides utilities for timeout handling and request timing
for Nexios applications.
"""
from __future__ import annotations

import asyncio
import time
from typing import Any, Awaitable, Callable, Optional

from nexios.http import Request, Response


class TimeoutException(Exception):
    """
    Exception raised when a request times out.

    This exception is raised by the TimeoutMiddleware when a request
    exceeds the configured timeout duration.
    """

    def __init__(self, timeout: float, detail: Optional[str] = None) -> None:
        """
        Initialize a TimeoutException.

        Args:
            timeout: The timeout duration in seconds.
            detail: Optional detail message.
        """
        self.timeout = timeout
        self.detail = detail or f"Request timed out after {timeout} seconds"
        super().__init__(self.detail)


def timeout_after(
    timeout: float,
    exception: Optional[Exception] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator that adds timeout functionality to async functions.

    Args:
        timeout: Maximum time in seconds to wait for the function to complete.
        exception: Exception to raise on timeout. Defaults to TimeoutException.

    Returns:
        Decorated function that will timeout after the specified duration.

    Example:
        @timeout_after(30.0)
        async def slow_operation():
            await asyncio.sleep(60)  # This will timeout after 30 seconds
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if timeout <= 0:
                return await func(*args, **kwargs)

            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
            except asyncio.TimeoutError:
                if exception:
                    raise exception
                raise TimeoutException(timeout)
        return wrapper
    return decorator


async def timeout_with_fallback(
    coro: Awaitable[Any],
    timeout: float,
    fallback_value: Any = None,
    fallback_exception: Optional[Exception] = None,
) -> Any:
    """
    Execute a coroutine with a timeout and return a fallback value if it times out.

    Args:
        coro: The coroutine to execute.
        timeout: Maximum time in seconds to wait.
        fallback_value: Value to return if the coroutine times out.
        fallback_exception: Exception to raise instead of returning fallback_value.

    Returns:
        Result of the coroutine or fallback_value if timeout occurs.

    Example:
        result = await timeout_with_fallback(
            slow_operation(), 30.0, fallback_value="default"
        )
    """
    if timeout <= 0:
        return await coro

    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        if fallback_exception:
            raise fallback_exception
        return fallback_value


def get_request_duration(request: Request) -> float:
    """
    Get the duration of a request in seconds.

    Args:
        request: The HTTP request object.

    Returns:
        Duration of the request in seconds, or 0 if not available.
    """
    if hasattr(request, 'start_time'):
        return time.time() - request.start_time
    return 0.0


def set_request_start_time(request: Request) -> None:
    """
    Set the start time for a request.

    Args:
        request: The HTTP request object to set the start time for.
    """
    request.start_time = time.time()


def get_request_start_time(request: Request) -> Optional[float]:
    """
    Get the start time for a request (if set).

    Args:
        request: The HTTP request object.

    Returns:
        The start time as a UNIX timestamp, or None if not available.
    """
    return getattr(request, "start_time", None)


def get_timeout_from_request(
    request: Request,
    default_timeout: float = 30.0
) -> float:
    """
    Extract timeout value from request headers or query parameters.

    Checks for timeout in:
    - X-Request-Timeout header (seconds)
    - timeout query parameter (seconds)

    Args:
        request: The HTTP request object.
        default_timeout: Default timeout if none specified.

    Returns:
        Timeout duration in seconds.
    """
    # Check for timeout in headers
    timeout_header = request.headers.get('X-Request-Timeout')
    if timeout_header:
        try:
            return max(0.1, float(timeout_header))
        except (ValueError, TypeError):
            pass

    # Check for timeout in query parameters
    timeout_param = request.query_params.get('timeout')
    if timeout_param:
        try:
            return max(0.1, float(timeout_param))
        except (ValueError, TypeError):
            pass

    return default_timeout


def create_timeout_response(
    response: Response,
    timeout: float,
    detail: Any = None,
) -> Response:
    """
    Create a timeout error response.

    Args:
        response: The Nexios response manager to write into.
        timeout: The timeout duration that was exceeded.
        detail: Optional detail message.

    Returns:
        HTTP response indicating a timeout error.
    """
    response.set_header("X-Timeout", str(timeout))
    return response.json(
        {"error": "Request Timeout", "timeout": timeout, "detail": detail},
        status_code=408,
    )


def is_timeout_error(error: Exception) -> bool:
    """
    Check if an exception is a timeout-related error.

    Args:
        error: The exception to check.

    Returns:
        True if the error is timeout-related, False otherwise.
    """
    return isinstance(error, (asyncio.TimeoutError, TimeoutException))


def format_timeout_duration(seconds: float) -> str:
    """
    Format a timeout duration in a human-readable format.

    Args:
        seconds: Duration in seconds.

    Returns:
        Human-readable duration string.
    """
    if seconds < 1:
        return f"{seconds*1000}ms"
    elif seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds}s"
    else:
        hours = int(seconds // 3600)
        remaining_minutes = int((seconds % 3600) // 60)
        remaining_seconds = seconds % 60
        return f"{hours}h {remaining_minutes}m {remaining_seconds}s"
