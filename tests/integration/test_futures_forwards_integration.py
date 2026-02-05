"""Integration tests for futures/forwards endpoints.

These tests use real API calls and are marked with @pytest.mark.integration.
Run with: pytest tests/integration/test_futures_forwards_integration.py -v -m integration
"""

import pytest
from avanza_mcp.client import AvanzaClient
from avanza_mcp.models.filter import SortBy
from avanza_mcp.models.future_forward import (
    FutureForwardMatrixFilter,
    FutureForwardMatrixRequest,
)
from avanza_mcp.services import MarketDataService


@pytest.mark.integration
class TestFutureForwardEndpoints:
    """Test futures/forwards endpoints with real API."""

    @pytest.mark.asyncio
    async def test_list_futures_forwards(self):
        """Test listing futures/forwards with empty filters."""
        async with AvanzaClient() as client:
            service = MarketDataService(client)
            # Use empty filters as shown in the working curl example
            request = FutureForwardMatrixRequest(
                filter=FutureForwardMatrixFilter(
                    underlyingInstruments=[],
                    optionTypes=[],
                    endDates=[],
                    callIndicators=[],
                ),
                offset=0,
                limit=5,
                sortBy=SortBy(field="strikePrice", order="desc"),
            )
            result = await service.list_futures_forwards(request)

        # Result structure may vary, just check it returns something
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_future_forward_info(self):
        """Test getting future/forward info."""
        # Using future/forward ID from new.md
        instrument_id = "2224452"

        async with AvanzaClient() as client:
            service = MarketDataService(client)
            result = await service.get_future_forward_info(instrument_id)

        assert result.orderbookId == instrument_id
        assert result.name is not None

    @pytest.mark.asyncio
    async def test_get_future_forward_filter_options(self):
        """Test getting filter options for futures/forwards."""
        async with AvanzaClient() as client:
            service = MarketDataService(client)
            result = await service.get_future_forward_filter_options()

        assert result is not None
        assert isinstance(result, dict)
