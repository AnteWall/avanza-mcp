"""Checks for safe errors, shared client lookup and holdings serialization."""

from unittest.mock import AsyncMock, Mock

import pytest
from fastmcp.exceptions import ToolError

from avanza_mcp.client.exceptions import (
    AvanzaError,
    AvanzaNotFoundError,
    AvanzaAuthError,
    AvanzaRateLimitError,
    AvanzaNetworkError,
    AvanzaTimeoutError,
    AvanzaAPIError,
)
from avanza_mcp.models.fund import FundInfo
from avanza_mcp.tools import funds
from avanza_mcp.tools._helpers import analysis_page, api_errors, page_metadata


def test_api_errors_preserves_unexpected_errors_and_sanitizes_expected_errors():
    error = ValueError("invalid response")
    with pytest.raises(ValueError) as caught:
        with api_errors():
            raise error
    assert caught.value is error
    expected = AvanzaError("private upstream payload")
    with pytest.raises(ToolError) as caught:
        with api_errors():
            raise expected
    assert caught.value.__cause__ is expected
    assert "private" not in str(caught.value)


def test_pagination_preserves_raw_order_and_missing_sections():
    points = [
        {"financialYear": year, "reportType": "FULL_YEAR", "value": 0}
        for year in (2025, 2023, 2024)
    ]
    source = {"dividendsByYear": {"dividendPerShare": points, "directYieldRatio": []}}
    result = analysis_page(source, "dividendsByYear", "dividendPerShare", 1, 1)
    assert result.data["dividendsByYear"]["dividendPerShare"][0].financialYear == 2023
    assert result.available_metrics == ["dividendPerShare", "directYieldRatio"]
    assert result.pagination.model_dump() == {
        "offset": 1,
        "limit": 1,
        "total": 3,
        "returned": 1,
        "has_more": True,
    }
    assert points[0]["value"] == 0
    assert page_metadata(3, 10, 1).returned == 0
    assert not page_metadata(3, 10, 1).has_more
    assert analysis_page({}, "dividendsByYear", "dividendPerShare", 0, 1).data == {}
    assert (
        analysis_page({}, "dividendsByYear", "dividendPerShare", 0, 1).pagination.total
        is None
    )
    assert (
        analysis_page(
            source, "dividendsByYear", "directYieldRatio", 0, 1
        ).pagination.total
        == 0
    )
    assert analysis_page(source, "dividendsByYear", "unknownMetric", 0, 1).data == {
        "dividendsByYear": {}
    }
    assert analysis_page(
        {"dividendsByYear": None}, "dividendsByYear", "dividendPerShare", 0, 1
    ).data == {"dividendsByYear": None}


@pytest.mark.parametrize(
    "error,expected",
    [
        (AvanzaNotFoundError("secret"), "did not find"),
        (AvanzaAuthError("secret"), "denied access"),
        (AvanzaRateLimitError(0, "secret"), "Retry after 0 seconds"),
        (AvanzaRateLimitError(12, "secret"), "Retry after 12 seconds"),
        (AvanzaRateLimitError(-1, "secret"), "Retry later"),
        (AvanzaRateLimitError(True, "secret"), "Retry later"),
        (AvanzaRateLimitError("secret", "secret"), "Retry later"),
        (AvanzaNetworkError("secret"), "temporarily unavailable"),
        (AvanzaTimeoutError("secret"), "temporarily unavailable"),
        (AvanzaAPIError(503, "secret"), "temporarily unavailable"),
    ],
)
def test_safe_expected_error_messages(error, expected):
    with pytest.raises(ToolError) as caught:
        with api_errors():
            raise error
    assert expected in str(caught.value)
    assert "secret" not in str(caught.value)
    assert caught.value.__cause__ is error


@pytest.mark.parametrize("portfolio_date", [None, "2026-09-08"])
async def test_fund_holdings_serialization(monkeypatch, portfolio_date):
    fund = FundInfo.model_validate(
        {
            "name": "Test fund",
            "countryChartData": [{"name": "Sweden", "y": 0, "extra": 1, "empty": None}],
            "holdingChartData": [{"name": None, "y": 10}],
            "portfolioDate": portfolio_date,
            "unrelated": "not holdings",
        }
    )
    upstream = Mock()
    service = Mock(get_fund_info=AsyncMock(return_value=fund))
    factory = Mock(return_value=service)
    monkeypatch.setattr(funds, "MarketDataService", factory)
    ctx = Mock(lifespan_context={"client": upstream})
    result = await funds.get_fund_holdings(ctx, "123")
    assert result.model_dump(mode="json", by_alias=True) == {
        "countryChartData": [{"name": "Sweden", "y": 0.0, "extra": 1, "empty": None}],
        "sectorChartData": None,
        "holdingChartData": [{"name": None, "y": 10.0}],
        "portfolioDate": portfolio_date,
    }
    factory.assert_called_once_with(upstream)
    service.get_fund_info.assert_awaited_once_with("123")
    ctx.info.assert_not_called()
    ctx.error.assert_not_called()
