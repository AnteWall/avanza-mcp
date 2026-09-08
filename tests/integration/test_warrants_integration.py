"""Integration tests for warrant endpoints.

These tests use real API calls and are marked with @pytest.mark.integration.
Run with: pytest tests/integration/test_warrants_integration.py -v -m integration
"""

import pytest
from avanza_mcp.models.filter import SortBy
from avanza_mcp.models.warrant import WarrantFilter, WarrantFilterRequest


@pytest.mark.integration
class TestWarrantEndpoints:
    """Test warrant endpoints with real API."""

    async def test_filter_warrants(self, service):
        """Test warrant filter endpoint."""
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

    async def test_get_warrant_info(self, service):
        """Test getting warrant info."""
        # Discover a current warrant instead of pinning an expiring ID.
        warrants = await service.filter_warrants(
            WarrantFilterRequest(
                filter=WarrantFilter(),
                limit=1,
                sortBy=SortBy(field="name", order="asc"),
            )
        )
        assert warrants.warrants, "Expected at least one current warrant"
        instrument_id = warrants.warrants[0].orderbookId
        result = await service.get_warrant_info(instrument_id)

        assert result.orderbookId == instrument_id
        assert result.name is not None

    async def test_invalid_warrant_id(self, service):
        """Test getting warrant with invalid ID."""
        instrument_id = "999999999"

        with pytest.raises(Exception):  # Should raise some kind of error
            await service.get_warrant_info(instrument_id)
