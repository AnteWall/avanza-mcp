"""ETF selection and detail tools."""

from typing import Literal

from fastmcp import Context

from .. import mcp
from ..models.common import Limit, Offset, OrderBookId
from ..models.etf import (
    ETFDetails,
    ETFFilter,
    ETFFilterRequest,
    ETFFilterResponse,
    ETFInfo,
)
from ..models.filter import SortBy
from ..services import MarketDataService
from ._helpers import READ_ONLY, api_errors


@mcp.tool(annotations=READ_ONLY)
async def filter_etfs(
    ctx: Context,
    offset: Offset = 0,
    limit: Limit = 20,
    asset_categories: list[str] | None = None,
    sub_categories: list[str] | None = None,
    exposures: list[str] | None = None,
    risk_scores: list[str] | None = None,
    directions: list[str] | None = None,
    issuers: list[str] | None = None,
    currency_codes: list[str] | None = None,
    sort_field: str = "numberOfOwners",
    sort_order: Literal["asc", "desc"] = "desc",
) -> ETFFilterResponse:
    """Select ETFs by upstream filters, with server-side pagination.

    Filter vocabulary is upstream-defined; inspect returned filterOptions rather
    than guessing labels. Use get_etf_info for a selected orderbookId.
    """
    request = ETFFilterRequest(
        filter=ETFFilter(
            assetCategories=asset_categories or [],
            subCategories=sub_categories or [],
            exposures=exposures or [],
            riskScores=risk_scores or [],
            directions=directions or [],
            issuers=issuers or [],
            currencyCodes=currency_codes or [],
        ),
        offset=offset,
        limit=limit,
        sortBy=SortBy(field=sort_field, order=sort_order),
    )
    with api_errors():
        return await MarketDataService(ctx.lifespan_context["client"]).filter_etfs(
            request
        )


@mcp.tool(annotations=READ_ONLY)
async def get_etf_info(ctx: Context, order_book_id: OrderBookId) -> ETFInfo:
    """Get ETF identity, listing and latest available quote; not guaranteed real-time."""
    with api_errors():
        return await MarketDataService(ctx.lifespan_context["client"]).get_etf_info(
            order_book_id
        )


@mcp.tool(annotations=READ_ONLY)
async def get_etf_details(ctx: Context, order_book_id: OrderBookId) -> ETFDetails:
    """Get extended ETF details beyond info. Detail fields are upstream-defined and flexible."""
    with api_errors():
        return await MarketDataService(ctx.lifespan_context["client"]).get_etf_details(
            order_book_id
        )
