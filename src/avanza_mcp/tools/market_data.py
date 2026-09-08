"""Stock market data tools. Latest available data is not guaranteed real-time."""

from fastmcp import Context

from .. import mcp
from ..models.common import Limit, Offset, OrderBookId, StockPeriod
from ..models.contracts import (
    AnalysisPage,
    AnalysisSection,
    BrokerSummaries,
    FinancialSection,
    MetricName,
    StockChartPage,
    TradesPage,
)
from ..models.fund import FundInfo
from ..models.stock import MarketplaceInfo, OrderDepth, Quote, StockInfo
from ..services import MarketDataService
from ._helpers import READ_ONLY, analysis_page, api_errors, page_metadata


@mcp.tool(annotations=READ_ONLY)
async def get_stock_info(ctx: Context, order_book_id: OrderBookId) -> StockInfo:
    """Get stock identity, listing, company, ratios and latest available quote.

    Use search_instruments to select an order_book_id. For pricing only, prefer
    get_stock_quote. Data is not guaranteed real-time.
    """
    with api_errors():
        return await MarketDataService(ctx.lifespan_context["client"]).get_stock_info(
            order_book_id
        )


@mcp.tool(annotations=READ_ONLY)
async def get_fund_info(ctx: Context, order_book_id: OrderBookId) -> FundInfo:
    """Get fund identity, latest available NAV, fees, risk and allocations.

    Missing currency and tradeability remain unknown. Not guaranteed real-time.
    Use get_fund_holdings for allocations only, get_fund_chart for raw history.
    """
    with api_errors():
        return await MarketDataService(ctx.lifespan_context["client"]).get_fund_info(
            order_book_id
        )


@mcp.tool(annotations=READ_ONLY)
async def get_stock_chart(
    ctx: Context,
    order_book_id: OrderBookId,
    time_period: StockPeriod = "one_year",
    offset: Offset = 0,
    limit: Limit = 100,
) -> StockChartPage:
    """Get a page of raw stock OHLC points in source order, without aggregation.

    Offset/limit slice the selected period, not a date range. Metadata describes
    the full upstream period. Upstream fields live under data, isolated from wrapper
    pagination keys. Latest available data is not guaranteed real-time.
    """
    with api_errors():
        chart = await MarketDataService(ctx.lifespan_context["client"]).get_chart_data(
            order_book_id, time_period
        )
    return StockChartPage(
        data=chart.model_copy(update={"ohlc": chart.ohlc[offset : offset + limit]}),
        pagination=page_metadata(len(chart.ohlc), offset, limit),
    )


@mcp.tool(annotations=READ_ONLY)
async def get_orderbook(ctx: Context, order_book_id: OrderBookId) -> OrderDepth:
    """Get latest available buy/sell depth; empty levels are valid. Not guaranteed real-time."""
    with api_errors():
        return await MarketDataService(ctx.lifespan_context["client"]).get_order_depth(
            order_book_id
        )


@mcp.tool(annotations=READ_ONLY)
async def get_stock_analysis(
    ctx: Context,
    order_book_id: OrderBookId,
    metric: MetricName,
    selection: AnalysisSection = "stockKeyRatiosByYear",
    offset: Offset = 0,
    limit: Limit = 20,
) -> AnalysisPage:
    """Get one named metric within a ratio section, paginated in source order.

    Select annual, quarterly, quarter-over-quarter, TTM, or company annual ratios.
    For dividends or financial statements use the dedicated tools. The selected
    section and metric names are retained inside data; absent fields are omitted.
    Example metric: priceEarningsRatio for stock ratios, earningsPerShare for company
    ratios. available_metrics lists the selected section's names. Sibling series and
    keyRatios summary sections are intentionally excluded, not aggregated.
    Units and record details are upstream-defined; no normalization is applied.
    """
    with api_errors():
        analysis = await MarketDataService(
            ctx.lifespan_context["client"]
        ).get_stock_analysis(order_book_id, selection)
    return analysis_page(analysis, selection, metric, offset, limit)


@mcp.tool(annotations=READ_ONLY)
async def get_stock_quote(ctx: Context, order_book_id: OrderBookId) -> Quote:
    """Get latest available stock prices and trading data, without company details.

    Not guaranteed real-time; inspect isRealTime and upstream timestamps.
    Null is unknown; zero is a reported value.
    """
    with api_errors():
        return await MarketDataService(ctx.lifespan_context["client"]).get_stock_quote(
            order_book_id
        )


@mcp.tool(annotations=READ_ONLY)
async def get_marketplace_info(
    ctx: Context, order_book_id: OrderBookId
) -> MarketplaceInfo:
    """Get latest available marketplace status and trading hours."""
    with api_errors():
        return await MarketDataService(
            ctx.lifespan_context["client"]
        ).get_marketplace_info(order_book_id)


@mcp.tool(annotations=READ_ONLY)
async def get_recent_trades(
    ctx: Context,
    order_book_id: OrderBookId,
    offset: Offset = 0,
    limit: Limit = 20,
) -> TradesPage:
    """Page through the latest available trade snapshot in upstream order.

    Not a complete trade history or guaranteed real-time feed. Separate page
    requests may observe a changed snapshot; total is the current source count.
    """
    with api_errors():
        trades = await MarketDataService(ctx.lifespan_context["client"]).get_trades(
            order_book_id
        )
    return TradesPage(
        trades=trades[offset : offset + limit],
        pagination=page_metadata(len(trades), offset, limit),
    )


@mcp.tool(annotations=READ_ONLY)
async def get_broker_trade_summary(
    ctx: Context, order_book_id: OrderBookId
) -> BrokerSummaries:
    """Get upstream broker buy/sell summaries; these do not identify investor types."""
    with api_errors():
        summaries = await MarketDataService(
            ctx.lifespan_context["client"]
        ).get_broker_trades(order_book_id)
    return BrokerSummaries(summaries=summaries)


@mcp.tool(annotations=READ_ONLY)
async def get_dividends(
    ctx: Context,
    order_book_id: OrderBookId,
    metric: MetricName,
    offset: Offset = 0,
    limit: Limit = 20,
) -> AnalysisPage:
    """Page one dividendsByYear metric: dividendPerShare, directYieldRatio or dividendPayoutRatio.

    data preserves the upstream section name. Missing data is omitted, not an
    empty history. Records contain financialYear, reportType, value and optional
    date, not inferred ex/payment dates. available_metrics lists names only; sibling
    series are excluded. Units and scales are upstream-defined.
    """
    with api_errors():
        data = await MarketDataService(ctx.lifespan_context["client"]).get_dividends(
            order_book_id
        )
    return analysis_page(data, "dividendsByYear", metric, offset, limit)


@mcp.tool(annotations=READ_ONLY)
async def get_company_financials(
    ctx: Context,
    order_book_id: OrderBookId,
    metric: MetricName,
    selection: FinancialSection = "companyFinancialsByYear",
    offset: Offset = 0,
    limit: Limit = 20,
) -> AnalysisPage:
    """Page one metric in an annual, quarterly, TTM or quarter-only financial section.

    data preserves the selected upstream field name and full raw records.
    Verified metric names include sales, netProfit, profitMargin, totalAssets,
    totalLiabilities and debtToEquityRatio. available_metrics lists names, not sibling
    series. Missing sections are omitted, not fabricated. No unit conversions are made.
    """
    with api_errors():
        data = await MarketDataService(
            ctx.lifespan_context["client"]
        ).get_company_financials(order_book_id, selection)
    return analysis_page(data, selection, metric, offset, limit)
