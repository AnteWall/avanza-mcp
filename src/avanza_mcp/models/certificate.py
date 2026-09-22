"""Certificate-related Pydantic models."""

from pydantic import Field
from .common import MODEL_CONFIG as MODEL_CONFIG, AvanzaModel, OrderBookId
from .stock import (
    BrokerTradeSummary,
    Documents,
    HistoricalClosingPrices,
    KeyIndicators,
    Listing,
    OrderDepth,
    Quote,
    Trade,
)
from .filter import (
    FilterOption,
    FilterResponse,
    PaginationRequest,
    SortBy,
    UnderlyingInstrument,
)


class CertificateListItem(AvanzaModel):
    """Certificate in filter/list results."""

    orderbookId: str
    countryCode: str
    name: str
    direction: str
    marketplaceCode: str
    issuer: str
    hasPosition: bool
    totalValueTraded: float | None = None
    underlyingInstrument: UnderlyingInstrument | None = None
    leverage: float | None = None
    spread: float | None = None
    buyPrice: float | None = None
    sellPrice: float | None = None


class CertificateInfo(AvanzaModel):
    """Detailed certificate information."""

    orderbookId: str
    name: str
    isin: str | None = None
    tradable: str | None = None
    listing: Listing | None = None
    historicalClosingPrices: HistoricalClosingPrices | None = None
    keyIndicators: KeyIndicators | None = None
    quote: Quote | None = None
    type: str | None = None
    assetCategory: str | None = None
    category: str | None = None
    subCategory: str | None = None


class CertificateDetails(AvanzaModel):
    """Detailed certificate extended information."""

    issuer: str | None = None
    direction: str | None = None
    leverage: float | None = None
    documents: Documents | None = None
    trades: list[Trade] = Field(default_factory=list)
    orderDepth: OrderDepth | None = None
    brokerTradeSummaries: list[BrokerTradeSummary] = Field(default_factory=list)
    collateralValue: float | None = None
    superInterestApproved: bool | None = None


class CertificateFilter(AvanzaModel):
    """Filter criteria for certificates."""

    directions: list[str] = Field(default_factory=list)
    leverages: list[float] = Field(default_factory=list)
    underlyingInstruments: list[OrderBookId] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    exposures: list[str] = Field(default_factory=list)
    issuers: list[str] = Field(default_factory=list)
    marketplaceCodes: list[str] = Field(default_factory=list)
    subTypes: list[str] = Field(default_factory=list)


class CertificateFilterOptions(AvanzaModel):
    marketplaces: list[FilterOption] = Field(default_factory=list)
    issuers: list[FilterOption] = Field(default_factory=list)
    underlyingInstruments: list[FilterOption] = Field(default_factory=list)
    exposures: list[FilterOption] = Field(default_factory=list)
    leverages: list[FilterOption] = Field(default_factory=list)
    directions: list[FilterOption] = Field(default_factory=list)
    categories: list[FilterOption] = Field(default_factory=list)
    subTypes: list[FilterOption] = Field(default_factory=list)


class CertificateFilterRequest(PaginationRequest):
    """Complete filter request for certificates."""

    filter: CertificateFilter
    sortBy: SortBy


class CertificateFilterResponse(FilterResponse):
    """Response from certificate filter endpoint."""

    certificates: list[CertificateListItem]
    filter: CertificateFilter | None = None
    filterOptions: CertificateFilterOptions | None = None
    sortBy: SortBy | None = None
