"""Base HTTP client for Avanza API."""

from typing import Any

import httpx

from .. import __version__
from .exceptions import (
    AvanzaAPIError,
    AvanzaAuthError,
    AvanzaNotFoundError,
    AvanzaRateLimitError,
)


class AvanzaClient:
    """Async HTTP client for Avanza public API."""

    def __init__(
        self,
        base_url: str = "https://www.avanza.se",
        timeout: float = 30.0,
    ) -> None:
        """Initialize Avanza client.

        Args:
            base_url: Base URL for Avanza API
            timeout: Request timeout in seconds
        """
        self._base_url = base_url
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "AvanzaClient":
        """Initialize httpx client.

        Returns:
            Self for context manager usage
        """
        headers = self._build_headers()
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers=headers,
            timeout=self._timeout,
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

    def _build_headers(self) -> dict[str, str]:
        """Build request headers.

        Returns:
            Dictionary of HTTP headers
        """
        return {
            "User-Agent": f"avanza-mcp/{__version__}",
            "Accept": "application/json",
        }

    def _handle_error(self, response: httpx.Response) -> None:
        """Handle HTTP error responses.

        Args:
            response: HTTP response object

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

        # Handle specific error types
        if status_code == 404:
            raise AvanzaNotFoundError(message)
        elif status_code in (401, 403):
            raise AvanzaAuthError(message)
        elif status_code == 429:
            retry_after = response.headers.get("Retry-After")
            retry_after_int = int(retry_after) if retry_after else None
            raise AvanzaRateLimitError(retry_after_int)
        else:
            try:
                response_dict = response.json()
            except Exception:
                response_dict = None
            raise AvanzaAPIError(status_code, message, response_dict)

    async def get(
        self, path: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """GET request with error handling and JSON parsing.

        Args:
            path: API endpoint path
            params: Optional query parameters

        Returns:
            JSON response as dictionary

        Raises:
            AvanzaError: If request fails or returns error
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")

        response = await self._client.get(path, params=params)

        if not response.is_success:
            self._handle_error(response)

        return response.json()

    async def post(
        self, path: str, json: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """POST request with error handling and JSON parsing.

        Args:
            path: API endpoint path
            json: Optional JSON body

        Returns:
            JSON response as dictionary

        Raises:
            AvanzaError: If request fails or returns error
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")

        response = await self._client.post(path, json=json)

        if not response.is_success:
            self._handle_error(response)

        return response.json()
