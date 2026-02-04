"""Unit tests for the Avanza client."""

import pytest
import httpx
import respx

from avanza_mcp.client import (
    AvanzaClient,
    AvanzaAPIError,
    AvanzaNotFoundError,
    AvanzaRateLimitError,
    AvanzaTimeoutError,
    AvanzaNetworkError,
)


@pytest.fixture
def mock_client():
    """Create a mock Avanza client."""
    return AvanzaClient(base_url="https://test.avanza.se", max_retries=1)


class TestAvanzaClientInit:
    """Tests for client initialization."""

    def test_default_values(self):
        """Test default configuration values."""
        client = AvanzaClient()
        assert client._base_url == "https://www.avanza.se"
        assert client._timeout == 30.0
        assert client._connect_timeout == 5.0
        assert client._max_connections == 10
        assert client._max_keepalive_connections == 5
        assert client._max_retries == 3

    def test_custom_values(self):
        """Test custom configuration values."""
        client = AvanzaClient(
            base_url="https://custom.url",
            timeout=60.0,
            connect_timeout=10.0,
            max_connections=20,
            max_keepalive_connections=10,
            max_retries=5,
        )
        assert client._base_url == "https://custom.url"
        assert client._timeout == 60.0
        assert client._connect_timeout == 10.0
        assert client._max_connections == 20
        assert client._max_keepalive_connections == 10
        assert client._max_retries == 5


class TestAvanzaClientContextManager:
    """Tests for context manager functionality."""

    @pytest.mark.asyncio
    async def test_enter_creates_client(self, mock_client):
        """Test that __aenter__ creates httpx client."""
        async with mock_client as client:
            assert client._client is not None
            assert isinstance(client._client, httpx.AsyncClient)

    @pytest.mark.asyncio
    async def test_exit_closes_client(self, mock_client):
        """Test that __aexit__ closes httpx client."""
        async with mock_client as client:
            internal_client = client._client
        # After context exit, the client should be closed
        assert internal_client.is_closed


class TestAvanzaClientGet:
    """Tests for GET requests."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_successful_get(self, mock_client):
        """Test successful GET request."""
        respx.get("https://test.avanza.se/test/endpoint").mock(
            return_value=httpx.Response(200, json={"key": "value"})
        )

        async with mock_client as client:
            result = await client.get("/test/endpoint")
            assert result == {"key": "value"}

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_with_params(self, mock_client):
        """Test GET request with query parameters."""
        respx.get("https://test.avanza.se/test/endpoint").mock(
            return_value=httpx.Response(200, json={"data": "test"})
        )

        async with mock_client as client:
            result = await client.get("/test/endpoint", params={"foo": "bar"})
            assert result == {"data": "test"}

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_404_raises_not_found(self, mock_client):
        """Test that 404 raises AvanzaNotFoundError."""
        respx.get("https://test.avanza.se/test/endpoint").mock(
            return_value=httpx.Response(404, json={"message": "Not found"})
        )

        async with mock_client as client:
            with pytest.raises(AvanzaNotFoundError):
                await client.get("/test/endpoint")

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_429_raises_rate_limit(self, mock_client):
        """Test that 429 raises AvanzaRateLimitError."""
        respx.get("https://test.avanza.se/test/endpoint").mock(
            return_value=httpx.Response(
                429, json={"message": "Rate limited"}, headers={"Retry-After": "60"}
            )
        )

        async with mock_client as client:
            with pytest.raises(AvanzaRateLimitError) as exc_info:
                await client.get("/test/endpoint")
            assert exc_info.value.retry_after == 60

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_empty_response(self, mock_client):
        """Test handling of empty response body."""
        respx.get("https://test.avanza.se/test/endpoint").mock(
            return_value=httpx.Response(200, content=b"")
        )

        async with mock_client as client:
            result = await client.get("/test/endpoint")
            assert result == {}

    @pytest.mark.asyncio
    async def test_get_without_context_manager_raises(self, mock_client):
        """Test that GET without context manager raises RuntimeError."""
        with pytest.raises(RuntimeError, match="Client not initialized"):
            await mock_client.get("/test/endpoint")


class TestAvanzaClientRetry:
    """Tests for retry functionality."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_retry_on_500(self):
        """Test that 500 errors trigger retry."""
        client = AvanzaClient(base_url="https://test.avanza.se", max_retries=3)

        # First two calls fail with 500, third succeeds
        route = respx.get("https://test.avanza.se/test/endpoint")
        route.side_effect = [
            httpx.Response(500, json={"error": "Server error"}),
            httpx.Response(500, json={"error": "Server error"}),
            httpx.Response(200, json={"success": True}),
        ]

        async with client:
            result = await client.get("/test/endpoint")
            assert result == {"success": True}
            assert route.call_count == 3

    @pytest.mark.asyncio
    @respx.mock
    async def test_no_retry_on_400(self):
        """Test that 400 errors don't trigger retry (client errors are not retried)."""
        client = AvanzaClient(base_url="https://test.avanza.se", max_retries=3)

        route = respx.get("https://test.avanza.se/test/endpoint").mock(
            return_value=httpx.Response(400, json={"error": "Bad request"})
        )

        async with client:
            with pytest.raises(AvanzaAPIError) as exc_info:
                await client.get("/test/endpoint")
            # Should only be called once, no retry for client errors
            assert route.call_count == 1
            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    @respx.mock
    async def test_no_retry_on_404(self):
        """Test that 404 errors don't trigger retry."""
        client = AvanzaClient(base_url="https://test.avanza.se", max_retries=3)

        route = respx.get("https://test.avanza.se/test/endpoint").mock(
            return_value=httpx.Response(404, json={"message": "Not found"})
        )

        async with client:
            with pytest.raises(AvanzaNotFoundError):
                await client.get("/test/endpoint")
            # Should only be called once
            assert route.call_count == 1


class TestAvanzaClientHeaders:
    """Tests for request headers."""

    def test_build_headers(self, mock_client):
        """Test that headers are built correctly."""
        headers = mock_client._build_headers()
        assert "User-Agent" in headers
        assert "avanza-mcp" in headers["User-Agent"]
        assert headers["Accept"] == "application/json"


class TestAvanzaClientRequestId:
    """Tests for request ID generation."""

    def test_generate_request_id(self, mock_client):
        """Test that request IDs are generated."""
        request_id = mock_client._generate_request_id()
        assert isinstance(request_id, str)
        assert len(request_id) == 8

    def test_request_ids_are_unique(self, mock_client):
        """Test that request IDs are unique."""
        ids = {mock_client._generate_request_id() for _ in range(100)}
        assert len(ids) == 100
