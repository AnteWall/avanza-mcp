"""Search result models matching Avanza API response structure."""

from pydantic import BaseModel, Field, field_validator

from .common import MODEL_CONFIG as MODEL_CONFIG, AvanzaModel, OrderBookId, SearchQuery


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
    highlightedTitle: str | None = None
    description: str | None = None
    highlightedDescription: str | None = None
    path: str | None = None
    flagCode: str | None = None
    orderBookId: str | None = None  # May be None for certain instrument types
    urlSlugName: str | None = None
    tradeable: bool | None = None
    sellable: bool | None = None
    buyable: bool | None = None
    price: SearchPrice | None = None  # May be None for certain instrument types
    stockSectors: list[StockSector] = Field(default_factory=list)
    fundTags: list[FundTag] = Field(default_factory=list)
    marketPlaceName: str | None = None
    isin: str | None = None
    currency: str | None = None
    subType: str | None = None
    highlightedSubType: str = ""

    @field_validator("orderBookId", mode="before")
    @classmethod
    def valid_order_book_id(cls, value: object) -> str | None:
        if isinstance(value, str) and value.isascii() and value.isdecimal():
            return value
        return None


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
    searchFilter: SearchFilter | None = None
    facets: SearchFacets | None = None
    pagination: SearchPagination | None = None


class SearchRequest(BaseModel):
    """Verified public filtered-search POST body (not URL query parameters)."""

    query: SearchQuery
    searchFilter: SearchFilter
    pagination: SearchPagination


class InstrumentHit(BaseModel):
    """Curated instrument identity; presentation and highlighting are excluded."""

    order_book_id: OrderBookId
    name: str
    type: str
    exchange: str | None
    isin: str | None = None
    currency: str | None = None


class InstrumentSearch(BaseModel):
    totalNumberOfHits: int = Field(
        description="Valid matching instruments in the examined candidate page, before limit; not a full-universe total."
    )
    candidatesExamined: int = Field(
        description="Number of upstream hits examined, including discarded hits; at most 50."
    )
    upstreamTotalNumberOfHits: int = Field(
        description="Upstream total before local validation/filtering; may include FAQ or other types."
    )
    hits: list[InstrumentHit]
    searchQuery: str
    returned: int
