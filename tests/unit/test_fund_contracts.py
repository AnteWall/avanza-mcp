"""MCP contracts from the three raw fund 41567 endpoints checked 2026-09-08."""

from unittest.mock import AsyncMock

import pytest
from fastmcp import Client
from jsonschema import validate

from avanza_mcp import mcp
from avanza_mcp.client import AvanzaClient


# Reduced guide response, retaining upstream names/types. Zero allocation is an
# edge-case substitution; the source date and timestamp formats are unchanged.
FUND = {
    "name": "Avanza Zero",
    "isin": "SE0001718388",
    "nav": 569.9,
    "navDate": "2026-09-07T00:00:00",
    "currency": "SEK",
    "productFee": 0.0,
    "managementFee": 0.0,
    "developmentOneDay": 0.26037,
    "developmentOneMonth": -0.63465,
    "developmentThreeMonths": 6.28299,
    "developmentSixMonths": 11.07213,
    "developmentOneYear": 27.67149,
    "developmentThisYear": 15.81921,
    "developmentThreeYears": 63.764388,
    "developmentFiveYears": 60.336473,
    "adminCompany": {
        "name": "Avanza",
        "country": "Sverige",
        "url": "http://www.avanzafonder.se",
    },
    "categories": ["Sverige"],
    "riskText": "Medel",
    "prospectusLink": "/_api/fund-reference/reference/41567/prospectus",
    "startDate": "2006-05-22",
    "portfolioDate": "2026-08-31",
    "countryChartData": [
        {
            "name": "Sverige",
            "y": 0.0,
            "type": "",
            "currency": "",
            "countryCode": "SE",
            "isin": None,
            "orderbookId": None,
        }
    ],
    "sectorChartData": [],
    "holdingChartData": [
        {
            "name": "Investor B",
            "y": 0.0,
            "type": "HOLDING_TYPE_EQUITY",
            "currency": "SEK",
            "countryCode": "SE",
            "isin": "SE0015811963",
            "orderbookId": "5247",
        }
    ],
}


@pytest.fixture
def upstream(monkeypatch):
    client = AsyncMock()
    monkeypatch.setattr(AvanzaClient, "__aenter__", AsyncMock(return_value=client))
    monkeypatch.setattr(AvanzaClient, "__aexit__", AsyncMock(return_value=None))
    return client


async def test_fund_guide_structured_contract(upstream):
    upstream.get.return_value = FUND
    async with Client(mcp) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}
        result = await client.call_tool("get_fund_info", {"order_book_id": "41567"})
    content = result.structured_content
    schema = tools["get_fund_info"].outputSchema
    validate(content, schema)
    for field in (
        "productFee",
        "managementFee",
        *(key for key in FUND if key.startswith("development")),
    ):
        assert field in schema["properties"]
        assert content[field] == str(FUND[field])
        assert {item.get("type") for item in schema["properties"][field]["anyOf"]} == {
            "string",
            "null",
        }
    assert content["nav"] == "569.9"
    assert schema["properties"]["categories"]["anyOf"][0]["items"] == {"type": "string"}
    company = schema["properties"]["adminCompany"]["anyOf"][0]
    assert set(company["properties"]) == {"name", "country", "url"}
    for field in (
        "navDate",
        "startDate",
        "portfolioDate",
        "adminCompany",
        "categories",
        "prospectusLink",
        "riskText",
    ):
        assert content[field] == FUND[field]
    upstream.get.assert_awaited_once_with("/_api/fund-guide/guide/41567")


async def test_fund_holdings_preserves_date_and_zero(upstream):
    upstream.get.return_value = FUND
    async with Client(mcp) as client:
        result = await client.call_tool("get_fund_holdings", {"order_book_id": "41567"})
        content = result.structured_content
        assert content["portfolioDate"] == "2026-08-31"
        assert content["countryChartData"][0]["y"] == 0.0
        assert content["holdingChartData"][0]["y"] == 0.0
        assert content["holdingChartData"][0]["orderbookId"] == "5247"
        upstream.get.return_value = {"name": "Unknown", "navDate": "2026-09-07"}
        result = await client.call_tool("get_fund_info", {"order_book_id": "41567"})
        assert result.structured_content["navDate"] == "2026-09-07"
        assert result.structured_content.get("currency") is None
        result = await client.call_tool("get_fund_holdings", {"order_book_id": "41567"})
        assert result.structured_content.get("portfolioDate") is None


async def test_sustainability_goal_structured_contract(upstream):
    goal = {
        "value": "NO_POVERTY",
        "name": "Ingen fattigdom",
        "type": "SOCIAL",
        "status": "NOT_REPORTED",
    }
    upstream.get.return_value = {
        "sustainabilityDevelopmentGoals": [goal],
        "environmentalRating": 0,
        "lowCarbon": True,
        "svanen": False,
        "productInvolvements": [
            {
                "product": "tobacco",
                "productDescription": "Tobak",
                "value": 0.0,
                "name": "TOBACCO",
            }
        ],
    }
    async with Client(mcp) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}
        result = await client.call_tool(
            "get_fund_sustainability", {"order_book_id": "41567"}
        )
    content = result.structured_content
    schema = tools["get_fund_sustainability"].outputSchema
    validate(content, schema)
    assert content["sustainabilityDevelopmentGoals"] == [goal]
    assert set(
        schema["properties"]["sustainabilityDevelopmentGoals"]["items"]["properties"]
    ) == set(goal)
    assert content["environmentalRating"] == 0
    assert content["svanen"] is False
    assert content["productInvolvements"][0]["value"] == 0.0
    upstream.get.assert_awaited_once_with("/_api/fund-reference/sustainability/41567")


async def test_fund_period_source_date_and_unscaled_change(upstream):
    periods = [
        {
            "timePeriod": "one_month",
            "change": -0.006346500000000001,
            "startDate": "2026-08-08",
        }
    ]
    upstream.get.return_value = periods
    async with Client(mcp) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}
        result = await client.call_tool(
            "get_fund_chart_periods", {"order_book_id": "41567"}
        )
    validate(result.structured_content, tools["get_fund_chart_periods"].outputSchema)
    assert result.structured_content["periods"] == periods
    upstream.get.assert_awaited_once_with("/_api/fund-guide/chart/timeperiods/41567")
