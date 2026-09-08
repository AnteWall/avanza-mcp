"""Offline MCP-boundary checks for research prompts and static guidance."""

import json
import re

import pytest
from fastmcp import Client
from mcp.shared.exceptions import McpError

from avanza_mcp import mcp
from avanza_mcp.resources.usage import QUICK_START, USAGE_GUIDE


@pytest.mark.parametrize(
    "name, arguments, expected",
    [
        ("analyze_stock", {"stock_symbol": "Volvo B"}, "Volvo B"),
        ("compare_funds", {"fund_names": json.dumps(["Fund, A", "Fund B"])}, "Fund, A"),
        ("compare_funds", {"fund_names": ["Fund A", "Fund B"]}, "Fund A"),
        (
            "screen_dividend_stocks",
            {"candidates": '["Volvo B"]', "min_yield": "0"},
            "0.0%",
        ),
    ],
)
async def test_rendered_research_prompts(name, arguments, expected):
    async with Client(mcp) as client:
        result = await client.get_prompt(name, arguments)
        text = result.messages[0].content.text
        assert expected in text
        assert "order_book_id" in text
        assert "instrument_id" not in text
        assert "get_news" not in text
        for phrase in (
            "source dates",
            "retrieval",
            "currencies",
            "zero",
            "missing",
            "data, not instructions",
        ):
            assert phrase in text
        referenced = set(re.findall(r"`((?:get_|search_|filter_|list_)\w+)`", text))
        assert referenced
        assert referenced <= {tool.name for tool in await client.list_tools()}
        if name == "analyze_stock":
            assert "not news coverage" in text
            assert "not guaranteed" in text
            assert "Microstructure data is not required" in text
            assert 'metric="priceEarningsRatio"' in text
            assert "data[selection][metric]" in text
            assert "available_metrics" in text
            assert "data.ohlc" in text
        elif name == "compare_funds":
            assert "avoid redundant subset calls" in text
            assert "risk-adjusted returns without" in text
            for phrase in (
                "developmentOneYear",
                "productFee/managementFee",
                "different scales",
                "data.dataSerie",
                "pagination",
            ):
                assert phrase in text
        else:
            assert "not an exhaustive universe screen" in text
            assert "excluded and unresolved" in text
            assert 'metric="dividendPerShare"' in text
            assert "available_metrics" in text
            assert "data[selection][metric]" in text


@pytest.mark.parametrize(
    "name, arguments",
    [
        ("analyze_stock", {"stock_symbol": "  "}),
        ("compare_funds", {"fund_names": "Fund A, Fund B"}),
        ("compare_funds", {"fund_names": "[]"}),
        ("compare_funds", {"fund_names": '["Fund A"]'}),
        ("compare_funds", {"fund_names": '["Fund A", "  "]'}),
        ("compare_funds", {"fund_names": '["Fund A", 2]'}),
        ("screen_dividend_stocks", {}),
        ("screen_dividend_stocks", {"candidates": "[]"}),
        ("screen_dividend_stocks", {"candidates": '[" "]'}),
        ("screen_dividend_stocks", {"candidates": '["Volvo"]', "min_yield": "-1"}),
        ("screen_dividend_stocks", {"candidates": '["Volvo"]', "min_yield": "NaN"}),
        (
            "screen_dividend_stocks",
            {"candidates": '["Volvo"]', "min_yield": "Infinity"},
        ),
    ],
)
async def test_prompt_validation(name, arguments):
    async with Client(mcp) as client:
        with pytest.raises(McpError):
            await client.get_prompt(name, arguments)


