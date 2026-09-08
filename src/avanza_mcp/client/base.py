"""Base HTTP client for Avanza API."""

import logging
import uuid
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .. import __version__
from .exceptions import (
    AvanzaAPIError,
    AvanzaAuthError,
    AvanzaNetworkError,
    AvanzaNotFoundError,
    AvanzaRateLimitError,
    AvanzaRetryableError,
    AvanzaTimeoutError,
)

logger = logging.getLogger(__name__)


class AvanzaClient:
    """Async HTTP client for Avanza public API."""

    # Default configuration
    DEFAULT_BASE_URL = "https://www.avanza.se"
    DEFAULT_TIMEOUT = 30.0
    DEFAULT_CONNECT_TIMEOUT = 5.0
    DEFAULT_MAX_CONNECTIONS = 10
    DEFAULT_MAX_KEEPALIVE = 5
    DEFAULT_MAX_RETRIES = 3

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        connect_timeout: float = DEFAULT_CONNECT_TIMEOUT,
        max_connections: int = DEFAULT_MAX_CONNECTIONS,
        max_keepalive_connections: int = DEFAULT_MAX_KEEPALIVE,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        """Initialize Avanza client.

        Args:
            base_url: Base URL for Avanza API
            timeout: Read timeout in seconds
            connect_timeout: Connection timeout in seconds
            max_connections: Maximum number of concurrent connections
            max_keepalive_connections: Maximum number of keepalive connections
            max_retries: Maximum number of retry attempts for transient failures
        """
        self._base_url = base_url
        self._timeout = timeout
        self._connect_timeout = connect_timeout
        self._max_connections = max_connections
        self._max_keepalive_connections = max_keepalive_connections
        self._max_retries = max_retries
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "AvanzaClient":
        """Initialize httpx client with connection pooling.

        Returns:
            Self for context manager usage
        """
        # Configure timeouts with separate connect and read values
        timeout = httpx.Timeout(
            self._timeout,
            connect=self._connect_timeout,
        )

        # Configure connection pooling limits
        limits = httpx.Limits(
            max_connections=self._max_connections,
            max_keepalive_connections=self._max_keepalive_connections,
        )

        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "User-Agent": f"avanza-mcp/{__version__}",
                "Accept": "application/json",
            },
            timeout=timeout,
            limits=limits,
            follow_redirects=True,
        )

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Clean up httpx client.

        Args:
            exc_type: Exception type if an error occurred
            exc_val: Exception value if an error occurred
            exc_tb: Exception traceback if an error occurred
        """
        if self._client:
            await self._client.aclose()

    def _handle_error(
        self,
        response: httpx.Response,
        path: str,
        request_id: str,
        params: dict[str, Any] | None = None,
    ) -> None:
        """Handle HTTP error responses with enhanced context.

        Args:
            response: HTTP response object
            path: Request path for error context
            request_id: Request ID for debugging
            params: Query parameters for error context

        Raises:
            AvanzaNotFoundError: If resource not found (404)
            AvanzaAuthError: If authentication failed (401, 403)
            AvanzaRateLimitError: If rate limit exceeded (429)
            AvanzaAPIError: For other API errors
        """
        status_code = response.status_code

        # Try to extract error message from response
        try:
            error_data = response.json()
            message = error_data.get("message", response.text)
        except Exception:
            message = response.text or f"HTTP {status_code}"

        # Add request context to error message
        context = f"[{request_id}] {path}"
        if params:
            context += f" params={params}"

        logger.warning(
            "API error: status=%d path=%s request_id=%s message=%s",
            status_code,
            path,
            request_id,
            message[:200],  # Truncate long messages
        )

        # Handle specific error types
        if status_code == 404:
            raise AvanzaNotFoundError(f"{context}: {message}")
        elif status_code in (401, 403):
            raise AvanzaAuthError(f"{context}: {message}")
        elif status_code == 429:
            retry_after = response.headers.get("Retry-After")
            retry_after_int = int(retry_after) if retry_after else None
            raise AvanzaRateLimitError(retry_after_int, f"{context}: {message}")
        else:
            try:
                response_dict = response.json()
            except Exception:
                response_dict = None
            raise AvanzaAPIError(status_code, f"{context}: {message}", response_dict)

    async def get(
        self, path: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """GET request with retry logic, error handling, and JSON parsing.

        Automatically retries on transient failures (network errors, timeouts,
        server errors) with exponential backoff.

        Args:
            path: API endpoint path
            params: Optional query parameters

        Returns:
            JSON response as dictionary

        Raises:
            AvanzaError: If request fails after all retries
        """
        return await self._request("GET", path, params=params)

    async def post(
        self, path: str, json: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """POST request with retry logic, error handling, and JSON parsing.

        Automatically retries on transient failures (network errors, timeouts,
        server errors) with exponential backoff.

        Args:
            path: API endpoint path
            json: Optional JSON body

        Returns:
            JSON response as dictionary

        Raises:
            AvanzaError: If request fails after all retries
        """
        return await self._request("POST", path, json=json)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send a request through the shared retry and response pipeline."""
        client = self._client
        if not client:
            raise RuntimeError("Client not initialized. Use async context manager.")

        request_id = str(uuid.uuid4())[:8]
        post_prefix = "POST " if method == "POST" else ""

        @retry(
            retry=retry_if_exception_type(
                (httpx.TimeoutException, httpx.NetworkError, AvanzaRetryableError)
            ),
            stop=stop_after_attempt(self._max_retries),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            reraise=True,
            before_sleep=lambda retry_state: logger.info(
                f"Retrying {post_prefix}request [%s] %s, attempt %d after %s",
                request_id,
                path,
                retry_state.attempt_number,
                type(retry_state.outcome.exception()).__name__
                if retry_state.outcome
                else "unknown",
            ),
        )
        async def _request_with_retry() -> dict[str, Any]:
            try:
                response = await client.request(method, path, params=params, json=json)
            except httpx.TimeoutException as e:
                logger.warning(
                    "POST timeout [%s] %s: %s"
                    if method == "POST"
                    else "Request timeout [%s] %s: %s",
                    request_id,
                    path,
                    str(e),
                )
                raise AvanzaTimeoutError(
                    f"[{request_id}] Request timeout after {self._timeout}s: {path}"
                ) from e
            except httpx.NetworkError as e:
                logger.warning(
                    "POST network error [%s] %s: %s"
                    if method == "POST"
                    else "Network error [%s] %s: %s",
                    request_id,
                    path,
                    str(e),
                )
                raise AvanzaNetworkError(
                    f"[{request_id}] Network error: {path} - {str(e)}"
                ) from e

            if not response.is_success:
                # Check if this is a retryable server error
                if response.status_code >= 500:
                    # Raise specific retryable error to trigger retry
                    raise AvanzaRetryableError(
                        response.status_code,
                        f"[{request_id}] Server error (will retry): {path}",
                    )
                # Non-retryable errors
                self._handle_error(response, path, request_id, params)

            # Handle empty responses
            if not response.content:
                logger.debug(f"Empty {post_prefix}response [%s] %s", request_id, path)
                return {}

            # Parse JSON response
            try:
                return response.json()
            except Exception as e:
                logger.error(
                    f"{post_prefix}JSON parse error [%s] %s: %s", request_id, path, str(e)
                )
                raise AvanzaAPIError(
                    response.status_code,
                    f"[{request_id}] Invalid JSON response: {path}",
                ) from e

        if method == "POST":
            logger.debug("POST [%s] %s", request_id, path)
        else:
            logger.debug("GET [%s] %s params=%s", request_id, path, params)
        return await _request_with_retry()
