"""Futures and forwards MCP tools."""

from typing import Literal

from fastmcp import Context

from .. import mcp
from ..client import AvanzaClient
from ..models.filter import SortBy
from ..models.future_forward import (
    FutureForwardMatrixFilter,
    FutureForwardMatrixRequest,
)
from ..services import MarketDataService


@mcp.tool()
async def list_futures_forwards(
    ctx: Context,
    underlying_instruments: list[str] | None = None,
    option_types: list[str] | None = None,
    end_dates: list[str] | None = None,
    offset: int = 0,
    limit: int = 20,
    sort_field: str = "strikePrice",
    sort_order: Literal["asc", "desc"] = "desc",
) -> dict:
    """List available futures and forward contracts.

    Retrieves a matrix/list of available futures and forward contracts,
    with optional filtering by underlying instruments, option types, and end dates.

    Args:
        ctx: MCP context for logging
        underlying_instruments: Optional list of underlying instrument IDs
        option_types: Optional list of option types to filter by
        end_dates: Optional list of end dates (YYYY-MM-DD format)
        offset: Number of results to skip (default: 0)
        limit: Maximum number of results (default: 20)
        sort_field: Field to sort by (default: "strikePrice")
        sort_order: Sort order "asc" or "desc" (default: "desc")

    Returns:
        List of available futures and forwards

    Examples:
        List all futures/forwards:
        >>> list_futures_forwards()

        Filter by underlying instrument:
        >>> list_futures_forwards(underlying_instruments=["19002"])
    """
    ctx.info("Listing futures/forwards")

    try:
        request = FutureForwardMatrixRequest(
            filter=FutureForwardMatrixFilter(
                underlyingInstruments=underlying_instruments or [],
                optionTypes=option_types or [],
                endDates=end_dates or [],
                callIndicators=[],
            ),
            offset=offset,
            limit=limit,
            sortBy=SortBy(field=sort_field, order=sort_order),
        )

        async with AvanzaClient() as client:
            service = MarketDataService(client)
            result = await service.list_futures_forwards(request)

        ctx.info("Retrieved futures/forwards list")
        return result.model_dump(by_alias=True, exclude_none=True)

    except Exception as e:
        ctx.error(f"Failed to list futures/forwards: {str(e)}")
        raise


@mcp.tool()
async def get_future_forward_info(ctx: Context, instrument_id: str) -> dict:
    """Get detailed information about a specific future or forward contract.

    Provides comprehensive contract data including expiration date, underlying
    instrument, contract specifications, and current pricing.

    Args:
        ctx: MCP context for logging
        instrument_id: Avanza future/forward ID

    Returns:
        Detailed contract information

    Examples:
        Get contract info:
        >>> get_future_forward_info(instrument_id="2224452")
    """
    ctx.info(f"Fetching future/forward info for ID: {instrument_id}")

    try:
        async with AvanzaClient() as client:
            service = MarketDataService(client)
            info = await service.get_future_forward_info(instrument_id)

        ctx.info(f"Retrieved info for: {info.name}")
        return info.model_dump(by_alias=True, exclude_none=True)

    except Exception as e:
        ctx.error(f"Failed to fetch future/forward info: {str(e)}")
        raise


@mcp.tool()
async def get_future_forward_details(ctx: Context, instrument_id: str) -> dict:
    """Get extended details about a specific future/forward contract.

    Provides additional detailed information beyond basic contract info.

    Args:
        ctx: MCP context for logging
        instrument_id: Avanza future/forward ID

    Returns:
        Extended contract details

    Examples:
        Get detailed info:
        >>> get_future_forward_details(instrument_id="2224452")
    """
    ctx.info(f"Fetching future/forward details for ID: {instrument_id}")

    try:
        async with AvanzaClient() as client:
            service = MarketDataService(client)
            details = await service.get_future_forward_details(instrument_id)

        ctx.info("Retrieved future/forward details")
        return details.model_dump(by_alias=True, exclude_none=True)

    except Exception as e:
        ctx.error(f"Failed to fetch future/forward details: {str(e)}")
        raise


@mcp.tool()
async def get_future_forward_filter_options(ctx: Context) -> dict:
    """Get available filter options for futures and forwards.

    Returns the available filter options including underlying instruments,
    option types, end dates, and other filterable parameters.

    Args:
        ctx: MCP context for logging

    Returns:
        Available filter options for futures/forwards

    Examples:
        Get filter options:
        >>> get_future_forward_filter_options()
    """
    ctx.info("Fetching future/forward filter options")

    try:
        async with AvanzaClient() as client:
            service = MarketDataService(client)
            options = await service.get_future_forward_filter_options()

        ctx.info("Retrieved filter options")
        return options

    except Exception as e:
        ctx.error(f"Failed to fetch filter options: {str(e)}")
        raise
