"""Future and forward contract models."""

from pydantic import BaseModel

from .filter import SortBy
from .stock import MODEL_CONFIG, HistoricalClosingPrices, Listing, Quote


class FutureForwardInfo(BaseModel):
    """Detailed future/forward information."""

    model_config = MODEL_CONFIG

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


class FutureForwardDetails(BaseModel):
    """Detailed future/forward extended information."""

    model_config = MODEL_CONFIG

    # Flexible structure to handle various response formats
    pass


class FutureForwardMatrixFilter(BaseModel):
    """Filter criteria for futures/forwards matrix."""

    model_config = MODEL_CONFIG

    underlyingInstruments: list[str] = []
    optionTypes: list[str] = []
    endDates: list[str] = []
    callIndicators: list[str] = []


class FutureForwardMatrixRequest(BaseModel):
    """Request for futures/forwards matrix list."""

    model_config = MODEL_CONFIG

    filter: FutureForwardMatrixFilter
    offset: int = 0
    limit: int = 20
    sortBy: SortBy


class FutureForwardMatrixResponse(BaseModel):
    """Response from futures/forwards matrix endpoint."""

    model_config = MODEL_CONFIG

    # Flexible structure to handle matrix response
    # The actual structure will be preserved via extra="allow"
