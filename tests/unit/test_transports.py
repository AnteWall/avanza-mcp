"""Offline checks of real stdio and loopback Streamable HTTP transports."""

import sys
from unittest.mock import AsyncMock

from fastmcp import Client
from fastmcp.client.transports import StdioTransport
from fastmcp.utilities.tests import run_server_async

from avanza_mcp import __version__, mcp
from avanza_mcp.client import AvanzaClient


async def test_stdio_discovery_and_prompt():
    transport = StdioTransport(
        command=sys.executable,
        args=["-c", "from avanza_mcp import main; main()"],
    )
    async with Client(transport) as client:
        assert client.initialize_result.serverInfo.version == __version__
        assert len(await client.list_tools()) == 34
        assert len(await client.list_prompts()) == 3
        prompt = await client.get_prompt("compare_funds", {"fund_names": '["A", "B"]'})
        assert "order_book_id" in prompt.messages[0].content.text
        resource = await client.read_resource("avanza://docs/usage")
        assert resource[0].mimeType == "text/markdown"


async def test_http_tool_and_resource(monkeypatch):
    get = AsyncMock(return_value={"last": 0, "isRealTime": False})
    monkeypatch.setattr(AvanzaClient, "get", get)
    async with run_server_async(mcp) as url:
        async with Client(url) as client:
            assert len(await client.list_tools()) == 34
            result = await client.call_tool(
                "get_stock_quote", {"order_book_id": "5269"}
            )
            assert result.structured_content == {"last": 0.0, "isRealTime": False}
            resource = await client.read_resource("avanza://docs/usage")
            assert resource[0].mimeType == "text/markdown"
    get.assert_awaited_once_with("/_api/market-guide/stock/5269/quote")
