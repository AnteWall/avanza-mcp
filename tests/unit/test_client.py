"""Unit tests for the Avanza client."""

import json
import logging
import re
import asyncio
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from functools import partial

import pytest
import httpx
import respx
from tenacity import retry
from unittest.mock import AsyncMock
from avanza_mcp.client.endpoints import PublicEndpoint
from avanza_mcp.client.exceptions import (
    AvanzaAuthError,
    AvanzaNetworkError,
    AvanzaTimeoutError,
)

from avanza_mcp.client import (
    AvanzaClient,
    AvanzaAPIError,
    AvanzaNotFoundError,
    AvanzaRateLimitError,
)


@pytest.fixture(autouse=True)
def no_retry_sleep(monkeypatch):
    sleep = AsyncMock()
    monkeypatch.setattr("avanza_mcp.client.base.retry", partial(retry, sleep=sleep))
    return sleep


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
        assert client._request_timeout == 30.0

    def test_custom_values(self):
        """Test custom configuration values."""
        client = AvanzaClient(
            base_url="https://custom.url",
            timeout=60.0,
            connect_timeout=10.0,
            max_connections=20,
            max_keepalive_connections=10,
            max_retries=5,
            request_timeout=90.0,
        )
        assert client._base_url == "https://custom.url"
        assert client._timeout == 60.0
        assert client._connect_timeout == 10.0
        assert client._max_connections == 20
        assert client._max_keepalive_connections == 10
        assert client._max_retries == 5
        assert client._request_timeout == 90.0


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
        ).mock(return_value=httpx.Response(200, json={"key": "value"}))

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
        ).mock(return_value=httpx.Response(200, json={"data": "test"}))

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
        ).mock(return_value=httpx.Response(200, content=b""))

        async with mock_client as client:
            with pytest.raises(AvanzaAPIError, match="Empty JSON response"):
                await getattr(client, method)("/test/endpoint")

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
        ).mock(return_value=httpx.Response(400, json={"error": "Bad request"}))

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
        ).mock(return_value=httpx.Response(404, json={"message": "Not found"}))
        async with client:
            with pytest.raises(AvanzaNotFoundError):
                await getattr(client, method)("/test/endpoint")
            assert route.call_count == 1


