"""Unit tests for warrant models."""

from avanza_mcp.models.filter import SortBy
from avanza_mcp.models.warrant import (
    WarrantFilter,
    WarrantFilterRequest,
    WarrantInfo,
    WarrantListItem,
)


class TestWarrantModels:
    """Test warrant models."""

    def test_warrant_list_item(self):
        """Test WarrantListItem creation."""
        item = WarrantListItem(
            orderbookId="2267542",
            countryCode="SE",
            name="Test Warrant",
            direction="long",
            issuer="Societe Generale",
            subType="TURBO",
            hasPosition=False,
            stopLoss=100.0,
        )
        assert item.orderbookId == "2267542"
        assert item.subType == "TURBO"
        assert item.stopLoss == 100.0

    def test_warrant_filter_creation(self):
        """Test warrant filter."""
        filter_obj = WarrantFilter(
            directions=["long"], subTypes=["TURBO"], issuers=["Societe Generale"]
        )
        assert len(filter_obj.directions) == 1
        assert filter_obj.subTypes == ["TURBO"]

    def test_warrant_filter_request(self):
        """Test WarrantFilterRequest."""
        request = WarrantFilterRequest(
            filter=WarrantFilter(subTypes=["TURBO"]),
            offset=0,
            limit=20,
            sortBy=SortBy(field="name", order="asc"),
        )
        assert request.filter.subTypes == ["TURBO"]
        assert request.offset == 0

    def test_warrant_info_with_underlying(self):
        """Test warrant with underlying instrument."""
        data = {
            "orderbookId": "2267542",
            "name": "Test Warrant",
            "type": "WARRANT",
            "underlying": {"name": "Test Stock", "orderbookId": "12345"},
        }
        warrant = WarrantInfo.model_validate(data)
        assert warrant.orderbookId == "2267542"
        assert warrant.underlying is not None
