"""Search result models matching Avanza API response structure."""

from pydantic import Field

from .common import MODEL_CONFIG as MODEL_CONFIG, AvanzaModel


class SearchPrice(AvanzaModel):
    """Price information for a search result."""

    last: str | None = None
    currency: str | None = None
    todayChangePercent: str | None = None
    todayChangeValue: str | None = None
    todayChangeDirection: int = 0
    threeMonthsAgoChangePercent: str | None = None
    threeMonthsAgoChangeDirection: int = 0
    spread: str | None = None


class StockSector(AvanzaModel):
    """Stock sector classification."""

    id: int
    level: int
    name: str
    englishName: str
    highlightedName: str | None = None


class FundTag(AvanzaModel):
    """Fund classification tag."""

    title: str
    category: str
    tagCategory: str
    highlightedTitle: str | None = None


class SearchHit(AvanzaModel):
    """Individual search result from the Avanza API."""

    type: str
    title: str
    highlightedTitle: str
    description: str
    highlightedDescription: str
    path: str | None = None
    flagCode: str | None = None
    orderBookId: str | None = None  # May be None for certain instrument types
    urlSlugName: str
    tradeable: bool
    sellable: bool
    buyable: bool
    price: SearchPrice | None = None  # May be None for certain instrument types
    stockSectors: list[StockSector] = Field(default_factory=list)
    fundTags: list[FundTag] = Field(default_factory=list)
    marketPlaceName: str
    subType: str | None = None
    highlightedSubType: str = ""


class TypeFacet(AvanzaModel):
    """Facet count for an instrument type."""

    type: str
    count: int


class SearchFacets(AvanzaModel):
    """Search result facets with type counts."""

    types: list[TypeFacet]


class SearchFilter(AvanzaModel):
    """Applied search filters."""

    types: list[str] = Field(default_factory=list)


class SearchPagination(AvanzaModel):
    """Pagination information."""

    size: int
    # Using field alias since 'from' is a Python keyword
    from_: int = Field(alias="from")


class SearchResponse(AvanzaModel):
    """Complete search API response from Avanza."""

    totalNumberOfHits: int
    hits: list[SearchHit]
    searchQuery: str
    searchFilter: SearchFilter
    facets: SearchFacets
    pagination: SearchPagination
