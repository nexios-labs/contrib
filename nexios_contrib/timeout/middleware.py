"""
Timeout middleware for Nexios.

This middleware provides request timeout handling and automatic timeout
responses for Nexios applications.
"""
from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, Optional, Union

from nexios.http import Request, Response
from nexios.middleware.base import BaseMiddleware
from nexios.exceptions import HTTPException

from .helper import (
    TimeoutException,
    create_timeout_response,
    get_request_duration,
    get_timeout_from_request,
    is_timeout_error,
    set_request_start_time,
    timeout_after,
)


class TimeoutMiddleware(BaseMiddleware):
    """
    Middleware for handling request timeouts in Nexios applications.

    This middleware can:
    - Set a global timeout for all requests
    - Extract timeout from request headers/query parameters
    - Provide timeout error responses
    - Track request durations
    - Apply timeouts to individual requests

    Options:
    - default_timeout (float): Default timeout in seconds for all requests
    - max_timeout (float): Maximum allowed timeout from request headers
    - min_timeout (float): Minimum allowed timeout (default: 0.1)
    - timeout_header (str): Header name to check for timeout values
    - timeout_param (str): Query parameter name to check for timeout values
    - track_duration (bool): Track request duration in response headers
    - timeout_response_enabled (bool): Return custom timeout responses
    - exception_on_timeout (bool): Raise exception instead of returning timeout response
    """

    def __init__(
        self,
        *,
        default_timeout: float = 30.0,
        max_timeout: Optional[float] = None,
        min_timeout: float = 0.1,
        timeout_header: str = "X-Request-Timeout",
        timeout_param: str = "timeout",
        track_duration: bool = True,
        timeout_response_enabled: bool = True,
        exception_on_timeout: bool = False,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the TimeoutMiddleware.

        Args:
            default_timeout: Default timeout in seconds for all requests.
            max_timeout: Maximum allowed timeout from request headers.
            min_timeout: Minimum allowed timeout (default: 0.1).
            timeout_header: Header name to check for timeout values.
            timeout_param: Query parameter name to check for timeout values.
            track_duration: Track request duration in response headers.
            timeout_response_enabled: Return custom timeout responses.
            exception_on_timeout: Raise exception instead of returning timeout response.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(**kwargs)
        self.default_timeout = default_timeout
        self.max_timeout = max_timeout
        self.min_timeout = min_timeout
        self.timeout_header = timeout_header
        self.timeout_param = timeout_param
        self.track_duration = track_duration
        self.timeout_response_enabled = timeout_response_enabled
        self.exception_on_timeout = exception_on_timeout

    async def process_request(
        self,
        request: Request,
        response: Response,
        call_next: Callable[..., Any],
    ) -> Any:
        """
        Process incoming request with timeout handling.

        Args:
            request: The HTTP request object.
            response: The HTTP response object.
            call_next: The next middleware or handler to call.

        Returns:
            Any: The result from the next middleware or handler.
        """
        # Set request start time for duration tracking
        set_request_start_time(request)

        # Get timeout for this request
        timeout = self._get_request_timeout(request)

        # Store timeout information in request for later use
        request.timeout = timeout
        request.timeout_config = {
            'default_timeout': self.default_timeout,
            'max_timeout': self.max_timeout,
            'min_timeout': self.min_timeout,
            'timeout_header': self.timeout_header,
            'timeout_param': self.timeout_param,
        }

        try:
            # Apply timeout to the next handler
            if timeout > 0:
                async def timeout_wrapper() -> Any:
                    try:
                        return await asyncio.wait_for(call_next(), timeout=timeout)
                    except asyncio.TimeoutError:
                        raise TimeoutException(timeout)

                result = await timeout_wrapper()
            else:
                result = await call_next()

            return result

        except TimeoutException as e:
            if self.exception_on_timeout:
                raise e
            elif self.timeout_response_enabled:
                return self._create_timeout_response(request, e)
            else:
                # Return a basic timeout response
                return Response(
                    status_code=408,
                    content="Request Timeout"
                )
        except Exception as e:
            # Handle other exceptions
            if is_timeout_error(e):
                if self.exception_on_timeout:
                    raise e
                elif self.timeout_response_enabled:
                    return self._create_timeout_response(request, e)
            raise

    async def process_response(
        self,
        request: Request,
        response: Response,
    ) -> Response:
        """
        Process outgoing response to add timing information.

        Args:
            request: The original HTTP request object.
            response: The HTTP response object to modify.

        Returns:
            Response: The modified HTTP response object.
        """
        # Add request duration to response headers if tracking is enabled
        if self.track_duration and hasattr(request, 'start_time'):
            duration = get_request_duration(request)
            response.headers['X-Request-Duration'] = str(duration)

            # Add timeout information if available
            if hasattr(request, 'timeout'):
                response.headers['X-Request-Timeout'] = str(request.timeout)

        return response

    def _get_request_timeout(self, request: Request) -> float:
        """
        Get the timeout value for this request.

        Args:
            request: The HTTP request object.

        Returns:
            float: Timeout duration in seconds.
        """
        # Check for timeout in headers
        timeout_header = request.headers.get(self.timeout_header)
        if timeout_header:
            try:
                timeout = float(timeout_header)
                return self._validate_timeout(timeout)
            except (ValueError, TypeError):
                pass

        # Check for timeout in query parameters
        timeout_param = request.query_params.get(self.timeout_param)
        if timeout_param:
            try:
                timeout = float(timeout_param)
                return self._validate_timeout(timeout)
            except (ValueError, TypeError):
                pass

        return self.default_timeout

    def _validate_timeout(self, timeout: float) -> float:
        """
        Validate and normalize a timeout value.

        Args:
            timeout: The timeout value to validate.

        Returns:
            float: Validated timeout value.
        """
        # Ensure timeout is not negative
        timeout = max(0, timeout)

        # Apply minimum timeout constraint
        timeout = max(self.min_timeout, timeout)

        # Apply maximum timeout constraint
        if self.max_timeout is not None:
            timeout = min(self.max_timeout, timeout)

        return timeout

    def _create_timeout_response(
        self,
        request: Request,
        timeout_exception: Union[TimeoutException, Exception],
    ) -> Response:
        """
        Create a timeout error response.

        Args:
            request: The original HTTP request object.
            timeout_exception: The timeout exception that occurred.

        Returns:
            Response: HTTP response indicating a timeout error.
        """
        timeout = getattr(timeout_exception, 'timeout', self.default_timeout)

        # Create the response
        response = create_timeout_response(
            timeout=timeout,
            detail=str(timeout_exception) if str(timeout_exception) else None
        )

        # Add timing information
        if hasattr(request, 'start_time'):
            duration = get_request_duration(request)
            response.headers['X-Actual-Duration'] = str(duration)

        return response


def Timeout(
    default_timeout: float = 30.0,
    max_timeout: Optional[float] = None,
    min_timeout: float = 0.1,
    timeout_header: str = "X-Request-Timeout",
    timeout_param: str = "timeout",
    track_duration: bool = True,
    timeout_response_enabled: bool = True,
    exception_on_timeout: bool = False,
) -> TimeoutMiddleware:
    """
    Create a TimeoutMiddleware instance with the specified configuration.

    Args:
        default_timeout: Default timeout in seconds for all requests.
        max_timeout: Maximum allowed timeout from request headers.
        min_timeout: Minimum allowed timeout (default: 0.1).
        timeout_header: Header name to check for timeout values.
        timeout_param: Query parameter name to check for timeout values.
        track_duration: Track request duration in response headers.
        timeout_response_enabled: Return custom timeout responses.
        exception_on_timeout: Raise exception instead of returning timeout response.

    Returns:
        TimeoutMiddleware: Configured timeout middleware instance.

    Example:
        app.add_middleware(Timeout(default_timeout=60.0))
    """
    return TimeoutMiddleware(
        default_timeout=default_timeout,
        max_timeout=max_timeout,
        min_timeout=min_timeout,
        timeout_header=timeout_header,
        timeout_param=timeout_param,
        track_duration=track_duration,
        timeout_response_enabled=timeout_response_enabled,
        exception_on_timeout=exception_on_timeout,
    )
