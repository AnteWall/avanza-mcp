"""Integration tests for MCP tools against real Avanza API.

These tests make real API calls and should be run sparingly to avoid rate limits.
Use: pytest tests/integration -v --tb=short
"""

import pytest
from fastmcp import Client
from avanza_mcp import mcp


# Well-known instrument IDs for testing
VOLVO_B_ID = "5479"  # Volvo B stock (Note: may be Telia now due to ID changes)
SEB_A_ID = "5269"  # SEB A stock (Note: may be Volvo B now)
GLOBAL_FUND_ID = "878733"  # Avanza Global fund


@pytest.fixture
async def mcp_client():
    """Create MCP client for testing."""
    async with Client(mcp) as client:
        yield client


def get_tool_result_text(result) -> str:
    """Extract text from MCP tool result."""
    # CallToolResult has content attribute with list of content items
    if hasattr(result, "content") and result.content:
        for content_item in result.content:
            if hasattr(content_item, "text"):
                return content_item.text
    return ""


@pytest.mark.parametrize(
    "tool, arguments, expected",
    [
        pytest.param(
            "search_instruments",
            {"query": "Volvo", "limit": 5},
            lambda text: "totalNumberOfHits" in text and "hits" in text,
            id="search_instruments",
        ),
        pytest.param(
            "search_instruments",
            {"query": "Global", "instrument_type": "fund", "limit": 3},
            lambda text: "hits" in text,
            id="search_instruments_with_type_filter",
        ),
        pytest.param(
            "get_instrument_by_order_book_id",
            {"order_book_id": SEB_A_ID},
            None,
            id="get_instrument_by_order_book_id",
        ),
        pytest.param(
            "get_stock_info",
            {"instrument_id": SEB_A_ID},
            lambda text: "orderbookId" in text and "name" in text and "quote" in text,
            id="get_stock_info",
        ),
        pytest.param(
            "get_stock_quote",
            {"instrument_id": SEB_A_ID},
            lambda text: "last" in text or "buy" in text,
            id="get_stock_quote",
        ),
        pytest.param(
            "get_stock_chart",
            {"instrument_id": SEB_A_ID, "time_period": "one_month"},
            lambda text: "ohlc" in text,
            id="get_stock_chart",
        ),
        pytest.param(
            "get_stock_analysis",
            {"instrument_id": SEB_A_ID},
            lambda text: "KeyRatios" in text or "keyRatios" in text.lower(),
            id="get_stock_analysis",
        ),
        pytest.param(
            "get_orderbook",
            {"instrument_id": SEB_A_ID},
            lambda text: "levels" in text,
            id="get_orderbook",
        ),
        pytest.param(
            "get_recent_trades",
            {"instrument_id": SEB_A_ID},
            lambda text: "trades" in text,
            id="get_recent_trades",
        ),
        pytest.param(
            "get_broker_trade_summary",
            {"instrument_id": SEB_A_ID},
            lambda text: "summaries" in text,
            id="get_broker_trade_summary",
        ),
        pytest.param(
            "get_marketplace_info",
            {"instrument_id": SEB_A_ID},
            lambda text: "marketOpen" in text,
            id="get_marketplace_info",
        ),
        pytest.param(
            "get_dividends",
            {"instrument_id": SEB_A_ID},
            lambda text: "dividendsByYear" in text,
            id="get_dividends",
        ),
        pytest.param(
            "get_company_financials",
            {"instrument_id": SEB_A_ID},
            lambda text: "companyFinancials" in text,
            id="get_company_financials",
        ),
        pytest.param(
            "get_fund_info",
            {"instrument_id": GLOBAL_FUND_ID},
            lambda text: "name" in text and "nav" in text,
            id="get_fund_info",
        ),
        pytest.param(
            "get_fund_sustainability",
            {"instrument_id": GLOBAL_FUND_ID},
            lambda text: "esgScore" in text or "sustainabilityRating" in text,
            id="get_fund_sustainability",
        ),
        pytest.param(
            "get_fund_chart",
            {"instrument_id": GLOBAL_FUND_ID, "time_period": "one_year"},
            lambda text: "dataSerie" in text,
            id="get_fund_chart",
        ),
        pytest.param(
            "get_fund_chart_periods",
            {"instrument_id": GLOBAL_FUND_ID},
            lambda text: "periods" in text,
            id="get_fund_chart_periods",
        ),
        pytest.param(
            "get_fund_description",
            {"instrument_id": GLOBAL_FUND_ID},
            lambda text: "response" in text or "heading" in text,
            id="get_fund_description",
        ),
        pytest.param(
            "get_fund_holdings",
            {"instrument_id": GLOBAL_FUND_ID},
            lambda text: "countryChartData" in text or "sectorChartData" in text,
            id="get_fund_holdings",
        ),
    ],
)
async def test_tool_success(mcp_client, tool, arguments, expected):
    """Each tool keeps its original arguments and AND/OR expectations."""
    result = await mcp_client.call_tool(tool, arguments)
    assert not result.is_error
    if expected is not None:
        text = get_tool_result_text(result)
        assert expected(text), text


class TestErrorHandling:
    """Integration tests for error handling."""

    async def test_invalid_stock_id(self, mcp_client):
        """Test that invalid stock ID raises appropriate error."""
        from fastmcp.exceptions import ToolError

        with pytest.raises(ToolError) as exc_info:
            await mcp_client.call_tool(
                "get_stock_info", {"instrument_id": "invalid_id_12345"}
            )
        # Error should mention the API error
        assert "error" in str(exc_info.value).lower() or "400" in str(exc_info.value)

    async def test_invalid_fund_id(self, mcp_client):
        """Test that invalid fund ID raises appropriate error."""
        from fastmcp.exceptions import ToolError

        with pytest.raises(ToolError) as exc_info:
            await mcp_client.call_tool(
                "get_fund_info", {"instrument_id": "invalid_id_12345"}
            )
        # Error should mention the API error
        assert "error" in str(exc_info.value).lower() or "400" in str(exc_info.value)
