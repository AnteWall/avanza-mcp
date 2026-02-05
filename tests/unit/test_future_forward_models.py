"""Unit tests for futures/forwards models."""

from avanza_mcp.models.filter import SortBy
from avanza_mcp.models.future_forward import (
    FutureForwardInfo,
    FutureForwardMatrixFilter,
    FutureForwardMatrixRequest,
)


class TestFutureForwardModels:
    """Test futures/forwards models."""

    def test_future_forward_info(self):
        """Test FutureForwardInfo model."""
        data = {
            "orderbookId": "2224452",
            "name": "Test Future",
            "type": "FUTURE_FORWARD",
        }
        info = FutureForwardInfo.model_validate(data)
        assert info.orderbookId == "2224452"
        assert info.name == "Test Future"

    def test_future_forward_matrix_filter(self):
        """Test matrix filter model."""
        filter_obj = FutureForwardMatrixFilter(
            underlyingInstruments=["12345"],
            optionTypes=[],
            endDates=["2026-02-06"],
            callIndicators=[],
        )
        assert filter_obj.underlyingInstruments == ["12345"]
        assert filter_obj.endDates == ["2026-02-06"]

    def test_future_forward_matrix_request(self):
        """Test matrix request model."""
        request = FutureForwardMatrixRequest(
            filter=FutureForwardMatrixFilter(
                underlyingInstruments=["12345"],
                optionTypes=[],
                endDates=["2026-02-06"],
                callIndicators=[],
            ),
            offset=0,
            limit=20,
            sortBy=SortBy(field="strikePrice", order="desc"),
        )
        assert request.filter.underlyingInstruments == ["12345"]
        assert request.offset == 0
        assert request.sortBy.field == "strikePrice"

    def test_matrix_request_with_empty_filters(self):
        """Test matrix request with empty filters (common use case)."""
        request = FutureForwardMatrixRequest(
            filter=FutureForwardMatrixFilter(
                underlyingInstruments=[],
                optionTypes=[],
                endDates=[],
                callIndicators=[],
            ),
            offset=0,
            limit=20,
            sortBy=SortBy(field="strikePrice", order="desc"),
        )
        assert request.filter.underlyingInstruments == []
        assert request.sortBy.order == "desc"
