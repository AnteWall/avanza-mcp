"""Unit tests for additional instrument data models."""

from avanza_mcp.models.instrument_data import NumberOfOwners, ShortSellingData


class TestInstrumentDataModels:
    """Test additional instrument data models."""

    def test_number_of_owners(self):
        """Test NumberOfOwners model."""
        data = {"orderbookId": "5247", "numberOfOwners": 50000, "timestamp": 123456}
        owners = NumberOfOwners.model_validate(data)
        assert owners.orderbookId == "5247"
        assert owners.numberOfOwners == 50000

    def test_short_selling_data(self):
        """Test ShortSellingData model."""
        data = {
            "orderbookId": "5247",
            "shortSellingVolume": 100000.0,
            "shortSellingPercentage": 5.5,
            "date": "2026-02-05",
        }
        short_data = ShortSellingData.model_validate(data)
        assert short_data.orderbookId == "5247"
        assert short_data.shortSellingPercentage == 5.5
