"""Integration tests for futures/forwards endpoints.

These tests use real API calls and are marked with @pytest.mark.integration.
Run with: pytest tests/integration/test_futures_forwards_integration.py -v -m integration
"""

import pytest
from avanza_mcp.models.filter import SortBy
from avanza_mcp.models.future_forward import (
    FutureForwardMatrixFilter,
    FutureForwardMatrixRequest,
)


@pytest.mark.integration
class TestFutureForwardEndpoints:
    """Test futures/forwards endpoints with real API."""

    async def test_list_futures_forwards(self, service):
        """Test listing futures/forwards with empty filters."""
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

    async def test_get_future_forward_info(self, service):
        """Test getting future/forward info."""
        # Discover a current contract instead of pinning an expiring ID.
        contracts = await service.list_futures_forwards(
            FutureForwardMatrixRequest(
                filter=FutureForwardMatrixFilter(),
                limit=1,
                sortBy=SortBy(field="strikePrice", order="desc"),
            )
        )
        futures = contracts.model_dump()["futureForwards"]
        assert futures, "Expected at least one current future/forward"
        instrument_id = futures[0]["orderbookId"]
        result = await service.get_future_forward_info(instrument_id)

        assert result.orderbookId == instrument_id
        assert result.name is not None

    async def test_get_future_forward_filter_options(self, service):
        """Test getting filter options for futures/forwards."""
        result = await service.get_future_forward_filter_options()

        assert result is not None
        assert isinstance(result, dict)
