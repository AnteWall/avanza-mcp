"""Offline tests of the actual registered MCP input/output contracts."""

import json
from unittest.mock import AsyncMock

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from jsonschema import validate

from avanza_mcp import mcp
from avanza_mcp.client import AvanzaClient


@pytest.fixture
def upstream(monkeypatch):
    client = AsyncMock()
    monkeypatch.setattr(AvanzaClient, "__aenter__", AsyncMock(return_value=client))
    monkeypatch.setattr(AvanzaClient, "__aexit__", AsyncMock(return_value=None))
    return client


async def test_registered_schemas_and_annotations():
    async with Client(mcp) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}
    assert len(tools) == 34
    for tool in tools.values():
        props = tool.inputSchema["properties"]
        assert "instrument_id" not in props and "ctx" not in props
        if "order_book_id" in props:
            assert props["order_book_id"]["pattern"] == "^[0-9]+$"
            assert "order_book_id" in tool.inputSchema["required"]
        if "limit" in props:
            assert props["limit"]["minimum"] == 1
            assert props["limit"]["maximum"] in (50, 100)
        if "offset" in props:
            assert props["offset"]["minimum"] == 0
        assert tool.annotations.readOnlyHint is True
        assert tool.annotations.destructiveHint is False
        assert tool.annotations.idempotentHint is True
        assert tool.annotations.openWorldHint is True
        assert tool.outputSchema
    fund = tools["get_fund_info"].outputSchema
    assert "navDate" in fund["properties"] and "nav_date" not in fund["properties"]
    assert {item.get("type") for item in fund["properties"]["nav"]["anyOf"]} == {
        "string",
        "null",
    }
    assert tools["filter_etfs"].inputSchema["properties"]["sort_order"]["enum"] == [
        "asc",
        "desc",
    ]
    assert (
        tools["list_futures_forwards"].inputSchema["properties"]["end_dates"]["anyOf"][
            0
        ]["items"]["format"]
        == "date"
    )


@pytest.mark.parametrize(
    "name,args",
    [
        ("get_stock_quote", {"order_book_id": "../123"}),
        ("get_stock_quote", {"order_book_id": "１２３"}),
        ("get_stock_quote", {"instrument_id": "123"}),
        ("search_instruments", {"query": " "}),
        ("search_instruments", {"query": "x", "limit": 51}),
        ("get_recent_trades", {"order_book_id": "123", "limit": 0}),
        ("get_stock_chart", {"order_book_id": "123", "offset": -1}),
        ("get_stock_chart", {"order_book_id": "123", "time_period": "daily"}),
        ("filter_etfs", {"limit": 101}),
        ("filter_warrants", {"sort_order": "descending"}),
        ("list_futures_forwards", {"end_dates": ["2026-02-30"]}),
    ],
)
async def test_mcp_validation_before_upstream(upstream, name, args):
    async with Client(mcp) as client:
        with pytest.raises(ToolError):
            await client.call_tool(name, args)
    upstream.get.assert_not_awaited()
    upstream.post.assert_not_awaited()


async def test_exact_lookup_and_curated_search(upstream):
    upstream.post.return_value = {
        "totalNumberOfHits": 2,
        "searchQuery": "123",
        "hits": [
            {
                "type": "STOCK",
                "title": "Wrong",
                "orderBookId": "9123",
                "highlightedTitle": "<b>Wrong</b>",
            },
            {
                "type": "FUND",
                "title": "Exact",
                "orderBookId": "123",
                "marketPlaceName": "Funds",
                "price": {"currency": "SEK"},
                "isin": "SE123",
            },
        ],
    }
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_instrument_by_order_book_id", {"order_book_id": "123"}
        )
        assert result.structured_content == {
            "order_book_id": "123",
            "name": "Exact",
            "type": "FUND",
            "exchange": "Funds",
            "isin": "SE123",
            "currency": "SEK",
        }
        assert upstream.post.call_args.kwargs["json"]["pagination"] == {
            "size": 50,
            "from": 0,
        }
        result = await client.call_tool(
            "search_instruments", {"query": "123", "limit": 1}
        )
        assert result.structured_content["returned"] == 1
        assert "highlight" not in json.dumps(result.structured_content)
        with pytest.raises(ToolError, match="not authoritative"):
            await client.call_tool(
                "get_instrument_by_order_book_id", {"order_book_id": "456"}
            )


