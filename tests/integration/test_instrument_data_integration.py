"""Integration tests for additional instrument data endpoints.

These tests use real API calls and are marked with @pytest.mark.integration.
Run with: pytest tests/integration/test_instrument_data_integration.py -v -m integration
"""

import pytest
from avanza_mcp.client import AvanzaClient
from avanza_mcp.services import MarketDataService


@pytest.mark.integration
class TestInstrumentDataEndpoints:
    """Test additional instrument data endpoints with real API."""

    @pytest.mark.asyncio
    async def test_get_number_of_owners(self):
        """Test number of owners endpoint."""
        # Using stock ID from new.md
        instrument_id = "1154359"

        async with AvanzaClient() as client:
            service = MarketDataService(client)
            result = await service.get_number_of_owners(instrument_id)

        assert result is not None
        # The response should have numberOfOwners
        assert hasattr(result, "numberOfOwners")

    @pytest.mark.asyncio
    async def test_get_short_selling(self):
        """Test short selling endpoint."""
        # Using stock ID from new.md
        instrument_id = "5247"

        async with AvanzaClient() as client:
            service = MarketDataService(client)
            result = await service.get_short_selling(instrument_id)

        assert result is not None
        # The response should have orderbookId
        assert hasattr(result, "orderbookId")
