"""Integration tests for ETF endpoints.

These tests use real API calls and are marked with @pytest.mark.integration.
Run with: pytest tests/integration/test_etfs_integration.py -v -m integration
"""

import pytest
from avanza_mcp.models.etf import ETFFilter, ETFFilterRequest
from avanza_mcp.models.filter import SortBy


@pytest.mark.integration
class TestETFEndpoints:
    """Test ETF endpoints with real API."""

    async def test_filter_etfs(self, service):
        """Test ETF filter endpoint."""
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

    async def test_get_etf_info(self, service):
        """Test getting ETF info."""
        # Using ETF ID from new.md
        instrument_id = "742236"

        result = await service.get_etf_info(instrument_id)

        assert result.orderbookId == instrument_id
        assert result.name is not None

    async def test_filter_etfs_with_filters(self, service):
        """Test filtering ETFs with specific criteria."""
        request = ETFFilterRequest(
            filter=ETFFilter(exposures=["usa"]),
            offset=0,
            limit=10,
            sortBy=SortBy(field="name", order="asc"),
        )
        result = await service.filter_etfs(request)

        assert hasattr(result, "etfs")

    async def test_etf_limit_parameter(self, service):
        """Test ETF limit parameter is respected."""
        request = ETFFilterRequest(
            filter=ETFFilter(),
            offset=0,
            limit=3,
            sortBy=SortBy(field="name", order="asc"),
        )
        result = await service.filter_etfs(request)

        # Should return at most 3 results
        assert len(result.etfs) <= 3
