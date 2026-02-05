"""Unit tests for certificate models."""

from avanza_mcp.models.certificate import (
    CertificateFilter,
    CertificateFilterRequest,
    CertificateFilterResponse,
    CertificateInfo,
    CertificateListItem,
)
from avanza_mcp.models.filter import SortBy


class TestCertificateModels:
    """Test certificate models."""

    def test_certificate_list_item(self):
        """Test CertificateListItem creation."""
        item = CertificateListItem(
            orderbookId="1756318",
            countryCode="DE",
            name="Test Certificate",
            direction="long",
            marketplaceCode="XETR",
            issuer="Valour",
            hasPosition=False,
            leverage=1.0,
            buyPrice=0.33,
            sellPrice=0.34,
        )
        assert item.orderbookId == "1756318"
        assert item.direction == "long"
        assert item.leverage == 1.0

    def test_certificate_filter_creation(self):
        """Test creating certificate filter."""
        filter_obj = CertificateFilter(
            directions=["long"], leverages=[1.0], issuers=["Valour"]
        )
        assert filter_obj.directions == ["long"]
        assert filter_obj.leverages == [1.0]
        assert filter_obj.issuers == ["Valour"]

    def test_certificate_filter_request(self):
        """Test CertificateFilterRequest."""
        request = CertificateFilterRequest(
            filter=CertificateFilter(directions=["long"]),
            offset=0,
            limit=20,
            sortBy=SortBy(field="name", order="asc"),
        )
        assert request.offset == 0
        assert request.limit == 20
        assert request.filter.directions == ["long"]

    def test_certificate_filter_response(self):
        """Test CertificateFilterResponse parsing."""
        data = {
            "certificates": [
                {
                    "orderbookId": "1756318",
                    "countryCode": "DE",
                    "name": "Test Certificate",
                    "direction": "long",
                    "marketplaceCode": "XETR",
                    "issuer": "Valour",
                    "hasPosition": False,
                    "leverage": 1.0,
                    "spread": 0.0054,
                    "buyPrice": 0.33,
                    "sellPrice": 0.34,
                }
            ],
            "totalNumberOfOrderbooks": 1,
        }
        response = CertificateFilterResponse.model_validate(data)
        assert len(response.certificates) == 1
        assert response.certificates[0].orderbookId == "1756318"

    def test_certificate_info_validation(self):
        """Test certificate info model validation."""
        data = {
            "orderbookId": "1756318",
            "name": "Test Certificate",
            "type": "CERTIFICATE",
            "listing": {
                "shortName": "TEST",
                "currency": "EUR",
                "marketPlaceName": "Xetra",
            },
        }
        cert = CertificateInfo.model_validate(data)
        assert cert.orderbookId == "1756318"
        assert cert.name == "Test Certificate"

    def test_certificate_filter_request_serialization(self):
        """Test filter request serializes correctly."""
        request = CertificateFilterRequest(
            filter=CertificateFilter(directions=["long"], issuers=["Valour"]),
            offset=10,
            limit=30,
            sortBy=SortBy(field="name", order="desc"),
        )
        data = request.model_dump(by_alias=True, exclude_none=True)
        assert data["offset"] == 10
        assert data["limit"] == 30
        assert "filter" in data
        assert data["filter"]["directions"] == ["long"]

    def test_model_extra_allow(self):
        """Test that models accept extra fields."""
        # This should not raise an error due to extra="allow"
        data = {
            "orderbookId": "12345",
            "name": "Test",
            "unknownField": "should be allowed",
        }
        info = CertificateInfo.model_validate(data)
        assert info.orderbookId == "12345"
