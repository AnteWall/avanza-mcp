"""Futures and forwards selection and detail tools."""

from datetime import date
from typing import Any, Literal

from fastmcp import Context

from .. import mcp
from ..models.common import Limit, Offset, OrderBookId
from ..models.filter import SortBy
from ..models.future_forward import (
    FutureForwardDetails,
    FutureForwardInfo,
    FutureForwardMatrixFilter,
    FutureForwardMatrixRequest,
    FutureForwardMatrixResponse,
)
from ..services import MarketDataService
from ._helpers import READ_ONLY, api_errors


@mcp.tool(annotations=READ_ONLY)
async def list_futures_forwards(
    ctx: Context,
    underlying_instruments: list[OrderBookId] | None = None,
    option_types: list[str] | None = None,
    end_dates: list[date] | None = None,
    offset: Offset = 0,
    limit: Limit = 20,
    sort_field: str = "strikePrice",
    sort_order: Literal["asc", "desc"] = "desc",
) -> FutureForwardMatrixResponse:
    """Select futures/forwards with server-side pagination and ISO YYYY-MM-DD end dates.

    Use get_future_forward_filter_options for current filter vocabulary. The
    matrix response retains flexible upstream fields, not an invented flat schema.
    """
    request = FutureForwardMatrixRequest(
        filter=FutureForwardMatrixFilter(
            underlyingInstruments=underlying_instruments or [],
            optionTypes=option_types or [],
            endDates=[value.isoformat() for value in end_dates or []],
            callIndicators=[],
        ),
        offset=offset,
        limit=limit,
        sortBy=SortBy(field=sort_field, order=sort_order),
    )
    with api_errors():
        return await MarketDataService(
            ctx.lifespan_context["client"]
        ).list_futures_forwards(request)


@mcp.tool(annotations=READ_ONLY)
async def get_future_forward_info(
    ctx: Context, order_book_id: OrderBookId
) -> FutureForwardInfo:
    """Get contract identity and latest available market data, not guaranteed real-time."""
    with api_errors():
        return await MarketDataService(
            ctx.lifespan_context["client"]
        ).get_future_forward_info(order_book_id)


@mcp.tool(annotations=READ_ONLY)
async def get_future_forward_details(
    ctx: Context, order_book_id: OrderBookId
) -> FutureForwardDetails:
    """Get extended contract details beyond info; detail fields are intentionally flexible."""
    with api_errors():
        return await MarketDataService(
            ctx.lifespan_context["client"]
        ).get_future_forward_details(order_book_id)


@mcp.tool(annotations=READ_ONLY)
async def get_future_forward_filter_options(ctx: Context) -> dict[str, Any]:
    """Get current upstream filter options before selecting futures/forwards.

    Option names, values and nested detail fields are intentionally flexible.
    """
    with api_errors():
        return await MarketDataService(
            ctx.lifespan_context["client"]
        ).get_future_forward_filter_options()
