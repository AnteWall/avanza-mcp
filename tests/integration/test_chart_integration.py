"""Integration tests for chart endpoints.

These tests use real API calls and are marked with @pytest.mark.integration.
Run with: pytest tests/integration/test_chart_integration.py -v -m integration
"""

import pytest
from avanza_mcp.client import AvanzaClient
from avanza_mcp.services import MarketDataService


@pytest.mark.integration
class TestChartEndpoints:
    """Test chart endpoints with real API."""

    @pytest.mark.asyncio
    async def test_get_marketmaker_chart_certificate(self):
        """Test getting chart data for a certificate."""
        # Using certificate ID from user's example
        instrument_id = "2090357"

        async with AvanzaClient() as client:
            service = MarketDataService(client)
            result = await service.get_marketmaker_chart(
                instrument_id, time_period="today"
            )

        assert result is not None
        assert hasattr(result, "ohlc")
        assert isinstance(result.ohlc, list)
        assert hasattr(result, "metadata")
        assert hasattr(result, "marketMaker")

    @pytest.mark.asyncio
    async def test_get_marketmaker_chart_etf(self):
        """Test getting chart data for an ETF."""
        # Using ETF ID from user's example (can use stock chart endpoint too)
        instrument_id = "5649"

        async with AvanzaClient() as client:
            service = MarketDataService(client)
            result = await service.get_marketmaker_chart(
                instrument_id, time_period="today"
            )

        assert result is not None
        assert hasattr(result, "ohlc")
        assert len(result.ohlc) > 0
        # First OHLC point should have all required fields
        if len(result.ohlc) > 0:
            point = result.ohlc[0]
            assert hasattr(point, "timestamp")
            assert hasattr(point, "open")
            assert hasattr(point, "close")
            assert hasattr(point, "high")
            assert hasattr(point, "low")
            assert hasattr(point, "totalVolumeTraded")

    @pytest.mark.asyncio
    async def test_get_marketmaker_chart_different_periods(self):
        """Test chart with different time periods."""
        instrument_id = "2090357"

        async with AvanzaClient() as client:
            service = MarketDataService(client)

            # Test today
            result_today = await service.get_marketmaker_chart(
                instrument_id, time_period="today"
            )
            assert result_today is not None

            # Test one_week
            result_week = await service.get_marketmaker_chart(
                instrument_id, time_period="one_week"
            )
            assert result_week is not None

            # Week should have more data points than today (usually)
            # Note: This might not always be true depending on trading activity

    @pytest.mark.asyncio
    async def test_chart_metadata(self):
        """Test that chart metadata is properly returned."""
        instrument_id = "2090357"

        async with AvanzaClient() as client:
            service = MarketDataService(client)
            result = await service.get_marketmaker_chart(
                instrument_id, time_period="today"
            )

        assert result.metadata is not None
        assert hasattr(result.metadata, "resolution")
        assert hasattr(result.metadata.resolution, "chartResolution")
        assert hasattr(result.metadata.resolution, "availableResolutions")
        assert isinstance(result.metadata.resolution.availableResolutions, list)

    @pytest.mark.asyncio
    async def test_invalid_instrument_for_chart(self):
        """Test getting chart with invalid instrument ID."""
        instrument_id = "999999999"

        with pytest.raises(Exception):  # Should raise some kind of error
            async with AvanzaClient() as client:
                service = MarketDataService(client)
                await service.get_marketmaker_chart(instrument_id, time_period="today")
