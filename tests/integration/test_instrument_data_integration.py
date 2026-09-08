"""Integration tests for additional instrument data endpoints.

These tests use real API calls and are marked with @pytest.mark.integration.
Run with: pytest tests/integration/test_instrument_data_integration.py -v -m integration
"""

import pytest

from avanza_mcp.models.instrument_data import (
    NumberOfOwners,
    OwnersHistorySummary,
    OwnersPoint,
    ShortSellingData,
    ShortSellingPoint,
)

pytestmark = pytest.mark.integration


class TestInstrumentDataEndpoints:
    """Test additional instrument data endpoints with real API."""

    async def test_get_number_of_owners(self, service):
        """Test number of owners endpoint."""
        # Using stock ID from new.md
        instrument_id = "1154359"

        result = await service.get_number_of_owners(instrument_id)

        assert isinstance(result, NumberOfOwners)
        assert isinstance(result.ownersPoints, list)
        for point in result.ownersPoints:
            assert isinstance(point, OwnersPoint)
            assert isinstance(point.timestamp, int)
            assert isinstance(point.numberOfOwners, int) and point.numberOfOwners >= 0
        if result.historySummary is not None:
            assert isinstance(result.historySummary, OwnersHistorySummary)
            for change in (
                result.historySummary.oneYearChange,
                result.historySummary.thisYearChange,
            ):
                assert change is None or isinstance(change, int)
            for change in (
                result.historySummary.oneYearChangePercent,
                result.historySummary.thisYearChangePercent,
            ):
                assert change is None or isinstance(change, float)

    async def test_get_short_selling(self, service):
        """Test short selling endpoint."""
        # Using stock ID from new.md
        instrument_id = "5247"

        result = await service.get_short_selling(instrument_id)

        assert isinstance(result, ShortSellingData)
        assert isinstance(result.shortSellingHistory, list)
        for point in result.shortSellingHistory:
            assert isinstance(point, ShortSellingPoint)
            assert isinstance(point.timestamp, int)
            assert isinstance(point.ratio, float)
