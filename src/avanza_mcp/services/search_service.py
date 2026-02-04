"""Search service for finding financial instruments."""

from typing import Any

from ..client.base import AvanzaClient
from ..client.endpoints import PublicEndpoint
from ..models.common import InstrumentType
from ..models.search import SearchResponse


class SearchService:
    """Service for searching financial instruments."""

    def __init__(self, client: AvanzaClient) -> None:
        """Initialize search service.

        Args:
            client: Avanza HTTP client
        """
        self._client = client

    async def search(
        self,
        query: str,
        instrument_type: str | InstrumentType | None = None,
        limit: int = 10,
    ) -> SearchResponse:
        """Search for financial instruments.

        Args:
            query: Search term (company name, ticker, ISIN)
            instrument_type: Optional type filter (stock, fund, etc.)
            limit: Maximum number of results

        Returns:
            Complete search response with hits, facets, and pagination
        """
        # Build search payload
        payload: dict[str, Any] = {
            "query": query,
            "limit": limit,
        }

        # Add instrument type filter if specified
        if instrument_type and instrument_type != "all":
            if isinstance(instrument_type, str):
                # Convert string to InstrumentType enum
                try:
                    type_value = InstrumentType[instrument_type.upper()].value
                except KeyError:
                    type_value = instrument_type.upper()
            else:
                type_value = instrument_type.value

            payload["instrumentType"] = type_value

        # Make search request
        response = await self._client.post(
            PublicEndpoint.SEARCH.value,
            json=payload,
        )

        # Parse and return typed response
        return SearchResponse.model_validate(response)
