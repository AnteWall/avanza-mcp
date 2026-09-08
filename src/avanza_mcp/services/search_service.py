"""Search service for finding financial instruments."""

from pydantic import validate_call

from ..client.base import AvanzaClient
from ..client.endpoints import PublicEndpoint
from ..models.common import InstrumentType, SearchLimit, SearchQuery
from ..models.search import (
    InstrumentHit,
    InstrumentSearch,
    SearchFilter,
    SearchPagination,
    SearchRequest,
    SearchResponse,
)


class SearchService:
    """Service for searching financial instruments."""

    def __init__(self, client: AvanzaClient) -> None:
        """Initialize search service.

        Args:
            client: Avanza HTTP client
        """
        self._client = client

    @validate_call
    async def search(
        self,
        query: SearchQuery,
        instrument_type: str | InstrumentType | None = None,
        limit: SearchLimit = 10,
    ) -> InstrumentSearch:
        """Filter one bounded candidate page before applying the output limit."""
        type_value = instrument_type.upper() if instrument_type else "ALL"
        financial_types = {
            item.value for item in InstrumentType if item != InstrumentType.FAQ
        }
        if type_value != "ALL" and type_value not in financial_types:
            raise ValueError("Unknown financial instrument type")
        requested_types = (
            {"ETF", "EXCHANGE_TRADED_FUND"}
            if type_value in {"ETF", "EXCHANGE_TRADED_FUND"}
            else {type_value}
        )
        # Only STOCK/FUND filters were live-verified; other types stay local.
        payload = SearchRequest(
            query=query,
            searchFilter=SearchFilter(
                types=[type_value] if type_value in {"STOCK", "FUND"} else []
            ),
            pagination=SearchPagination(size=50, from_=0),
        )
        response = await self._client.post(
            PublicEndpoint.SEARCH.value,
            json=payload.model_dump(by_alias=True),
        )
        parsed = SearchResponse.model_validate(response)
        candidates = parsed.hits[:50]
        hits = [
            InstrumentHit(
                order_book_id=hit.orderBookId,
                name=hit.title,
                type=hit.type,
                exchange=hit.marketPlaceName,
                isin=hit.isin,
                currency=hit.currency
                if hit.currency is not None
                else (hit.price.currency if hit.price else None),
            )
            for hit in candidates
            if hit.type in financial_types
            and (type_value == "ALL" or hit.type in requested_types)
            and hit.orderBookId is not None
        ]
        return InstrumentSearch(
            totalNumberOfHits=len(hits),
            candidatesExamined=len(candidates),
            upstreamTotalNumberOfHits=parsed.totalNumberOfHits,
            hits=hits[:limit],
            searchQuery=parsed.searchQuery,
            returned=len(hits[:limit]),
        )
