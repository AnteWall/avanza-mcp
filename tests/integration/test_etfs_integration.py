"""Integration tests for ETF endpoints.

These tests use real API calls and are marked with @pytest.mark.integration.
Run with: pytest tests/integration/test_etfs_integration.py -v -m integration
"""

import pytest
from avanza_mcp.client import AvanzaClient
from avanza_mcp.models.etf import ETFFilter, ETFFilterRequest
from avanza_mcp.models.filter import SortBy
from avanza_mcp.services import MarketDataService


@pytest.mark.integration
class TestETFEndpoints:
    """Test ETF endpoints with real API."""

    @pytest.mark.asyncio
    async def test_filter_etfs(self):
        """Test ETF filter endpoint."""
        async with AvanzaClient() as client:
            service = MarketDataService(client)
            request = ETFFilterRequest(
                filter=ETFFilter(),
                offset=0,
                limit=5,
                sortBy=SortBy(field="numberOfOwners", order="desc"),
            )
            result = await service.filter_etfs(request)

        assert hasattr(result, "etfs")
        assert isinstance(result.etfs, list)
        if len(result.etfs) > 0:
            etf = result.etfs[0]
            assert hasattr(etf, "orderbookId")
            assert hasattr(etf, "name")

    @pytest.mark.asyncio
    async def test_get_etf_info(self):
        """Test getting ETF info."""
        # Using ETF ID from new.md
        instrument_id = "742236"

        async with AvanzaClient() as client:
            service = MarketDataService(client)
            result = await service.get_etf_info(instrument_id)

        assert result.orderbookId == instrument_id
        assert result.name is not None

    @pytest.mark.asyncio
    async def test_filter_etfs_with_filters(self):
        """Test filtering ETFs with specific criteria."""
        async with AvanzaClient() as client:
            service = MarketDataService(client)
            request = ETFFilterRequest(
                filter=ETFFilter(exposures=["usa"]),
                offset=0,
                limit=10,
                sortBy=SortBy(field="name", order="asc"),
            )
            result = await service.filter_etfs(request)

        assert hasattr(result, "etfs")

    @pytest.mark.asyncio
    async def test_etf_limit_parameter(self):
        """Test ETF limit parameter is respected."""
        async with AvanzaClient() as client:
            service = MarketDataService(client)
            request = ETFFilterRequest(
                filter=ETFFilter(),
                offset=0,
                limit=3,
                sortBy=SortBy(field="name", order="asc"),
            )
            result = await service.filter_etfs(request)

        # Should return at most 3 results
        assert len(result.etfs) <= 3
