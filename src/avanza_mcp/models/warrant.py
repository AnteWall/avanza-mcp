"""Warrant-related Pydantic models."""

from __future__ import annotations

from pydantic import Field

from .common import MODEL_CONFIG as MODEL_CONFIG, AvanzaModel, OrderBookId
from .filter import (
    FilterOption,
    FilterResponse,
    PaginationRequest,
    SortBy,
    UnderlyingInstrument,
)
from .stock import (
    BrokerTradeSummary,
    Documents,
    HistoricalClosingPrices,
    Listing,
    OrderDepth,
    Quote,
    Trade,
    UnderlyingInfo,
)


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
    keyIndicators: WarrantKeyIndicators | None = None
    quote: Quote | None = None
    type: str | None = None
    underlying: UnderlyingInfo | None = None
    assetCategory: str | None = None
    category: str | None = None
    subCategory: str | None = None


class WarrantDetails(AvanzaModel):
    """Detailed warrant extended information."""

    issuer: str | None = None
    documents: Documents | None = None
    orderDepth: OrderDepth | None = None
    brokerTradeSummaries: list[BrokerTradeSummary] = Field(default_factory=list)
    trades: list[Trade] = Field(default_factory=list)
    tradingUnit: float | None = None
    collateralValue: float | None = None
    endDate: str | None = None


class WarrantKeyIndicators(AvanzaModel):
    parity: float | None = None
    direction: str | None = None
    strikePrice: float | None = None
    isAza: bool | None = None
    numberOfOwners: int | None = None
    subType: str | None = None


class WarrantFilter(AvanzaModel):
    """Filter criteria for warrants."""

    directions: list[str] = Field(default_factory=list)
    subTypes: list[str] = Field(default_factory=list)
    issuers: list[str] = Field(default_factory=list)
    underlyingInstruments: list[OrderBookId] = Field(default_factory=list)


class WarrantFilterOptions(AvanzaModel):
    issuers: list[FilterOption] = Field(default_factory=list)
    underlyingInstruments: list[FilterOption] = Field(default_factory=list)
    endDates: list[FilterOption] = Field(default_factory=list)
    subTypes: list[FilterOption] = Field(default_factory=list)
    directions: list[FilterOption] = Field(default_factory=list)
    categories: list[FilterOption] = Field(default_factory=list)
    exposures: list[FilterOption] = Field(default_factory=list)


class WarrantFilterRequest(PaginationRequest):
    """Complete filter request for warrants."""

    filter: WarrantFilter
    sortBy: SortBy


class WarrantFilterResponse(FilterResponse):
    """Response from warrant filter endpoint."""

    warrants: list[WarrantListItem]
    filter: WarrantFilter | None = None
    filterOptions: WarrantFilterOptions | None = None
    sortBy: SortBy | None = None
