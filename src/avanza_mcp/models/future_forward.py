"""Future and forward contract models."""

from .common import MODEL_CONFIG as MODEL_CONFIG, AvanzaModel
from .filter import SortBy
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

    underlyingInstruments: list[str] = []
    optionTypes: list[str] = []
    endDates: list[str] = []
    callIndicators: list[str] = []


class FutureForwardMatrixRequest(AvanzaModel):
    """Request for futures/forwards matrix list."""

    filter: FutureForwardMatrixFilter
    offset: int = 0
    limit: int = 20
    sortBy: SortBy


class FutureForwardMatrixResponse(AvanzaModel):
    """Response from futures/forwards matrix endpoint."""

    # Flexible structure to handle matrix response
    # The actual structure will be preserved via extra="allow"
