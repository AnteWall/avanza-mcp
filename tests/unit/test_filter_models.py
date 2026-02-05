"""Unit tests for shared filter models."""

import pytest
from avanza_mcp.models.filter import SortBy, UnderlyingInstrument


class TestFilterModels:
    """Test shared filter models."""

    def test_sort_by_creation(self):
        """Test SortBy model."""
        sort = SortBy(field="name", order="asc")
        assert sort.field == "name"
        assert sort.order == "asc"

    def test_sort_by_validation(self):
        """Test SortBy validates order."""
        with pytest.raises(ValueError):
            SortBy(field="name", order="invalid")

    def test_underlying_instrument(self):
        """Test UnderlyingInstrument model."""
        instrument = UnderlyingInstrument(
            name="Test Stock",
            orderbookId="12345",
            instrumentType="STOCK",
            countryCode="SE",
        )
        assert instrument.name == "Test Stock"
        assert instrument.orderbookId == "12345"
