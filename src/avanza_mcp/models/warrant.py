"""Warrant-related Pydantic models."""

from pydantic import BaseModel, Field

from .filter import SortBy, FilterResponse, UnderlyingInstrument
from .stock import MODEL_CONFIG, Listing, Quote, HistoricalClosingPrices


class WarrantListItem(BaseModel):
    """Warrant in filter/list results."""

    model_config = MODEL_CONFIG

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


class WarrantInfo(BaseModel):
    """Detailed warrant information."""

    model_config = MODEL_CONFIG

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


class WarrantDetails(BaseModel):
    """Detailed warrant extended information."""

    model_config = MODEL_CONFIG

    # Flexible structure to handle various response formats
    pass


class WarrantFilter(BaseModel):
    """Filter criteria for warrants."""

    model_config = MODEL_CONFIG

    directions: list[str] = Field(default_factory=list)
    subTypes: list[str] = Field(default_factory=list)
    issuers: list[str] = Field(default_factory=list)
    underlyingInstruments: list[str] = Field(default_factory=list)


class WarrantFilterRequest(BaseModel):
    """Complete filter request for warrants."""

    model_config = MODEL_CONFIG

    filter: WarrantFilter
    offset: int = 0
    limit: int = 20
    sortBy: SortBy


class WarrantFilterResponse(FilterResponse):
    """Response from warrant filter endpoint."""

    model_config = MODEL_CONFIG

    warrants: list[WarrantListItem]
    filter: WarrantFilter | None = None
    sortBy: SortBy | None = None
