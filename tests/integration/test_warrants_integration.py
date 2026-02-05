"""Integration tests for warrant endpoints.

These tests use real API calls and are marked with @pytest.mark.integration.
Run with: pytest tests/integration/test_warrants_integration.py -v -m integration
"""

import pytest
from avanza_mcp.client import AvanzaClient
from avanza_mcp.models.filter import SortBy
from avanza_mcp.models.warrant import WarrantFilter, WarrantFilterRequest
from avanza_mcp.services import MarketDataService


@pytest.mark.integration
class TestWarrantEndpoints:
    """Test warrant endpoints with real API."""

    @pytest.mark.asyncio
    async def test_filter_warrants(self):
        """Test warrant filter endpoint."""
        async with AvanzaClient() as client:
            service = MarketDataService(client)
            request = WarrantFilterRequest(
                filter=WarrantFilter(),
                offset=0,
                limit=5,
                sortBy=SortBy(field="name", order="asc"),
            )
            result = await service.filter_warrants(request)

        assert hasattr(result, "warrants")
        assert isinstance(result.warrants, list)
        if len(result.warrants) > 0:
            warrant = result.warrants[0]
            assert hasattr(warrant, "orderbookId")
            assert hasattr(warrant, "name")

    @pytest.mark.asyncio
    async def test_get_warrant_info(self):
        """Test getting warrant info."""
        # Using warrant ID from new.md
        instrument_id = "2267542"

        async with AvanzaClient() as client:
            service = MarketDataService(client)
            result = await service.get_warrant_info(instrument_id)

        assert result.orderbookId == instrument_id
        assert result.name is not None

    @pytest.mark.asyncio
    async def test_invalid_warrant_id(self):
        """Test getting warrant with invalid ID."""
        instrument_id = "999999999"

        with pytest.raises(Exception):  # Should raise some kind of error
            async with AvanzaClient() as client:
                service = MarketDataService(client)
                await service.get_warrant_info(instrument_id)
