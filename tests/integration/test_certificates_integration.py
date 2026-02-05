"""Integration tests for certificate endpoints.

These tests use real API calls and are marked with @pytest.mark.integration.
Run with: pytest tests/integration/test_certificates_integration.py -v -m integration
"""

import pytest
from avanza_mcp.client import AvanzaClient
from avanza_mcp.models.certificate import (
    CertificateFilter,
    CertificateFilterRequest,
)
from avanza_mcp.models.filter import SortBy
from avanza_mcp.services import MarketDataService


@pytest.mark.integration
class TestCertificateEndpoints:
    """Test certificate endpoints with real API."""

    @pytest.mark.asyncio
    async def test_filter_certificates(self):
        """Test certificate filter endpoint."""
        async with AvanzaClient() as client:
            service = MarketDataService(client)
            request = CertificateFilterRequest(
                filter=CertificateFilter(),
                offset=0,
                limit=5,
                sortBy=SortBy(field="name", order="asc"),
            )
            result = await service.filter_certificates(request)

        assert hasattr(result, "certificates")
        assert isinstance(result.certificates, list)
        if len(result.certificates) > 0:
            cert = result.certificates[0]
            assert hasattr(cert, "orderbookId")
            assert hasattr(cert, "name")

    @pytest.mark.asyncio
    async def test_get_certificate_info(self):
        """Test getting certificate info."""
        # Using certificate ID from new.md
        instrument_id = "1756318"

        async with AvanzaClient() as client:
            service = MarketDataService(client)
            result = await service.get_certificate_info(instrument_id)

        assert result.orderbookId == instrument_id
        assert result.name is not None

    @pytest.mark.asyncio
    async def test_filter_certificates_with_filters(self):
        """Test filtering certificates with specific criteria."""
        async with AvanzaClient() as client:
            service = MarketDataService(client)
            request = CertificateFilterRequest(
                filter=CertificateFilter(directions=["long"]),
                offset=0,
                limit=10,
                sortBy=SortBy(field="name", order="asc"),
            )
            result = await service.filter_certificates(request)

        assert hasattr(result, "certificates")
        # All results should have direction="long"
        for cert in result.certificates:
            if hasattr(cert, "direction"):
                assert cert.direction == "long"

    @pytest.mark.asyncio
    async def test_certificate_pagination(self):
        """Test certificate pagination works correctly."""
        async with AvanzaClient() as client:
            service = MarketDataService(client)

            # Get first page
            request1 = CertificateFilterRequest(
                filter=CertificateFilter(),
                offset=0,
                limit=5,
                sortBy=SortBy(field="name", order="asc"),
            )
            result1 = await service.filter_certificates(request1)

            # Get second page
            request2 = CertificateFilterRequest(
                filter=CertificateFilter(),
                offset=5,
                limit=5,
                sortBy=SortBy(field="name", order="asc"),
            )
            result2 = await service.filter_certificates(request2)

        # If there are enough results, pages should be different
        if len(result1.certificates) > 0 and len(result2.certificates) > 0:
            assert result1.certificates[0].orderbookId != result2.certificates[
                0
            ].orderbookId

    @pytest.mark.asyncio
    async def test_invalid_certificate_id(self):
        """Test getting certificate with invalid ID."""
        instrument_id = "999999999"

        with pytest.raises(Exception):  # Should raise some kind of error
            async with AvanzaClient() as client:
                service = MarketDataService(client)
                await service.get_certificate_info(instrument_id)
