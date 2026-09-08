"""Direct callers receive the same request and upstream envelope validation."""

from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from avanza_mcp.models.certificate import CertificateFilterRequest
from avanza_mcp.models.etf import ETFFilterRequest
from avanza_mcp.models.future_forward import FutureForwardMatrixRequest
from avanza_mcp.models.warrant import WarrantFilterRequest
from avanza_mcp.services import MarketDataService, SearchService


@pytest.mark.parametrize(
    "model",
    [
        CertificateFilterRequest,
        ETFFilterRequest,
        WarrantFilterRequest,
        FutureForwardMatrixRequest,
    ],
)
@pytest.mark.parametrize("pagination", [{"offset": -1}, {"limit": 0}, {"limit": 101}])
def test_request_bounds(model, pagination):
    with pytest.raises(ValidationError):
        model(filter={}, sortBy={"field": "name", "order": "asc"}, **pagination)


async def test_futures_dates_json_mode():
    request = FutureForwardMatrixRequest(
        filter={"endDates": ["2026-09-18"]},
        sortBy={"field": "strikePrice", "order": "asc"},
    )
    assert request.filter.endDates == ["2026-09-18"]
    upstream = AsyncMock()
    upstream.post.return_value = {}
    await MarketDataService(upstream).list_futures_forwards(request)
    assert upstream.post.call_args.kwargs["json"]["filter"]["endDates"] == [
        "2026-09-18"
    ]
    with pytest.raises(ValidationError):
        FutureForwardMatrixRequest(
            filter={"endDates": ["2026-02-30"]},
            sortBy={"field": "name", "order": "asc"},
        )


@pytest.mark.parametrize(
    "method,payload",
    [
        ("get_trades", {}),
        ("get_trades", [None]),
        ("get_broker_trades", {}),
        ("get_fund_chart_periods", {}),
        ("get_stock_analysis", []),
        ("get_dividends", {"dividendsByYear": []}),
        ("get_company_financials", {"companyFinancialsByYear": {"sales": [None]}}),
        ("get_stock_quote", {}),
        ("get_stock_quote", {"error": "invalid"}),
        ("get_number_of_owners", {}),
        ("get_number_of_owners", {"orderbookId": "123"}),
        ("get_number_of_owners", {"ownersPoints": None}),
        ("get_number_of_owners", {"ownersPoints": [{"timestamp": 0}]}),
        ("get_short_selling", {}),
        ("get_short_selling", {"shortSellingHistory": {}}),
        ("get_short_selling", {"shortSellingHistory": [{"timestamp": 0}]}),
        ("get_etf_details", []),
        ("get_order_depth", []),
    ],
)
async def test_invalid_service_envelopes(method, payload):
    upstream = AsyncMock()
    upstream.get.return_value = payload
    with pytest.raises((ValidationError, ValueError)):
        await getattr(MarketDataService(upstream), method)("123")


async def test_empty_optional_data_zero_and_missing_sections():
    upstream = AsyncMock()
    service = MarketDataService(upstream)
    upstream.get.return_value = []
    assert await service.get_trades("123") == []
    upstream.get.return_value = {}
    assert (await service.get_order_depth("123")).levels == []
    assert await service.get_dividends("123") == {}
    assert await service.get_company_financials("123") == {}
    upstream.get.return_value = {
        "dividendsByYear": {"dividendPerShare": []},
        "companyFinancialsByYear": None,
    }
    assert await service.get_dividends("123") == {
        "dividendsByYear": {"dividendPerShare": []}
    }
    assert await service.get_company_financials("123") == {
        "companyFinancialsByYear": None
    }
    upstream.get.return_value = {"last": 0, "buy": None}
    quote = await service.get_stock_quote("123")
    assert quote.last == 0 and quote.buy is None
    upstream.get.return_value = {
        "ownersPoints": [{"timestamp": 0, "numberOfOwners": 0}],
        "historySummary": {"oneYearChange": 0},
    }
    owners = await service.get_number_of_owners("123")
    assert owners.ownersPoints[0].numberOfOwners == 0
    assert owners.historySummary.oneYearChange == 0
    upstream.get.return_value = {"ownersPoints": []}
    assert (await service.get_number_of_owners("123")).ownersPoints == []
    upstream.get.return_value = {"shortSellingHistory": [{"timestamp": 0, "ratio": 0}]}
    assert (await service.get_short_selling("123")).shortSellingHistory[0].ratio == 0
    upstream.get.return_value = {"shortSellingHistory": []}
    assert (await service.get_short_selling("123")).shortSellingHistory == []


async def test_analysis_subsets_share_service_method():
    service = MarketDataService(AsyncMock())
    payload = {
        "dividendsByYear": {
            "dividendPerShare": [
                {"reportType": "FULL_YEAR", "financialYear": 2025, "value": 0}
            ]
        }
    }
    service.get_stock_analysis = AsyncMock(return_value=payload)
    assert await service.get_dividends("123") == payload
    service.get_stock_analysis.assert_awaited_once_with("123", "dividendsByYear")


async def test_analysis_validates_only_selected_section():
    upstream = AsyncMock()
    upstream.get.return_value = {
        "stockKeyRatiosByYear": {
            "priceEarningsRatio": [
                {"reportType": "FULL_YEAR", "financialYear": 2025, "value": 0}
            ]
        },
        "dividendsByYear": ["unrelated malformed section"],
        "keyRatiosByYear": {"priceEarningsRatio": {"latest": 0, "average": 0}},
    }
    service = MarketDataService(upstream)
    assert (
        await service.get_stock_analysis("123", "stockKeyRatiosByYear")
        == upstream.get.return_value
    )
    assert await service.get_stock_analysis("123") == upstream.get.return_value
    with pytest.raises(ValidationError):
        await service.get_dividends("123")


@pytest.mark.parametrize(
    "method", ["get_chart_data", "get_fund_chart", "get_marketmaker_chart"]
)
async def test_direct_chart_period_validation(method):
    upstream = AsyncMock()
    with pytest.raises(ValidationError):
        await getattr(MarketDataService(upstream), method)("123", "invented_period")
    upstream.get.assert_not_awaited()


async def test_direct_search_bounds():
    upstream = AsyncMock()
    for kwargs in (
        {"query": " "},
        {"query": "x", "limit": 0},
        {"query": "x", "limit": 51},
    ):
        with pytest.raises(ValidationError):
            await SearchService(upstream).search(**kwargs)
    upstream.post.assert_not_awaited()