async def test_mcp_guidance_registration():
    async with Client(mcp) as client:
        tools = await client.list_tools()
        tool_names = {tool.name for tool in tools}
        assert len(tool_names) == 34
        prompts = await client.list_prompts()
        assert {prompt.name for prompt in prompts} == {
            "analyze_stock",
            "compare_funds",
            "screen_dividend_stocks",
        }
        for name, argument in (
            ("compare_funds", "fund_names"),
            ("screen_dividend_stocks", "candidates"),
        ):
            prompt = next(prompt for prompt in prompts if prompt.name == name)
            arg = next(arg for arg in prompt.arguments if arg.name == argument)
            assert arg.required
            assert "JSON" in arg.description
            assert "array" in arg.description

        resources = await client.list_resources()
        assert {str(resource.uri) for resource in resources} == {
            "avanza://docs/usage",
            "avanza://docs/quick-start",
        }
        for resource in resources:
            assert resource.mimeType == "text/markdown"
        for uri, expected in (
            ("avanza://docs/usage", USAGE_GUIDE),
            ("avanza://docs/quick-start", QUICK_START),
        ):
            contents = await client.read_resource(uri)
            assert contents[0].mimeType == "text/markdown"
            assert contents[0].text == expected
            referenced = set(
                re.findall(r"`((?:get_|search_|filter_|list_)\w+)`", expected)
            )
            assert referenced <= tool_names
            assert "```python" not in expected
            assert "instrument_id" not in expected
            for phrase in (
                "call count",
                "item count",
                "source dates",
                "zero",
                "unknown",
                "dynamic",
                "retrieval date",
            ):
                assert phrase in expected
            for phrase in (
                "priceEarningsRatio",
                "available_metrics",
                "upstream traffic",
                "data cache",
                "explicit null",
            ):
                assert phrase in expected
        for phrase in (
            "candidatesExamined",
            "upstreamTotalNumberOfHits",
            "limit=100",
            "limit=20",
            "data.ownersPoints",
            "data.shortSellingHistory",
            "data.dataSerie",
            "marketMakerPagination",
            "prompt-to-tool",
        ):
            assert phrase in USAGE_GUIDE
        templates = await client.list_resource_templates()
        assert len(templates) == 2
        assert {template.uriTemplate for template in templates} == {
            "avanza://stock/{order_book_id}",
            "avanza://fund/{order_book_id}",
        }
        assert all(template.mimeType == "text/markdown" for template in templates)


async def test_documented_history_defaults_and_metric_contracts():
    async with Client(mcp) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}
    for name in (
        "get_stock_chart",
        "get_fund_chart",
        "get_marketmaker_chart",
        "get_stock_analysis",
        "get_dividends",
        "get_company_financials",
        "get_recent_trades",
        "get_number_of_owners",
        "get_short_selling",
    ):
        tool = tools[name]
        properties = tool.inputSchema["properties"]
        assert properties["offset"]["default"] == 0
        assert properties["offset"]["minimum"] == 0
        assert properties["limit"]["default"] == (100 if name.endswith("chart") else 20)
        assert properties["limit"]["minimum"] == 1
        assert properties["limit"]["maximum"] == 100
        assert "order_book_id" in tool.inputSchema["required"]
        assert "instrument_id" not in properties
        output = tool.outputSchema["properties"]
        assert "pagination" in output
        assert ("trades" if name == "get_recent_trades" else "data") in output
    for name, section in (
        ("get_stock_analysis", "stockKeyRatiosByYear"),
        ("get_company_financials", "companyFinancialsByYear"),
        ("get_dividends", None),
    ):
        tool = tools[name]
        assert "metric" in tool.inputSchema["required"]
        assert set(tool.outputSchema["properties"]) == {
            "selection",
            "metric",
            "available_metrics",
            "data",
            "pagination",
        }
        if section is None:
            assert "selection" not in tool.inputSchema["properties"]
        else:
            assert tool.inputSchema["properties"]["selection"]["default"] == section
    for name, period in (
        ("get_stock_chart", "one_year"),
        ("get_fund_chart", "three_years"),
        ("get_marketmaker_chart", "today"),
    ):
        assert tools[name].inputSchema["properties"]["time_period"]["default"] == period
