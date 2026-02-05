"""Warrant MCP tools."""

from fastmcp import Context

from .. import mcp
from ..client import AvanzaClient
from ..models.filter import SortBy
from ..models.warrant import WarrantFilter, WarrantFilterRequest
from ..services import MarketDataService


@mcp.tool()
async def filter_warrants(
    ctx: Context,
    offset: int = 0,
    limit: int = 20,
    directions: list[str] | None = None,
    sub_types: list[str] | None = None,
    issuers: list[str] | None = None,
    underlying_instruments: list[str] | None = None,
    sort_field: str = "name",
    sort_order: str = "asc",
) -> dict:
    """Filter and list warrants (turbos, mini futures, etc.) with pagination.

    Search through available warrants with filters for direction, sub-type
    (TURBO, MINI, etc.), issuer, and underlying instrument.

    Args:
        ctx: MCP context for logging
        offset: Number of results to skip (default: 0)
        limit: Maximum number of results (default: 20, max: 100)
        directions: Filter by direction, e.g., ["long"], ["short"]
        sub_types: Filter by sub-type, e.g., ["TURBO"], ["MINI"]
        issuers: Filter by issuer, e.g., ["Societe Generale"]
        underlying_instruments: Filter by underlying instrument IDs
        sort_field: Field to sort by (default: "name")
        sort_order: Sort order "asc" or "desc" (default: "asc")

    Returns:
        Filtered list of warrants with stop loss, underlying instrument, etc.

    Examples:
        List turbo warrants:
        >>> filter_warrants(sub_types=["TURBO"])

        Find long warrants from specific issuer:
        >>> filter_warrants(directions=["long"], issuers=["Societe Generale"])
    """
    ctx.info(f"Filtering warrants: offset={offset}, limit={limit}")

    try:
        filter_req = WarrantFilterRequest(
            filter=WarrantFilter(
                directions=directions or [],
                subTypes=sub_types or [],
                issuers=issuers or [],
                underlyingInstruments=underlying_instruments or [],
            ),
            offset=offset,
            limit=min(limit, 100),
            sortBy=SortBy(field=sort_field, order=sort_order),
        )

        async with AvanzaClient() as client:
            service = MarketDataService(client)
            result = await service.filter_warrants(filter_req)

        ctx.info(f"Retrieved {len(result.warrants)} warrants")
        return result.model_dump(by_alias=True, exclude_none=True)

    except Exception as e:
        ctx.error(f"Failed to filter warrants: {str(e)}")
        raise


@mcp.tool()
async def get_warrant_info(ctx: Context, instrument_id: str) -> dict:
    """Get detailed information about a specific warrant.

    Provides comprehensive warrant data including strike price, barrier level,
    stop loss, underlying instrument details, and current pricing.

    Args:
        ctx: MCP context for logging
        instrument_id: Avanza warrant ID

    Returns:
        Detailed warrant information with strike, barrier, underlying, etc.

    Examples:
        Get warrant info:
        >>> get_warrant_info(instrument_id="2267542")
    """
    ctx.info(f"Fetching warrant info for ID: {instrument_id}")

    try:
        async with AvanzaClient() as client:
            service = MarketDataService(client)
            warrant = await service.get_warrant_info(instrument_id)

        ctx.info(f"Retrieved info for: {warrant.name}")
        return warrant.model_dump(by_alias=True, exclude_none=True)

    except Exception as e:
        ctx.error(f"Failed to fetch warrant info: {str(e)}")
        raise


@mcp.tool()
async def get_warrant_details(ctx: Context, instrument_id: str) -> dict:
    """Get extended details about a specific warrant.

    Provides additional detailed information beyond basic warrant info.

    Args:
        ctx: MCP context for logging
        instrument_id: Avanza warrant ID

    Returns:
        Extended warrant details

    Examples:
        Get detailed info:
        >>> get_warrant_details(instrument_id="2267542")
    """
    ctx.info(f"Fetching warrant details for ID: {instrument_id}")

    try:
        async with AvanzaClient() as client:
            service = MarketDataService(client)
            details = await service.get_warrant_details(instrument_id)

        ctx.info("Retrieved warrant details")
        return details.model_dump(by_alias=True, exclude_none=True)

    except Exception as e:
        ctx.error(f"Failed to fetch warrant details: {str(e)}")
        raise
