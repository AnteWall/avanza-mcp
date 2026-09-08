"""Unit tests for additional instrument data models."""

from avanza_mcp.models.instrument_data import NumberOfOwners, ShortSellingData


class TestInstrumentDataModels:
    """Test additional instrument data models."""

    def test_number_of_owners(self):
        """Test NumberOfOwners model."""
        data = {
            "ownersPoints": [{"numberOfOwners": 50000, "timestamp": 123456}],
            "historySummary": {"oneYearChange": 0},
        }
        owners = NumberOfOwners.model_validate(data)
        assert owners.ownersPoints[0].numberOfOwners == 50000
        assert owners.historySummary.oneYearChange == 0

    def test_short_selling_data(self):
        """Test ShortSellingData model."""
        data = {
            "shortSellingHistory": [{"timestamp": 123456, "ratio": 0.011}],
        }
        short_data = ShortSellingData.model_validate(data)
        assert short_data.shortSellingHistory[0].ratio == 0.011
