"""Additional instrument data tools."""

from fastmcp import Context

from .. import mcp
from ..models.common import Limit, MarketmakerPeriod, Offset, OrderBookId
from ..models.contracts import MarketmakerChartPage, OwnersPage, ShortSellingPage
from ..services import MarketDataService
from ._helpers import READ_ONLY, api_errors, page_metadata


@mcp.tool(annotations=READ_ONLY)
async def get_number_of_owners(
    ctx: Context,
    order_book_id: OrderBookId,
    offset: Offset = 0,
    limit: Limit = 20,
) -> OwnersPage:
    """Page Avanza ownersPoints in source order and preserve the full historySummary.

    data contains upstream fields, not a fabricated top-level owner count. Summary
    fields describe the full source history, not this page. Not market-wide ownership.
    """
    with api_errors():
        history = await MarketDataService(
            ctx.lifespan_context["client"]
        ).get_number_of_owners(order_book_id)
    return OwnersPage(
        data=history.model_copy(
            update={"ownersPoints": history.ownersPoints[offset : offset + limit]}
        ),
        pagination=page_metadata(len(history.ownersPoints), offset, limit),
    )


@mcp.tool(annotations=READ_ONLY)
async def get_short_selling(
    ctx: Context,
    order_book_id: OrderBookId,
    offset: Offset = 0,
    limit: Limit = 20,
) -> ShortSellingPage:
    """Page shortSellingHistory in source order; timestamp/ratio values are not converted.

    data preserves upstream fields. A page is not the full history or a latest-value
    summary. Offset zero is the beginning of source order, not necessarily newest.
    """
    with api_errors():
        history = await MarketDataService(
            ctx.lifespan_context["client"]
        ).get_short_selling(order_book_id)
    return ShortSellingPage(
        data=history.model_copy(
            update={
                "shortSellingHistory": history.shortSellingHistory[
                    offset : offset + limit
                ]
            }
        ),
        pagination=page_metadata(len(history.shortSellingHistory), offset, limit),
    )


@mcp.tool(annotations=READ_ONLY)
async def get_marketmaker_chart(
    ctx: Context,
    order_book_id: OrderBookId,
    time_period: MarketmakerPeriod = "today",
    offset: Offset = 0,
    limit: Limit = 100,
) -> MarketmakerChartPage:
    """Get raw OHLC and market-maker data for traded products, not stock/fund charts.

    Both arrays are independently sliced with the same offset/limit in source
    order; their metadata counts are separate. No point alignment, aggregation
    or unit conversion is inferred. Upstream fields are under data, separate from
    wrapper pagination keys. Not guaranteed real-time.
    """
    with api_errors():
        chart = await MarketDataService(
            ctx.lifespan_context["client"]
        ).get_marketmaker_chart(order_book_id, time_period)
    updates = {"ohlc": chart.ohlc[offset : offset + limit]}
    maker_page = None
    if chart.marketMaker is not None:
        updates["marketMaker"] = chart.marketMaker[offset : offset + limit]
        maker_page = page_metadata(len(chart.marketMaker), offset, limit)
    return MarketmakerChartPage(
        data=chart.model_copy(update=updates),
        pagination=page_metadata(len(chart.ohlc), offset, limit),
        marketMakerPagination=maker_page,
    )
