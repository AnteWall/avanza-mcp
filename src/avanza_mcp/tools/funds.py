"""Fund-specific tools using the shared lifespan client."""

from fastmcp import Context

from .. import mcp
from ..models.common import FundPeriod, Limit, Offset, OrderBookId
from ..models.contracts import FundChartPage, FundHoldings, FundPeriods
from ..models.fund import FundDescription, FundSustainability
from ..services import MarketDataService
from ._helpers import READ_ONLY, api_errors, page_metadata


@mcp.tool(annotations=READ_ONLY)
async def get_fund_sustainability(
    ctx: Context, order_book_id: OrderBookId
) -> FundSustainability:
    """Get latest available fund ESG and sustainability data, not a real-time assessment."""
    with api_errors():
        return await MarketDataService(
            ctx.lifespan_context["client"]
        ).get_fund_sustainability(order_book_id)


@mcp.tool(annotations=READ_ONLY)
async def get_fund_chart(
    ctx: Context,
    order_book_id: OrderBookId,
    time_period: FundPeriod = "three_years",
    offset: Offset = 0,
    limit: Limit = 100,
) -> FundChartPage:
    """Get a page of raw fund dataSerie points in source order, without aggregation.

    x/y values retain upstream meaning; y is not assumed to be NAV or a return.
    Offset/limit slice the chosen period; dates describe the full source period.
    """
    with api_errors():
        chart = await MarketDataService(ctx.lifespan_context["client"]).get_fund_chart(
            order_book_id, time_period
        )
    return FundChartPage(
        data=chart.model_copy(
            update={"dataSerie": chart.dataSerie[offset : offset + limit]}
        ),
        pagination=page_metadata(len(chart.dataSerie), offset, limit),
    )


@mcp.tool(annotations=READ_ONLY)
async def get_fund_chart_periods(
    ctx: Context, order_book_id: OrderBookId
) -> FundPeriods:
    """Get available fund performance periods, rather than individual chart points.

    startDate is the source period start date. change retains its upstream scale;
    do not assume it uses the same scale as fund-guide development fields.
    """
    with api_errors():
        periods = await MarketDataService(
            ctx.lifespan_context["client"]
        ).get_fund_chart_periods(order_book_id)
    return FundPeriods(periods=periods)


@mcp.tool(annotations=READ_ONLY)
async def get_fund_description(
    ctx: Context, order_book_id: OrderBookId
) -> FundDescription:
    """Get the fund's investment description and category explanation."""
    with api_errors():
        return await MarketDataService(
            ctx.lifespan_context["client"]
        ).get_fund_description(order_book_id)


@mcp.tool(annotations=READ_ONLY)
async def get_fund_holdings(ctx: Context, order_book_id: OrderBookId) -> FundHoldings:
    """Get reported country, sector and holding allocations, not a complete position ledger.

    portfolioDate is the source portfolio date, not retrieval time. Missing dates
    are not inferred. Missing allocations are null; reported empty arrays stay [].
    Allocation values are returned without unit conversion.
    """
    with api_errors():
        fund = await MarketDataService(ctx.lifespan_context["client"]).get_fund_info(
            order_book_id
        )
    return FundHoldings(
        countryChartData=fund.country_chart_data,
        sectorChartData=fund.sector_chart_data,
        holdingChartData=fund.holding_chart_data,
        portfolioDate=fund.portfolio_date,
    )
