"""Custom exceptions for Avanza client."""


class AvanzaError(Exception):
    """Base exception for Avanza API errors."""

    pass


class AvanzaAPIError(AvanzaError):
    """API returned an error response."""

    def __init__(
        self, status_code: int, message: str, response: dict | None = None
    ) -> None:
        self.status_code = status_code
        self.message = message
        self.response = response
        super().__init__(f"API error {status_code}: {message}")


class AvanzaAuthError(AvanzaError):
    """Authentication failed or token expired."""

    pass


class AvanzaNotFoundError(AvanzaError):
    """Requested resource not found."""

    pass


class AvanzaRateLimitError(AvanzaError):
    """Rate limit exceeded."""

    def __init__(self, retry_after: int | None = None, message: str | None = None) -> None:
        self.retry_after = retry_after
        msg = message or "Rate limit exceeded"
        if retry_after and not message:
            msg += f", retry after {retry_after}s"
        super().__init__(msg)


class AvanzaTimeoutError(AvanzaError):
    """Request timed out."""

    pass


class AvanzaNetworkError(AvanzaError):
    """Network error occurred during request."""

    pass


class AvanzaRetryableError(AvanzaError):
    """Transient error that should trigger a retry.

    This is an internal exception used for retry logic.
    """

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"Retryable error {status_code}: {message}")