@pytest.mark.parametrize("method", ["get", "post"])
class TestClientFailureBoundaries:
    @pytest.mark.parametrize(
        "failure,public_error",
        [
            (httpx.ConnectTimeout, AvanzaTimeoutError),
            (httpx.ReadTimeout, AvanzaTimeoutError),
            (httpx.WriteTimeout, AvanzaTimeoutError),
            (httpx.ConnectError, AvanzaNetworkError),
            (httpx.ReadError, AvanzaNetworkError),
            (httpx.WriteError, AvanzaNetworkError),
            (httpx.RemoteProtocolError, AvanzaNetworkError),
        ],
    )
    @pytest.mark.parametrize("recover", [True, False])
    async def test_transient_failures(
        self, method, failure, public_error, recover, no_retry_sleep
    ):
        async with AvanzaClient() as client:
            request = AsyncMock(
                side_effect=[
                    failure("transient"),
                    failure("transient"),
                    httpx.Response(200, json=[]) if recover else failure("exhausted"),
                ]
            )
            client._client.request = request
            if recover:
                assert await getattr(client, method)("/test") == []
            else:
                with pytest.raises(public_error) as exc:
                    await getattr(client, method)("/test")
                assert isinstance(exc.value.__cause__, failure)
            assert request.await_count == 3
            assert no_retry_sleep.await_count == 2
            assert 2 <= no_retry_sleep.call_args_list[0].args[0] <= 3
            assert 4 <= no_retry_sleep.call_args_list[1].args[0] <= 5

    @pytest.mark.parametrize(
        "failure,public_error",
        [
            (httpx.PoolTimeout, AvanzaTimeoutError),
            (httpx.LocalProtocolError, httpx.LocalProtocolError),
            (httpx.UnsupportedProtocol, httpx.UnsupportedProtocol),
        ],
    )
    async def test_nontransient_transport(
        self, method, failure, public_error, no_retry_sleep
    ):
        async with AvanzaClient() as client:
            client._client.request = AsyncMock(side_effect=failure("failure"))
            with pytest.raises(public_error):
                await getattr(client, method)("/test")
            assert client._client.request.await_count == 1
            no_retry_sleep.assert_not_awaited()

    async def test_server_exhaustion(self, method):
        async with AvanzaClient() as client:
            client._client.request = AsyncMock(
                return_value=httpx.Response(503, json={"message": "Unavailable"})
            )
            with pytest.raises(AvanzaAPIError) as exc:
                await getattr(client, method)("/test")
            assert type(exc.value) is AvanzaAPIError
            assert exc.value.status_code == 503
            assert exc.value.response == {"message": "Unavailable"}
            assert "will retry" not in str(exc.value)
            assert client._client.request.await_count == 3

    @pytest.mark.parametrize(
        "status,error",
        [
            (400, AvanzaAPIError),
            (401, AvanzaAuthError),
            (403, AvanzaAuthError),
            (404, AvanzaNotFoundError),
            (408, AvanzaAPIError),
            (429, AvanzaRateLimitError),
            (499, AvanzaAPIError),
        ],
    )
    @pytest.mark.parametrize(
        "body",
        [
            b'{"message":null}',
            b'{"message":123}',
            b'{"message":["bad"]}',
            b'{"message":{"bad":true}}',
            b"[]",
            b"null",
            b"not json",
            b"x" * 2000,
        ],
    )
    async def test_malformed_errors(self, method, status, error, body):
        async with AvanzaClient() as client:
            client._client.request = AsyncMock(
                return_value=httpx.Response(status, content=body)
            )
            with pytest.raises(error) as exc:
                await getattr(client, method)("/test")
            assert len(str(exc.value)) < 600
            assert client._client.request.await_count == 1

    @pytest.mark.parametrize(
        "header,expected",
        [
            ("60", 60),
            (" 0 ", 0),
            ("invalid", None),
            ("-1", None),
            ("1.5", None),
            ("", None),
            ("Wed, 99 Jan 2020 00:00:00 GMT", None),
            ("Wed, 01 Jan 2020 00:00:00 GMT", 0),
        ],
    )
    async def test_retry_after(self, method, header, expected):
        async with AvanzaClient() as client:
            client._client.request = AsyncMock(
                return_value=httpx.Response(
                    429, json={}, headers={"Retry-After": header}
                )
            )
            with pytest.raises(AvanzaRateLimitError) as exc:
                await getattr(client, method)("/test")
            assert exc.value.retry_after == expected
            assert "retry" in str(exc.value)
            assert client._client.request.await_count == 1

    async def test_retry_after_future_date(self, method):
        date = format_datetime(
            datetime.now(timezone.utc) + timedelta(seconds=60), usegmt=True
        )
        async with AvanzaClient() as client:
            client._client.request = AsyncMock(
                return_value=httpx.Response(429, headers={"Retry-After": date})
            )
            with pytest.raises(AvanzaRateLimitError) as exc:
                await getattr(client, method)("/test")
            assert 59 <= exc.value.retry_after <= 60

    @pytest.mark.parametrize(
        "body", [b"", b" ", b"null", b"123", b'"text"', b"false", b"invalid"]
    )
    async def test_invalid_json(self, method, body):
        async with AvanzaClient() as client:
            client._client.request = AsyncMock(
                return_value=httpx.Response(200, content=body)
            )
            with pytest.raises(AvanzaAPIError, match="JSON response"):
                await getattr(client, method)("/test")
            assert client._client.request.await_count == 1

    @pytest.mark.parametrize("during_backoff", [False, True])
    @pytest.mark.parametrize("cancel", [False, True])
    async def test_deadline_and_cancellation(
        self, method, during_backoff, cancel, no_retry_sleep
    ):
        entered = asyncio.Event()

        async def block(*args, **kwargs):
            entered.set()
            await asyncio.Future()

        async with AvanzaClient(request_timeout=30 if cancel else 0.01) as client:
            client._client.request = AsyncMock(
                side_effect=httpx.ReadTimeout("retry") if during_backoff else block
            )
            if during_backoff:
                no_retry_sleep.side_effect = block
            task = asyncio.create_task(getattr(client, method)("/test"))
            await entered.wait()
            if cancel:
                task.cancel()
            with pytest.raises(
                asyncio.CancelledError if cancel else AvanzaTimeoutError
            ):
                await task
            assert client._client.request.await_count == 1


@pytest.mark.parametrize(
    "value",
    [
        "",
        "../123",
        "1/2",
        "1?x=2",
        "-1",
        "1.0",
        " 123",
        "123 ",
        "\u0661",
        "\u00b2",
        True,
        None,
    ],
)
def test_invalid_order_book_id(value):
    with pytest.raises(ValueError, match="Order-book id"):
        PublicEndpoint.STOCK_INFO.format(id=value)


@pytest.mark.parametrize("value", [123, "123", "00123", "0"])
def test_order_book_id_and_period(value):
    assert (
        PublicEndpoint.FUND_CHART.format(id=value, time_period="three_years")
        == f"/_api/fund-guide/chart/{value}/three_years"
    )
    assert PublicEndpoint.SEARCH.format() == PublicEndpoint.SEARCH.value


@pytest.mark.parametrize("timeout", [0, -1, float("inf"), float("nan")])
def test_invalid_request_deadline(timeout):
    with pytest.raises(ValueError, match="request_timeout"):
        AvanzaClient(request_timeout=timeout)
