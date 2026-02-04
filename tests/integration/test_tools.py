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


class TestSearchTools:
    """Integration tests for search tools."""

    @pytest.mark.asyncio
    async def test_search_instruments(self, mcp_client):
        """Test search_instruments returns results."""
        result = await mcp_client.call_tool(
            "search_instruments", {"query": "Volvo", "limit": 5}
        )
        assert not result.is_error
        text = get_tool_result_text(result)
        assert "totalNumberOfHits" in text
        assert "hits" in text

    @pytest.mark.asyncio
    async def test_search_instruments_with_type_filter(self, mcp_client):
        """Test search with instrument type filter."""
        result = await mcp_client.call_tool(
            "search_instruments",
            {"query": "Global", "instrument_type": "fund", "limit": 3},
        )
        assert not result.is_error
        text = get_tool_result_text(result)
        assert "hits" in text

    @pytest.mark.asyncio
    async def test_get_instrument_by_order_book_id(self, mcp_client):
        """Test lookup by order book ID."""
        result = await mcp_client.call_tool(
            "get_instrument_by_order_book_id", {"order_book_id": SEB_A_ID}
        )
        assert not result.is_error


class TestStockTools:
    """Integration tests for stock tools."""

    @pytest.mark.asyncio
    async def test_get_stock_info(self, mcp_client):
        """Test get_stock_info returns valid data."""
        result = await mcp_client.call_tool(
            "get_stock_info", {"instrument_id": SEB_A_ID}
        )
        assert not result.is_error
        text = get_tool_result_text(result)
        assert "orderbookId" in text
        assert "name" in text
        assert "quote" in text

    @pytest.mark.asyncio
    async def test_get_stock_quote(self, mcp_client):
        """Test get_stock_quote returns pricing data."""
        result = await mcp_client.call_tool(
            "get_stock_quote", {"instrument_id": SEB_A_ID}
        )
        assert not result.is_error
        text = get_tool_result_text(result)
        # Should have price data
        assert "last" in text or "buy" in text

    @pytest.mark.asyncio
    async def test_get_stock_chart(self, mcp_client):
        """Test get_stock_chart returns OHLC data."""
        result = await mcp_client.call_tool(
            "get_stock_chart",
            {"instrument_id": SEB_A_ID, "time_period": "one_month"},
        )
        assert not result.is_error
        text = get_tool_result_text(result)
        assert "ohlc" in text

    @pytest.mark.asyncio
    async def test_get_stock_analysis(self, mcp_client):
        """Test get_stock_analysis returns financial ratios."""
        result = await mcp_client.call_tool(
            "get_stock_analysis", {"instrument_id": SEB_A_ID}
        )
        assert not result.is_error
        text = get_tool_result_text(result)
        # Should have ratio data
        assert "KeyRatios" in text or "keyRatios" in text.lower()

    @pytest.mark.asyncio
    async def test_get_orderbook(self, mcp_client):
        """Test get_orderbook returns order depth."""
        result = await mcp_client.call_tool(
            "get_orderbook", {"instrument_id": SEB_A_ID}
        )
        assert not result.is_error
        text = get_tool_result_text(result)
        assert "levels" in text

    @pytest.mark.asyncio
    async def test_get_recent_trades(self, mcp_client):
        """Test get_recent_trades returns trade list."""
        result = await mcp_client.call_tool(
            "get_recent_trades", {"instrument_id": SEB_A_ID}
        )
        assert not result.is_error
        text = get_tool_result_text(result)
        assert "trades" in text

    @pytest.mark.asyncio
    async def test_get_broker_trade_summary(self, mcp_client):
        """Test get_broker_trade_summary returns broker data."""
        result = await mcp_client.call_tool(
            "get_broker_trade_summary", {"instrument_id": SEB_A_ID}
        )
        assert not result.is_error
        text = get_tool_result_text(result)
        assert "summaries" in text

    @pytest.mark.asyncio
    async def test_get_marketplace_info(self, mcp_client):
        """Test get_marketplace_info returns market status."""
        result = await mcp_client.call_tool(
            "get_marketplace_info", {"instrument_id": SEB_A_ID}
        )
        assert not result.is_error
        text = get_tool_result_text(result)
        assert "marketOpen" in text

    @pytest.mark.asyncio
    async def test_get_dividends(self, mcp_client):
        """Test get_dividends returns dividend history."""
        result = await mcp_client.call_tool(
            "get_dividends", {"instrument_id": SEB_A_ID}
        )
        assert not result.is_error
        text = get_tool_result_text(result)
        assert "dividendsByYear" in text

    @pytest.mark.asyncio
    async def test_get_company_financials(self, mcp_client):
        """Test get_company_financials returns financial data."""
        result = await mcp_client.call_tool(
            "get_company_financials", {"instrument_id": SEB_A_ID}
        )
        assert not result.is_error
        text = get_tool_result_text(result)
        assert "companyFinancials" in text


