"""Search-related MCP tools."""

from typing import Literal

from fastmcp import Context

from .. import mcp
from ..client import AvanzaClient
from ..services import SearchService


@mcp.tool()
async def search_instruments(
    ctx: Context,
    query: str,
    instrument_type: Literal[
        "stock", "fund", "etf", "certificate", "warrant", "all"
    ] = "all",
    limit: int = 10,
) -> dict:
    """Search for financial instruments on Avanza.

    Searches across stocks, funds, ETFs, certificates, and warrants.
    Returns detailed search results including price info, sectors, and metadata.

    Args:
        ctx: MCP context for logging
        query: Search term (company name, ticker symbol, or ISIN)
        instrument_type: Type of instrument to search for. Options:
            - "stock": Stocks only
            - "fund": Mutual funds only
            - "etf": ETFs only
            - "certificate": Certificates only
            - "warrant": Warrants only
            - "all": All instrument types (default)
        limit: Maximum number of results to return (1-50, default: 10)

    Returns:
        Search response with:
        - totalNumberOfHits: Total matching results
        - hits: Array of search results with:
            - orderBookId: Unique ID
            - type: Instrument type (STOCK, FUND, etc.)
            - title: Name
            - price: Price information
            - marketPlaceName: Exchange/market
            - And more details...
        - facets: Type breakdowns with counts
        - searchQuery: The query that was executed

    Examples:
        Search for Volvo stock:
        >>> search_instruments(query="Volvo", instrument_type="stock", limit=5)

        Search for any instrument matching "Global":
        >>> search_instruments(query="Global", instrument_type="all", limit=10)
    """
    ctx.info(f"Searching for '{query}' (type: {instrument_type}, limit: {limit})")

    try:
        # Validate limit
        limit = max(1, min(limit, 50))

        async with AvanzaClient() as client:
            service = SearchService(client)
            response = await service.search(
                query=query,
                instrument_type=instrument_type if instrument_type != "all" else None,
                limit=limit,
            )

        ctx.info(f"Found {response.totalNumberOfHits} total hits, returning {len(response.hits)} results")

        # Return the full response as dict
        return response.model_dump(by_alias=True)

    except Exception as e:
        ctx.error(f"Search failed: {str(e)}")
        raise


@mcp.tool()
async def get_instrument_by_order_book_id(
    ctx: Context,
    order_book_id: str,
) -> dict | None:
    """Look up a financial instrument by its order book ID.

    The order book ID is the unique identifier returned from search results.

    Args:
        ctx: MCP context for logging
        order_book_id: Order book ID to search for

    Returns:
        First matching search hit if found, None otherwise

    Examples:
        Look up by order book ID:
        >>> get_instrument_by_order_book_id(order_book_id="878733")
    """
    ctx.info(f"Looking up instrument with order book ID: {order_book_id}")

    try:
        async with AvanzaClient() as client:
            service = SearchService(client)
            response = await service.search(query=order_book_id, limit=1)

        if response.hits:
            hit = response.hits[0]
            ctx.info(f"Found: {hit.title}")
            return hit.model_dump()
        else:
            ctx.info("No instrument found with that order book ID")
            return None

    except Exception as e:
        ctx.error(f"Lookup failed: {str(e)}")
        raise
