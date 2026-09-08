"""Certificate-related Pydantic models."""

from pydantic import Field
from .common import MODEL_CONFIG as MODEL_CONFIG, AvanzaModel
from .stock import Quote, Listing, HistoricalClosingPrices, KeyIndicators
from .filter import UnderlyingInstrument, SortBy, FilterResponse


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

    # Flexible structure to handle various response formats
    pass


class CertificateFilter(AvanzaModel):
    """Filter criteria for certificates."""

    directions: list[str] = Field(default_factory=list)
    leverages: list[float] = Field(default_factory=list)
    underlyingInstruments: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    exposures: list[str] = Field(default_factory=list)
    issuers: list[str] = Field(default_factory=list)


class CertificateFilterRequest(AvanzaModel):
    """Complete filter request for certificates."""

    filter: CertificateFilter
    offset: int = 0
    limit: int = 20
    sortBy: SortBy


class CertificateFilterResponse(FilterResponse):
    """Response from certificate filter endpoint."""

    certificates: list[CertificateListItem]
    filter: CertificateFilter | None = None
    sortBy: SortBy | None = None
