"""Aggregated leveraged-instrument screen."""

from __future__ import annotations

from typing import Annotated, Literal

from fastmcp import Context
from pydantic import Field

from .. import mcp
from ..models.common import OrderBookId
from ..models.leveraged import LeveragedScreenResponse
from ..services.leveraged_screen_service import LeveragedScreenService
from ._helpers import READ_ONLY, api_errors

MaxPerType = Annotated[
    int,
    Field(
        ge=1,
        le=200,
        description="Maximum candidates to collect per product family.",
    ),
]


@mcp.tool(annotations=READ_ONLY)
async def screen_leveraged_instruments(
    ctx: Context,
    underlying_order_book_id: OrderBookId,
    direction: Literal["long", "short"],
    product_types: list[Literal["certificate", "warrant"]] | None = None,
    max_per_type: MaxPerType = 100,
) -> LeveragedScreenResponse:
    """Screen certificates and warrants for one verified underlying in one bounded call.

    Product families are fetched concurrently and internally paginated up to
    max_per_type each. Discovery facts include leverage, spread, bid/ask,
    turnover, issuer and stop-loss when the upstream filter supplies them.
    Discovery prices are not execution-verified.
    """
    selected = product_types or ["certificate", "warrant"]
    with api_errors():
        return await LeveragedScreenService(
            ctx.lifespan_context["client"]
        ).screen(
            underlying_order_book_id,
            direction,
            selected,
            max_per_type,
        )