async def test_shared_client_and_json_output(upstream):
    upstream.get.return_value = {
        "name": "Test",
        "nav": "0.00",
        "navDate": "2026-09-08",
        "development": {"oneWeek": "0"},
    }
    async with Client(mcp) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}
        result = await client.call_tool("get_fund_info", {"order_book_id": "123"})
        content = result.structured_content
        validate(content, tools["get_fund_info"].outputSchema)
        assert "currency" not in content and "tradeable" not in content
        assert content["nav"] == "0.00" and content["navDate"] == "2026-09-08"
        assert content["development"] == {"oneWeek": "0"}
        upstream.get.return_value = {"last": 0, "buy": None, "isRealTime": False}
        result = await client.call_tool("get_stock_quote", {"order_book_id": "123"})
        validate(result.structured_content, tools["get_stock_quote"].outputSchema)
        assert result.structured_content["last"] == 0
        assert result.structured_content["buy"] is None
        assert result.structured_content["isRealTime"] is False
        assert "sell" not in result.structured_content
        AvanzaClient.__aenter__.assert_awaited_once()
    AvanzaClient.__aexit__.assert_awaited_once()
    assert upstream.get.await_count == 2


async def test_chart_trade_and_analysis_pagination(upstream):
    points = [
        {
            "timestamp": timestamp,
            "open": 0,
            "close": 1,
            "high": 2,
            "low": 0,
            "totalVolumeTraded": 0,
            "rawExtra": {"x": 1},
        }
        for timestamp in (30, 10, 20)
    ]
    async with Client(mcp) as client:
        upstream.get.return_value = {
            "ohlc": points,
            "from": "2026-09-01",
            "to": "2026-09-08",
            "pagination": {"upstream": "retained"},
        }
        result = await client.call_tool(
            "get_stock_chart", {"order_book_id": "123", "offset": 1, "limit": 1}
        )
        content = result.structured_content
        assert content["data"]["ohlc"] == [points[1]]
        assert (
            content["data"]["from"] == "2026-09-01" and "from_" not in content["data"]
        )
        assert content["data"]["pagination"] == {"upstream": "retained"}
        assert content["pagination"] == {
            "offset": 1,
            "limit": 1,
            "total": 3,
            "returned": 1,
            "has_more": True,
        }
        upstream.get.return_value = []
        result = await client.call_tool(
            "get_recent_trades", {"order_book_id": "123", "offset": 5}
        )
        assert result.structured_content["trades"] == []
        assert result.structured_content["pagination"]["has_more"] is False
        point = {
            "reportType": "FULL_YEAR",
            "financialYear": 2025,
            "value": 0,
            "date": "2026-01-28",
        }
        upstream.get.return_value = {
            "dividendsByYear": {
                "dividendPerShare": [point, point],
                "directYieldRatio": [],
            }
        }
        result = await client.call_tool(
            "get_dividends",
            {"order_book_id": "123", "metric": "dividendPerShare", "limit": 1},
        )
        assert result.structured_content["data"] == {
            "dividendsByYear": {"dividendPerShare": [point]}
        }
        assert result.structured_content["pagination"]["total"] == 2
        upstream.get.return_value = {}
        result = await client.call_tool(
            "get_company_financials", {"order_book_id": "123", "metric": "sales"}
        )
        assert result.structured_content["data"] == {}
        assert result.structured_content["pagination"]["total"] is None


