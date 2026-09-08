"""Checks for shared tool error handling and holdings serialization."""

from unittest.mock import AsyncMock, Mock

import pytest

from avanza_mcp.models.fund import FundInfo
from avanza_mcp.tools import funds
from avanza_mcp.tools._logging import log_errors


async def test_log_errors_preserves_exception():
    ctx = Mock(error=AsyncMock())
    async with log_errors(ctx, "Fetch failed"):
        pass
    ctx.error.assert_not_awaited()

    error = ValueError("invalid response")
    with pytest.raises(ValueError) as caught:
        async with log_errors(ctx, "Fetch failed"):
            raise error
    assert caught.value is error
    ctx.error.assert_awaited_once_with("Fetch failed: invalid response")


@pytest.mark.parametrize("portfolio_date", [None, "2026-09-08"])
async def test_fund_holdings_serialization(monkeypatch, portfolio_date):
    fund = FundInfo.model_validate({
        "name": "Test fund",
        "countryChartData": [{"name": "Sweden", "y": 50, "extra": 1, "empty": None}],
        "holdingChartData": [{"name": None, "y": 10}],
        "portfolioDate": portfolio_date,
        "unrelated": "not holdings",
    })
    client = AsyncMock()
    monkeypatch.setattr(funds, "AvanzaClient", Mock(return_value=client))
    service = Mock(get_fund_info=AsyncMock(return_value=fund))
    monkeypatch.setattr(funds, "MarketDataService", Mock(return_value=service))
    ctx = Mock(error=AsyncMock())

    result = await funds.get_fund_holdings(ctx, "123")

    assert result == {
        "countryChartData": [{"name": "Sweden", "y": 50.0, "extra": 1}],
        "sectorChartData": [],
        "holdingChartData": [{"y": 10.0}],
        "portfolioDate": portfolio_date,
    }
    service.get_fund_info.assert_awaited_once_with("123")
    client.__aexit__.assert_awaited_once()
    ctx.error.assert_not_awaited()
