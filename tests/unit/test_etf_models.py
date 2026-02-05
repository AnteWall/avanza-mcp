"""Unit tests for ETF models."""

from avanza_mcp.models.etf import ETFFilter, ETFFilterRequest, ETFInfo, ETFListItem
from avanza_mcp.models.filter import SortBy


class TestETFModels:
    """Test ETF models."""

    def test_etf_list_item(self):
        """Test ETFListItem creation."""
        item = ETFListItem(
            orderbookId="742236",
            countryCode="SE",
            name="Test ETF",
            directYield=2.5,
            managementFee=0.25,
            numberOfOwners=1000,
            riskScore=4,
        )
        assert item.orderbookId == "742236"
        assert item.directYield == 2.5
        assert item.numberOfOwners == 1000

    def test_etf_filter_with_exposures(self):
        """Test ETF filter with geographic exposures."""
        filter_obj = ETFFilter(
            exposures=["usa", "global"], riskScores=["risk_four"]
        )
        assert len(filter_obj.exposures) == 2
        assert filter_obj.exposures[0] == "usa"

    def test_etf_filter_request(self):
        """Test ETFFilterRequest."""
        request = ETFFilterRequest(
            filter=ETFFilter(assetCategories=["stock"]),
            offset=0,
            limit=50,
            sortBy=SortBy(field="numberOfOwners", order="desc"),
        )
        assert request.limit == 50
        assert request.sortBy.order == "desc"

    def test_etf_info_validation(self):
        """Test ETF info model validation."""
        data = {
            "orderbookId": "742236",
            "name": "Test ETF",
            "type": "ETF",
            "isin": "SE0007158910",
        }
        etf = ETFInfo.model_validate(data)
        assert etf.orderbookId == "742236"
        assert etf.name == "Test ETF"
