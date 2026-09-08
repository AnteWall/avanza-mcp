"""Resource formatting and shared tool/resource lifecycle through MCP."""

from unittest.mock import AsyncMock

import pytest
from fastmcp import Client
from mcp.shared.exceptions import McpError

from avanza_mcp import __version__, mcp
from avanza_mcp.client import AvanzaClient
from avanza_mcp.resources.instruments import format_fund_markdown, format_stock_markdown


def test_resource_zero_and_missing_values():
    stock = format_stock_markdown(
        {
            "name": "Stock",
            "quote": {"last": 0, "isRealTime": False},
            "company": None,
            "listing": None,
            "keyIndicators": {
                "priceEarningsRatio": 0,
                "directYield": 0,
                "marketCapital": {"value": 0, "currency": "SEK"},
            },
        }
    )
    assert "**Change (source value):** Unknown" in stock
    assert "**Currency:** Unknown" in stock
    assert "**P/E:** 0" in stock
    assert "**Dividend yield (source value):** 0" in stock
    assert "**Real-time flag:** False" in stock
    assert "**Market cap:** 0 SEK" in stock
    fund = format_fund_markdown(
        {
            "name": "Fund",
            "nav": 0,
            "currency": None,
            "development": None,
            "developmentThisYear": 0,
            "productFee": 0,
            "managementFee": 0,
            "fee": None,
        }
    )
    assert "**NAV:** 0" in fund and "**Currency:** Unknown" in fund
    assert "**YTD (source value):** 0" in fund
    assert "**Product fee (source value):** 0" in fund
    assert "**Management fee (source value):** 0" in fund


async def test_tools_and_resources_share_one_client(monkeypatch):
    upstream = AsyncMock()
    enter = AsyncMock(return_value=upstream)
    close = AsyncMock(return_value=None)
    monkeypatch.setattr(AvanzaClient, "__aenter__", enter)
    monkeypatch.setattr(AvanzaClient, "__aexit__", close)
    async with Client(mcp) as client:
        assert client.initialize_result.serverInfo.version == __version__
        assert "order_book_id" in client.initialize_result.instructions
        upstream.get.return_value = {"name": "Fund", "nav": 0, "productFee": 0}
        resource = await client.read_resource("avanza://fund/41567")
        assert resource[0].mimeType == "text/markdown"
        assert "**Product fee (source value):** 0" in resource[0].text
        upstream.get.return_value = {"last": 0}
        result = await client.call_tool("get_stock_quote", {"order_book_id": "5269"})
        assert result.structured_content == {"last": 0.0}
        with pytest.raises(McpError):
            await client.read_resource("avanza://fund/not-an-id")
        assert upstream.get.await_count == 2
        enter.assert_awaited_once()
        close.assert_not_awaited()
    close.assert_awaited_once()
