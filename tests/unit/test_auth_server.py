"""Local stdio launch policy for the opt-in authenticated server."""

import os
import subprocess
import sys
from unittest.mock import Mock

import httpx
import pytest
import respx
from fastmcp import Client
from fastmcp.exceptions import ToolError

from avanza_mcp import main
from avanza_mcp.auth.browser import AuthStatus
from avanza_mcp.auth.server import create_auth_server, run_auth_server
from avanza_mcp.client.bankid import SessionMaterial


class FakeAuth:
    def __init__(self):
        self.closed = False
        self.opened = 0
        self._session = None

    async def open_browser(self):
        self.opened += 1
        return AuthStatus(
            state="awaiting_approval", message="Approve in the local browser."
        )

    async def open_disconnect_browser(self):
        self.opened += 1
        return self.status()

    def status(self):
        return AuthStatus(state="disconnected", message="Avanza is not connected.")

    @property
    def session(self):
        return self._session

    async def aclose(self):
        self.closed = True

    async def restore(self):
        return self.status()

    async def invalidate_session(self):
        self._session = None
        return None


async def test_auth_server_mounts_public_contract_and_adds_auth_tools():
    auth = FakeAuth()
    server = create_auth_server(auth)  # type: ignore[arg-type]
    async with Client(server) as client:
        tools = {tool.name for tool in await client.list_tools()}
        assert len(tools) == 51
        assert {
            "connect_avanza",
            "disconnect_avanza",
            "get_auth_status",
            "get_accounts",
            "get_holdings",
            "get_transactions",
            "get_credit_info",
            "get_watchlists",
            "get_price_alerts",
            "get_current_offers",
            "get_portfolio_insights",
            "get_instrument_news",
            "get_forum_posts",
            "get_insider_transactions",
            "get_active_orders",
            "get_deals",
            "get_stop_loss_orders",
        } <= tools
        assert len(await client.list_prompts()) == 3
        connected = await client.call_tool("connect_avanza", {})
        assert connected.structured_content["state"] == "awaiting_approval"
        status = await client.call_tool("get_auth_status", {})
        assert status.structured_content == {
            "state": "disconnected",
            "message": "Avanza is not connected.",
            "error_code": None,
        }
        with pytest.raises(ToolError, match="AVANZA_AUTH_REQUIRED"):
            await client.call_tool("get_accounts", {})
    assert auth.closed
    assert auth.opened == 2


@respx.mock
async def test_existing_market_tools_reuse_authenticated_session():
    auth = FakeAuth()
    auth._session = SessionMaterial((), "sentinel-token")
    route = respx.get("https://www.avanza.se/_api/market-guide/stock/123/quote").mock(
        return_value=httpx.Response(200, json={"last": 10, "isRealTime": True})
    )

    async with Client(create_auth_server(auth)) as client:  # type: ignore[arg-type]
        result = await client.call_tool("get_stock_quote", {"order_book_id": "123"})

    assert result.structured_content["last"] == 10
    assert route.calls.last.request.headers["x-securitytoken"] == "sentinel-token"


def test_auth_transport_is_stdio(monkeypatch):
    server = Mock()
    create = Mock(return_value=server)
    monkeypatch.setattr("avanza_mcp.auth.server.create_auth_server", create)
    run_auth_server()
    create.assert_called_once_with()
    server.run.assert_called_once_with()


def test_cli_preserves_public_default(monkeypatch):
    run = Mock()
    monkeypatch.delenv("AVANZA_MCP_AUTH", raising=False)
    monkeypatch.setattr("avanza_mcp.mcp.run", run)
    main()
    run.assert_called_once_with()


def test_cli_selects_auth_stdio_from_environment(monkeypatch):
    run = Mock()
    monkeypatch.setenv("AVANZA_MCP_AUTH", "1")
    monkeypatch.setattr("avanza_mcp.auth.server.run_auth_server", run)
    main()
    run.assert_called_once_with()


def test_cli_rejects_ambiguous_auth_environment(monkeypatch):
    monkeypatch.setenv("AVANZA_MCP_AUTH", "true")
    with pytest.raises(SystemExit):
        main()


def test_public_startup_does_not_import_account_modules():
    script = """
import sys
from avanza_mcp import main, mcp
mcp.run = lambda: None
main()
assert 'avanza_mcp.auth.server' not in sys.modules
"""
    env = os.environ.copy()
    env.pop("AVANZA_MCP_AUTH", None)
    subprocess.run([sys.executable, "-c", script], check=True, env=env)
