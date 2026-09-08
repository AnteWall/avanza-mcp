"""Unit tests for the Avanza client."""

import json
import logging
import re

import pytest
import httpx
import respx

from avanza_mcp.client import (
    AvanzaClient,
    AvanzaAPIError,
    AvanzaNotFoundError,
    AvanzaRateLimitError,
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

    async def test_enter_creates_client(self, mock_client):
        """Test that __aenter__ creates httpx client."""
        async with mock_client as client:
            assert client._client is not None
            assert isinstance(client._client, httpx.AsyncClient)

    async def test_exit_closes_client(self, mock_client):
        """Test that __aexit__ closes httpx client."""
        async with mock_client as client:
            internal_client = client._client
        # After context exit, the client should be closed
        assert internal_client.is_closed


@pytest.mark.parametrize("method", ["get", "post"])
class TestAvanzaClientRequests:
    """Test both public methods through the shared request pipeline."""

    @respx.mock
    async def test_successful_request(self, mock_client, method, caplog):
        """Test response parsing, outgoing headers, and logged request IDs."""
        caplog.set_level(logging.DEBUG, logger="avanza_mcp.client.base")
        route = respx.route(
            method=method.upper(), url="https://test.avanza.se/test/endpoint"
        ).mock(
            return_value=httpx.Response(200, json={"key": "value"})
        )

        async with mock_client as client:
            result = await getattr(client, method)("/test/endpoint")
            assert result == {"key": "value"}

        assert route.call_count == 1
        headers = route.calls.last.request.headers
        assert "User-Agent" in headers
        assert "avanza-mcp" in headers["User-Agent"]
        assert headers["Accept"] == "application/json"
        assert any(
            re.match(
                rf"{method.upper()} \[[0-9a-f]{{8}}\] /test/endpoint(?: |$)",
                record.message,
            )
            for record in caplog.records
            if record.name == "avanza_mcp.client.base"
        )

    @respx.mock
    async def test_request_with_payload(self, mock_client, method):
        """Test query parameters for GET and a JSON body for POST."""
        route = respx.route(
            method=method.upper(), url="https://test.avanza.se/test/endpoint"
        ).mock(
            return_value=httpx.Response(200, json={"data": "test"})
        )

        async with mock_client as client:
            arguments = {"params" if method == "get" else "json": {"foo": "bar"}}
            result = await getattr(client, method)("/test/endpoint", **arguments)
            assert result == {"data": "test"}

        assert route.call_count == 1
        request = route.calls.last.request
        if method == "get":
            assert dict(request.url.params) == {"foo": "bar"}
            assert request.content == b""
        else:
            assert json.loads(request.content) == {"foo": "bar"}
            assert not request.url.params

    @respx.mock
    async def test_429_raises_rate_limit(self, mock_client, method):
        """Test that 429 raises AvanzaRateLimitError."""
        respx.route(
            method=method.upper(), url="https://test.avanza.se/test/endpoint"
        ).mock(
            return_value=httpx.Response(
                429, json={"message": "Rate limited"}, headers={"Retry-After": "60"}
            )
        )

        async with mock_client as client:
            with pytest.raises(AvanzaRateLimitError) as exc_info:
                await getattr(client, method)("/test/endpoint")
            assert exc_info.value.retry_after == 60

    @respx.mock
    async def test_empty_response(self, mock_client, method):
        """Test handling of empty response body."""
        respx.route(
            method=method.upper(), url="https://test.avanza.se/test/endpoint"
        ).mock(
            return_value=httpx.Response(200, content=b"")
        )

        async with mock_client as client:
            result = await getattr(client, method)("/test/endpoint")
            assert result == {}

    async def test_without_context_manager_raises(self, mock_client, method):
        """Test that requests without context manager raise RuntimeError."""
        with pytest.raises(RuntimeError, match="Client not initialized"):
            await getattr(mock_client, method)("/test/endpoint")


@pytest.mark.parametrize("method", ["get", "post"])
class TestAvanzaClientRetry:
    """Tests for retry functionality."""

    @respx.mock
    async def test_retry_on_500(self, method):
        """Test that 500 errors trigger retry."""
        client = AvanzaClient(base_url="https://test.avanza.se", max_retries=3)

        # First two calls fail with 500, third succeeds
        route = respx.route(
            method=method.upper(), url="https://test.avanza.se/test/endpoint"
        )
        route.side_effect = [
            httpx.Response(500, json={"error": "Server error"}),
            httpx.Response(500, json={"error": "Server error"}),
            httpx.Response(200, json={"success": True}),
        ]

        async with client:
            result = await getattr(client, method)("/test/endpoint")
            assert result == {"success": True}
            assert route.call_count == 3

    @respx.mock
    async def test_no_retry_on_400(self, method):
        """Test that 400 errors don't trigger retry (client errors are not retried)."""
        client = AvanzaClient(base_url="https://test.avanza.se", max_retries=3)

        route = respx.route(
            method=method.upper(), url="https://test.avanza.se/test/endpoint"
        ).mock(
            return_value=httpx.Response(400, json={"error": "Bad request"})
        )

        async with client:
            with pytest.raises(AvanzaAPIError) as exc_info:
                await getattr(client, method)("/test/endpoint")
            # Should only be called once, no retry for client errors
            assert route.call_count == 1
            assert exc_info.value.status_code == 400

    @respx.mock
    async def test_no_retry_on_404(self, method):
        """Test that 404 errors don't trigger retry."""
        client = AvanzaClient(base_url="https://test.avanza.se", max_retries=3)

        route = respx.route(
            method=method.upper(), url="https://test.avanza.se/test/endpoint"
        ).mock(
            return_value=httpx.Response(404, json={"message": "Not found"})
        )

        async with client:
            with pytest.raises(AvanzaNotFoundError):
                await getattr(client, method)("/test/endpoint")
            # Should only be called once
            assert route.call_count == 1
