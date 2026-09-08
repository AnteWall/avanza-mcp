"""Integration tests for additional instrument data endpoints.

These tests use real API calls and are marked with @pytest.mark.integration.
Run with: pytest tests/integration/test_instrument_data_integration.py -v -m integration
"""

import pytest


@pytest.mark.integration
class TestInstrumentDataEndpoints:
    """Test additional instrument data endpoints with real API."""

    async def test_get_number_of_owners(self, service):
        """Test number of owners endpoint."""
        # Using stock ID from new.md
        instrument_id = "1154359"

        result = await service.get_number_of_owners(instrument_id)

        assert result is not None
        # The response should have numberOfOwners
        assert hasattr(result, "numberOfOwners")

    async def test_get_short_selling(self, service):
        """Test short selling endpoint."""
        # Using stock ID from new.md
        instrument_id = "5247"

        result = await service.get_short_selling(instrument_id)

        assert result is not None
        # The response should have orderbookId
        assert hasattr(result, "orderbookId")
