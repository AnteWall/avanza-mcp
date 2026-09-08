"""Future and forward contract models."""

from datetime import date

from pydantic import field_validator

from .common import MODEL_CONFIG as MODEL_CONFIG, AvanzaModel, OrderBookId
from .filter import SortBy, PaginationRequest
from .stock import HistoricalClosingPrices, Listing, Quote


class FutureForwardInfo(AvanzaModel):
    """Detailed future/forward information."""

    orderbookId: str
    name: str
    isin: str | None = None
    tradable: str | None = None
    listing: Listing | None = None
    historicalClosingPrices: HistoricalClosingPrices | None = None
    keyIndicators: dict | None = None
    quote: Quote | None = None
    type: str | None = None
    underlying: dict | None = None


class FutureForwardDetails(AvanzaModel):
    """Detailed future/forward extended information."""

    # Flexible structure to handle various response formats
    pass


class FutureForwardMatrixFilter(AvanzaModel):
    """Filter criteria for futures/forwards matrix."""

    underlyingInstruments: list[OrderBookId] = []
    optionTypes: list[str] = []
    endDates: list[str] = []
    callIndicators: list[str] = []

    @field_validator("endDates")
    @classmethod
    def validate_end_dates(cls, values: list[str]) -> list[str]:
        return [date.fromisoformat(value).isoformat() for value in values]


class FutureForwardMatrixRequest(PaginationRequest):
    """Request for futures/forwards matrix list."""

    filter: FutureForwardMatrixFilter
    sortBy: SortBy


class FutureForwardMatrixResponse(AvanzaModel):
    """Response from futures/forwards matrix endpoint."""

    # Flexible structure to handle matrix response
    # The actual structure will be preserved via extra="allow"
