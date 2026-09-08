"""Warrant-related Pydantic models."""

from pydantic import Field

from .common import MODEL_CONFIG as MODEL_CONFIG, AvanzaModel, OrderBookId
from .filter import SortBy, FilterResponse, UnderlyingInstrument, PaginationRequest
from .stock import Listing, Quote, HistoricalClosingPrices


class WarrantListItem(AvanzaModel):
    """Warrant in filter/list results."""

    orderbookId: str
    countryCode: str
    name: str
    direction: str
    issuer: str
    subType: str
    hasPosition: bool
    underlyingInstrument: UnderlyingInstrument | None = None
    totalValueTraded: float | None = None
    stopLoss: float | None = None
    oneDayChangePercent: float | None = None
    spread: float | None = None
    buyPrice: float | None = None
    sellPrice: float | None = None


class WarrantInfo(AvanzaModel):
    """Detailed warrant information."""

    orderbookId: str
    name: str
    isin: str | None = None
    tradable: str | None = None
    listing: Listing | None = None
    historicalClosingPrices: HistoricalClosingPrices | None = None
    keyIndicators: dict | None = None  # Different structure than stock
    quote: Quote | None = None
    type: str | None = None
    underlying: dict | None = None  # Nested underlying instrument info
    assetCategory: str | None = None
    category: str | None = None
    subCategory: str | None = None


class WarrantDetails(AvanzaModel):
    """Detailed warrant extended information."""

    # Flexible structure to handle various response formats
    pass


class WarrantFilter(AvanzaModel):
    """Filter criteria for warrants."""

    directions: list[str] = Field(default_factory=list)
    subTypes: list[str] = Field(default_factory=list)
    issuers: list[str] = Field(default_factory=list)
    underlyingInstruments: list[OrderBookId] = Field(default_factory=list)


class WarrantFilterRequest(PaginationRequest):
    """Complete filter request for warrants."""

    filter: WarrantFilter
    sortBy: SortBy


class WarrantFilterResponse(FilterResponse):
    """Response from warrant filter endpoint."""

    warrants: list[WarrantListItem]
    filter: WarrantFilter | None = None
    sortBy: SortBy | None = None
