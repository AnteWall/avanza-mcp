"""ETF-related Pydantic models."""

from __future__ import annotations

from pydantic import Field

from .common import MODEL_CONFIG as MODEL_CONFIG, AvanzaModel
from .filter import FilterOption, FilterResponse, PaginationRequest, SortBy
from .fund import SustainabilityGoal
from .stock import (
    BrokerTradeSummary,
    Documents,
    HistoricalClosingPrices,
    Listing,
    MarketPlace,
    OrderDepth,
    Quote,
    Trade,
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
    collateralValue: float | None = None


class ETFDividend(AvanzaModel):
    exDate: str
    paymentDate: str
    amount: float
    currencyCode: str
    dividendType: str | None = None
    exDateStatus: str | None = None


class ETFKeyIndicators(AvanzaModel):
    direction: str | None = None
    leverage: float | None = None
    numberOfOwners: int | None = None
    dividend: ETFDividend | None = None
    historicYield: float | None = None
    historicYieldDate: str | None = None


class ETFInfo(AvanzaModel):
    """Detailed ETF information."""

    orderbookId: str
    name: str
    isin: str | None = None
    tradable: str | None = None
    listing: Listing | None = None
    marketPlace: MarketPlace | None = None
    historicalClosingPrices: HistoricalClosingPrices | None = None
    keyIndicators: ETFKeyIndicators | None = None
    quote: Quote | None = None
    type: str | None = None


class ETFDetails(AvanzaModel):
    """Detailed ETF extended information."""

    assetCategory: str | None = None
    category: str | None = None
    issuer: str | None = None
    description: str | None = None
    documents: Documents | None = None
    orderDepth: OrderDepth | None = None
    brokerTradeSummaries: list[BrokerTradeSummary] = Field(default_factory=list)
    trades: list[Trade] = Field(default_factory=list)
    tradingUnit: float | None = None
    collateralValue: float | None = None
    superInterestApproved: bool | None = None
    introDate: str | None = None
    dividends: ETFDividends | None = None
    fundExposures: list[FundExposure] = Field(default_factory=list)
    riskScore: str | None = None
    holdingPeriod: str | None = None
    countryExposures: CountryExposures | None = None
    sectorExposures: SectorExposures | None = None
    portfolioDate: str | None = None
    esgView: ESGView | None = None


class ETFDividends(AvanzaModel):
    events: list[ETFDividend] = Field(default_factory=list)
    pastEvents: list[ETFDividend] = Field(default_factory=list)


class FundExposure(AvanzaModel):
    orderbookId: str
    name: str
    exposure: float
    instrumentType: str
    countryCode: str
    hasPosition: bool


class CountryExposure(AvanzaModel):
    countryCode: str
    countryName: str
    weight: float


class CountryExposures(AvanzaModel):
    updated: str
    exposures: list[CountryExposure]


class SectorExposure(AvanzaModel):
    sector: str
    weight: float


class SectorExposures(AvanzaModel):
    updated: str
    exposures: list[SectorExposure]


class ESGView(AvanzaModel):
    euArticleType: str | None = None
    sustainabilityDevelopmentGoals: list[SustainabilityGoal] = Field(
        default_factory=list
    )


class ETFFilter(AvanzaModel):
    """Filter criteria for ETFs."""

    assetCategories: list[str] = Field(default_factory=list)
    subCategories: list[str] = Field(default_factory=list)
    exposures: list[str] = Field(default_factory=list)
    riskScores: list[str] = Field(default_factory=list)
    directions: list[str] = Field(default_factory=list)
    issuers: list[str] = Field(default_factory=list)
    currencyCodes: list[str] = Field(default_factory=list)


class ETFFilterRequest(PaginationRequest):
    """Complete filter request for ETFs."""

    filter: ETFFilter
    sortBy: SortBy


class ETFFilterOptions(AvanzaModel):
    assetCategories: list[FilterOption] = Field(default_factory=list)
    subCategories: list[FilterOption] = Field(default_factory=list)
    exposures: list[FilterOption] = Field(default_factory=list)
    riskScores: list[FilterOption] = Field(default_factory=list)
    directions: list[FilterOption] = Field(default_factory=list)
    issuers: list[FilterOption] = Field(default_factory=list)
    currencyCodes: list[FilterOption] = Field(default_factory=list)


class ETFFilterResponse(FilterResponse):
    """Response from ETF filter endpoint."""

    etfs: list[ETFListItem]
    filter: ETFFilter | None = None
    filterOptions: ETFFilterOptions | None = None
    sortBy: SortBy | None = None
