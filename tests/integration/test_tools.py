"""Live MCP boundary checks. Collecting this module makes no API calls."""

import json
import re

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from avanza_mcp import mcp
from avanza_mcp.models.contracts import (
    AnalysisPage,
    BrokerSummaries,
    FundChartPage,
    FundHoldings,
    FundPeriods,
    MarketmakerChartPage,
    OwnersPage,
    ShortSellingPage,
    StockChartPage,
    TradesPage,
)
from avanza_mcp.models.fund import FundDescription, FundInfo, FundSustainability
from avanza_mcp.models.search import InstrumentHit, InstrumentSearch
from avanza_mcp.models.stock import MarketplaceInfo, OrderDepth, Quote, StockInfo

pytestmark = pytest.mark.integration

STOCK_ID = "5269"
GLOBAL_FUND_ID = "878733"


@pytest.fixture
async def mcp_client():
    async with Client(mcp) as client:
        yield client


@pytest.mark.parametrize(
    "tool, arguments, model",
    [
        ("search_instruments", {"query": "Volvo", "limit": 5}, InstrumentSearch),
        (
            "search_instruments",
            {"query": "Global", "instrument_type": "fund", "limit": 3},
            InstrumentSearch,
        ),
        ("get_stock_info", {"order_book_id": STOCK_ID}, StockInfo),
        ("get_stock_quote", {"order_book_id": STOCK_ID}, Quote),
        (
            "get_stock_chart",
            {
                "order_book_id": STOCK_ID,
                "time_period": "one_month",
                "offset": 1,
                "limit": 3,
            },
            StockChartPage,
        ),
        (
            "get_stock_analysis",
            {
                "order_book_id": STOCK_ID,
                "selection": "stockKeyRatiosByQuarter",
                "metric": "priceEarningsRatio",
                "offset": 1,
                "limit": 3,
            },
            AnalysisPage,
        ),
        ("get_orderbook", {"order_book_id": STOCK_ID}, OrderDepth),
        (
            "get_recent_trades",
            {"order_book_id": STOCK_ID, "offset": 1, "limit": 3},
            TradesPage,
        ),
        ("get_broker_trade_summary", {"order_book_id": STOCK_ID}, BrokerSummaries),
        ("get_marketplace_info", {"order_book_id": STOCK_ID}, MarketplaceInfo),
        (
            "get_dividends",
            {
                "order_book_id": STOCK_ID,
                "metric": "dividendPerShare",
                "offset": 1,
                "limit": 3,
            },
            AnalysisPage,
        ),
        (
            "get_company_financials",
            {
                "order_book_id": STOCK_ID,
                "selection": "companyFinancialsByQuarter",
                "metric": "sales",
                "offset": 1,
                "limit": 3,
            },
            AnalysisPage,
        ),
        ("get_fund_info", {"order_book_id": GLOBAL_FUND_ID}, FundInfo),
        (
            "get_fund_sustainability",
            {"order_book_id": GLOBAL_FUND_ID},
            FundSustainability,
        ),
        (
            "get_fund_chart",
            {
                "order_book_id": GLOBAL_FUND_ID,
                "time_period": "one_year",
                "offset": 1,
                "limit": 3,
            },
            FundChartPage,
        ),
        ("get_fund_chart_periods", {"order_book_id": GLOBAL_FUND_ID}, FundPeriods),
        ("get_fund_description", {"order_book_id": GLOBAL_FUND_ID}, FundDescription),
        ("get_fund_holdings", {"order_book_id": GLOBAL_FUND_ID}, FundHoldings),
        (
            "get_marketmaker_chart",
            {"order_book_id": "5649", "time_period": "today", "offset": 1, "limit": 3},
            MarketmakerChartPage,
        ),
        (
            "get_number_of_owners",
            {"order_book_id": "1154359", "offset": 1, "limit": 3},
            OwnersPage,
        ),
        (
            "get_short_selling",
            {"order_book_id": "5247", "offset": 1, "limit": 3},
            ShortSellingPage,
        ),
    ],
    ids=lambda value: value if isinstance(value, str) else None,
)
async def test_tool_success(mcp_client, tool, arguments, model):
    result = await mcp_client.call_tool(tool, arguments)
    assert not result.is_error
    content = result.structured_content
    assert isinstance(content, dict)
    # Validate JSON types without coercing strings into numeric quote/chart fields.
    data = model.model_validate_json(json.dumps(content), strict=True)

    if isinstance(data, InstrumentSearch):
        assert data.searchQuery == arguments["query"]
        assert data.returned == len(data.hits) <= arguments["limit"]
        assert data.totalNumberOfHits >= data.returned
        assert data.totalNumberOfHits <= data.candidatesExamined <= 50
        for hit in content["hits"]:
            assert hit.keys() <= InstrumentHit.model_fields.keys()
            if arguments.get("instrument_type") == "fund":
                assert hit["type"].lower() == "fund"
    elif isinstance(data, StockInfo):
        assert data.orderbookId == arguments["order_book_id"]
    elif isinstance(data, FundInfo) and data.id is not None:
        assert data.id == arguments["order_book_id"]

    if isinstance(data, AnalysisPage):
        selection = arguments.get("selection", "dividendsByYear")
        metric = arguments["metric"]
        assert data.selection == selection
        assert data.metric == metric
        assert data.data.keys() <= {selection}
        section = data.data.get(selection)
        if section is not None:
            assert section.keys() <= {metric}
            assert (metric in section) == (metric in data.available_metrics)
        else:
            assert data.available_metrics == []
        records = section.get(metric) if section is not None else None
        assert_page(data.pagination, records, arguments)
    elif isinstance(data, (StockChartPage, MarketmakerChartPage)):
        assert_page(data.pagination, data.data.ohlc, arguments)
        if isinstance(data, MarketmakerChartPage):
            if data.data.marketMaker is None:
                assert data.marketMakerPagination is None
            else:
                assert data.marketMakerPagination is not None
                assert_page(
                    data.marketMakerPagination, data.data.marketMaker, arguments
                )
    elif isinstance(data, FundChartPage):
        assert data.data.id == arguments["order_book_id"]
        assert_page(data.pagination, data.data.dataSerie, arguments)
    elif isinstance(data, TradesPage):
        assert_page(data.pagination, data.trades, arguments)
    elif isinstance(data, OwnersPage):
        assert_page(data.pagination, data.data.ownersPoints, arguments)
    elif isinstance(data, ShortSellingPage):
        assert_page(data.pagination, data.data.shortSellingHistory, arguments)