@pytest.mark.parametrize(
    "name,field,points",
    [
        (
            "get_number_of_owners",
            "ownersPoints",
            [
                {"timestamp": 30, "numberOfOwners": 0},
                {"timestamp": 10, "numberOfOwners": 2},
            ],
        ),
        (
            "get_short_selling",
            "shortSellingHistory",
            [{"timestamp": 10, "ratio": 0}, {"timestamp": 30, "ratio": 0.0099}],
        ),
    ],
)
async def test_typed_history_pages(upstream, name, field, points):
    payload = {field: points, "pagination": {"source": True}}
    if field == "ownersPoints":
        payload["historySummary"] = {
            "oneYearChangePercent": 0.0513,
            "oneYearChange": 10233,
            "thisYearChangePercent": 0.0371,
            "thisYearChange": 7508,
        }
    upstream.get.return_value = payload
    async with Client(mcp) as client:
        schema = next(
            tool.outputSchema for tool in await client.list_tools() if tool.name == name
        )
        result = await client.call_tool(name, {"order_book_id": "5269", "limit": 1})
        content = result.structured_content
        validate(content, schema)
        assert content["data"][field] == points[:1]
        assert content["data"]["pagination"] == {"source": True}
        assert content["pagination"] == {
            "offset": 0,
            "limit": 1,
            "total": 2,
            "returned": 1,
            "has_more": True,
        }
        if field == "ownersPoints":
            assert content["data"]["historySummary"] == payload["historySummary"]
            assert "numberOfOwners" not in content["data"]
        result = await client.call_tool(
            name, {"order_book_id": "5269", "offset": 5, "limit": 1}
        )
        assert result.structured_content["pagination"]["returned"] == 0


async def test_selected_analysis_schema_and_missing_metric(upstream):
    point = {"reportType": "FULL_YEAR", "financialYear": 2016, "value": 0}
    upstream.get.return_value = {
        "stockKeyRatiosByYear": {"priceEarningsRatio": [point], "priceSalesRatio": []},
        "dividendsByYear": "unrelated bad section",
    }
    async with Client(mcp) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}
        assert "metric" in tools["get_stock_analysis"].inputSchema["required"]
        result = await client.call_tool(
            "get_stock_analysis",
            {"order_book_id": "5269", "metric": "priceEarningsRatio"},
        )
        validate(result.structured_content, tools["get_stock_analysis"].outputSchema)
        assert (
            result.structured_content["data"]["stockKeyRatiosByYear"][
                "priceEarningsRatio"
            ][0]["value"]
            == 0
        )
        assert result.structured_content["available_metrics"] == [
            "priceEarningsRatio",
            "priceSalesRatio",
        ]
        result = await client.call_tool(
            "get_stock_analysis", {"order_book_id": "5269", "metric": "missing"}
        )
        assert result.structured_content["data"] == {"stockKeyRatiosByYear": {}}
        assert result.structured_content["pagination"]["total"] is None


async def test_marketmaker_metadata_cannot_collide(upstream):
    point = {
        "timestamp": 0,
        "open": 0,
        "close": 0,
        "high": 0,
        "low": 0,
        "totalVolumeTraded": 0,
    }
    upstream.get.return_value = {
        "ohlc": [point, point],
        "marketMaker": [{"raw": 1}, {"raw": 2}],
        "metadata": {
            "resolution": {"chartResolution": "DAY", "availableResolutions": ["DAY"]}
        },
        "pagination": {"upstream": True},
        "marketMakerPagination": {"upstream": True},
    }
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_marketmaker_chart", {"order_book_id": "5269", "offset": 1, "limit": 1}
        )
        content = result.structured_content
        assert content["data"]["pagination"] == {"upstream": True}
        assert content["data"]["marketMakerPagination"] == {"upstream": True}
        assert content["data"]["ohlc"] == [point]
        assert content["data"]["marketMaker"] == [{"raw": 2}]
        assert (
            content["pagination"]["total"]
            == content["marketMakerPagination"]["total"]
            == 2
        )
        assert (
            content["pagination"]["returned"]
            == content["marketMakerPagination"]["returned"]
            == 1
        )