class TestFundTools:
    """Integration tests for fund tools."""

    @pytest.mark.asyncio
    async def test_get_fund_info(self, mcp_client):
        """Test get_fund_info returns fund details."""
        result = await mcp_client.call_tool(
            "get_fund_info", {"instrument_id": GLOBAL_FUND_ID}
        )
        assert not result.is_error
        text = get_tool_result_text(result)
        assert "name" in text
        assert "nav" in text

    @pytest.mark.asyncio
    async def test_get_fund_sustainability(self, mcp_client):
        """Test get_fund_sustainability returns ESG data."""
        result = await mcp_client.call_tool(
            "get_fund_sustainability", {"instrument_id": GLOBAL_FUND_ID}
        )
        assert not result.is_error
        text = get_tool_result_text(result)
        # Should have ESG metrics
        assert "esgScore" in text or "sustainabilityRating" in text

    @pytest.mark.asyncio
    async def test_get_fund_chart(self, mcp_client):
        """Test get_fund_chart returns performance data."""
        result = await mcp_client.call_tool(
            "get_fund_chart",
            {"instrument_id": GLOBAL_FUND_ID, "time_period": "one_year"},
        )
        assert not result.is_error
        text = get_tool_result_text(result)
        assert "dataSerie" in text

    @pytest.mark.asyncio
    async def test_get_fund_chart_periods(self, mcp_client):
        """Test get_fund_chart_periods returns available periods."""
        result = await mcp_client.call_tool(
            "get_fund_chart_periods", {"instrument_id": GLOBAL_FUND_ID}
        )
        assert not result.is_error
        text = get_tool_result_text(result)
        assert "periods" in text

    @pytest.mark.asyncio
    async def test_get_fund_description(self, mcp_client):
        """Test get_fund_description returns text description."""
        result = await mcp_client.call_tool(
            "get_fund_description", {"instrument_id": GLOBAL_FUND_ID}
        )
        assert not result.is_error
        text = get_tool_result_text(result)
        assert "response" in text or "heading" in text

    @pytest.mark.asyncio
    async def test_get_fund_holdings(self, mcp_client):
        """Test get_fund_holdings returns portfolio allocation."""
        result = await mcp_client.call_tool(
            "get_fund_holdings", {"instrument_id": GLOBAL_FUND_ID}
        )
        assert not result.is_error
        text = get_tool_result_text(result)
        assert "countryChartData" in text or "sectorChartData" in text


class TestErrorHandling:
    """Integration tests for error handling."""

    @pytest.mark.asyncio
    async def test_invalid_stock_id(self, mcp_client):
        """Test that invalid stock ID raises appropriate error."""
        from fastmcp.exceptions import ToolError

        with pytest.raises(ToolError) as exc_info:
            await mcp_client.call_tool(
                "get_stock_info", {"instrument_id": "invalid_id_12345"}
            )
        # Error should mention the API error
        assert "error" in str(exc_info.value).lower() or "400" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_invalid_fund_id(self, mcp_client):
        """Test that invalid fund ID raises appropriate error."""
        from fastmcp.exceptions import ToolError

        with pytest.raises(ToolError) as exc_info:
            await mcp_client.call_tool(
                "get_fund_info", {"instrument_id": "invalid_id_12345"}
            )
        # Error should mention the API error
        assert "error" in str(exc_info.value).lower() or "400" in str(exc_info.value)
