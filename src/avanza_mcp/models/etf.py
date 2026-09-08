"""ETF-related Pydantic models."""

from pydantic import Field

from .common import MODEL_CONFIG as MODEL_CONFIG, AvanzaModel
from .filter import FilterResponse, SortBy
from .stock import (
    HistoricalClosingPrices,
    Listing,
    MarketPlace,
    Quote,
)


class ETFListItem(AvanzaModel):
    """ETF in filter/list results."""

    orderbookId: str
    countryCode: str
    name: str
    directYield: float | None = None
    oneDayChangePercent: float | None = None
    threeYearsChangePercent: float | None = None
    managementFee: float | None = None
    productFee: float | None = None
    numberOfOwners: int | None = None
    riskScore: int | None = None
    hasPosition: bool = False


class ETFInfo(AvanzaModel):
    """Detailed ETF information."""

    orderbookId: str
    name: str
    isin: str | None = None
    tradable: str | None = None
    listing: Listing | None = None
    marketPlace: MarketPlace | None = None
    historicalClosingPrices: HistoricalClosingPrices | None = None
    keyIndicators: dict | None = None
    quote: Quote | None = None
    type: str | None = None


class ETFDetails(AvanzaModel):
    """Detailed ETF extended information."""

    # Flexible structure to handle various response formats
    pass


class ETFFilter(AvanzaModel):
    """Filter criteria for ETFs."""

    assetCategories: list[str] = Field(default_factory=list)
    subCategories: list[str] = Field(default_factory=list)
    exposures: list[str] = Field(default_factory=list)
    riskScores: list[str] = Field(default_factory=list)
    directions: list[str] = Field(default_factory=list)
    issuers: list[str] = Field(default_factory=list)
    currencyCodes: list[str] = Field(default_factory=list)


class ETFFilterRequest(AvanzaModel):
    """Complete filter request for ETFs."""

    filter: ETFFilter
    offset: int = 0
    limit: int = 20
    sortBy: SortBy


class ETFFilterResponse(FilterResponse):
    """Response from ETF filter endpoint."""

    etfs: list[ETFListItem]
    filter: ETFFilter | None = None
    filterOptions: dict | None = None  # Available filter options
    sortBy: SortBy | None = None