async def test_exact_order_book_lookup(mcp_client):
    # Search is not an authoritative ID registry, even for a known stock.
    try:
        result = await mcp_client.call_tool(
            "get_instrument_by_order_book_id", {"order_book_id": STOCK_ID}
        )
    except ToolError as exc:
        assert re.fullmatch(
            r"No exact order_book_id match among (?:[0-9]|[1-4][0-9]|50) search candidates "
            r"\(maximum 50\)\. Search is not authoritative; this does not prove the ID is invalid\. "
            r"Search by name or ISIN and confirm the returned order_book_id, type and exchange\.",
            str(exc),
        ), str(exc)
    else:
        assert not result.is_error
        content = result.structured_content
        assert isinstance(content, dict)
        hit = InstrumentHit.model_validate(content, strict=True)
        assert hit.order_book_id == STOCK_ID
        assert content.keys() <= InstrumentHit.model_fields.keys()


def assert_page(page, records, arguments):
    """Check one snapshot, without assuming activity or stability across requests."""
    assert page.offset == arguments["offset"]
    assert page.limit == arguments["limit"]
    if records is None:
        assert page.total is None
        assert page.returned == 0
        assert page.has_more is False
    else:
        assert page.total is not None and page.total >= 0
        assert (
            page.returned
            == len(records)
            == min(page.limit, max(0, page.total - page.offset))
        )
        assert page.has_more == (page.offset + page.limit < page.total)


@pytest.mark.parametrize(
    "tool, message",
    [
        ("get_stock_info", "Avanza did not find the requested data"),
        # The fund-guide endpoint returns 500 for this ID, not a not-found response.
        ("get_fund_info", "Avanza is temporarily unavailable"),
    ],
)
async def test_invalid_order_book_id(mcp_client, tool, message):
    """A syntactically valid but nonexistent ID reaches upstream error handling."""
    with pytest.raises(ToolError, match=message):
        await mcp_client.call_tool(tool, {"order_book_id": "999999999"})
