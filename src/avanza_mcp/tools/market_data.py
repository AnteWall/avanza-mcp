"""Market data MCP tools for stocks, funds, and other instruments."""

from fastmcp import Context

from .. import mcp
from ..client import AvanzaClient
from ..services import MarketDataService


@mcp.tool()
async def get_stock_info(
    ctx: Context,
    instrument_id: str,
) -> dict:
    """Get detailed information about a specific stock.

    Provides comprehensive stock data including current price, trading volume,
    market capitalization, valuation metrics (P/E, P/B ratios), dividend yield,
    and company description.

    Use search_instruments() first to find the instrument_id for a stock.

    Args:
        ctx: MCP context for logging
        instrument_id: Avanza instrument ID from search results

    Returns:
        Detailed stock information including:
        - quote: Current price, change, volume, trading data
        - company: Description, CEO, sector, market cap
        - key_ratios: P/E ratio, dividend yield, volatility, beta
        - Trading metadata: market, tradeable status

    Examples:
        Get info for Volvo B (ID from search):
        >>> get_stock_info(instrument_id="5479")
    """
    ctx.info(f"Fetching stock info for ID: {instrument_id}")

    try:
        async with AvanzaClient() as client:
            service = MarketDataService(client)
            stock_info = await service.get_stock_info(instrument_id)

        ctx.info(f"Retrieved info for: {stock_info.name}")
        return stock_info.model_dump(by_alias=True, exclude_none=True)

    except Exception as e:
        ctx.error(f"Failed to fetch stock info: {str(e)}")
        raise


@mcp.tool()
async def get_fund_info(
    ctx: Context,
    instrument_id: str,
) -> dict:
    """Get detailed information about a mutual fund.

    Provides comprehensive fund data including NAV (Net Asset Value), performance
    over various time periods, risk metrics, fees, and fund characteristics.

    Use search_instruments() with instrument_type="fund" to find fund IDs.

    Args:
        ctx: MCP context for logging
        instrument_id: Avanza fund ID from search results

    Returns:
        Detailed fund information including:
        - Basic info: name, ISIN, description, NAV
        - Performance: returns over 1w, 1m, 3m, YTD, 1y, 3y, 5y, 10y
        - Risk: risk level (1-7), standard deviation, Sharpe ratio
        - Fees: ongoing charges, entry/exit fees
        - Characteristics: fund company, type, category, AUM

    Examples:
        Get info for a specific fund:
        >>> get_fund_info(instrument_id="12345")
    """
    ctx.info(f"Fetching fund info for ID: {instrument_id}")

    try:
        async with AvanzaClient() as client:
            service = MarketDataService(client)
            fund_info = await service.get_fund_info(instrument_id)

        ctx.info(f"Retrieved info for: {fund_info.name}")
        return fund_info.model_dump(by_alias=True, exclude_none=True)

    except Exception as e:
        ctx.error(f"Failed to fetch fund info: {str(e)}")
        raise


@mcp.tool()
async def get_stock_chart(
    ctx: Context,
    instrument_id: str,
    time_period: str = "one_year",
) -> dict:
    """Get historical price chart data (OHLC) for a stock.

    Retrieves time series price data with Open, High, Low, Close values and volume.
    Perfect for charting and technical analysis.

    Args:
        ctx: MCP context for logging
        instrument_id: Avanza instrument ID
        time_period: Time period for chart data. Options:
            - "today": Intraday data for today
            - "one_week": Past week
            - "one_month": Past month
            - "three_months": Past 3 months
            - "this_year": Year to date
            - "one_year": Past year (default)
            - "three_years": Past 3 years
            - "five_years": Past 5 years

    Returns:
        Chart data with OHLC values:
        - ohlc: Array of data points with timestamp, open, high, low, close, volume
        - metadata: Chart metadata
        - from/to: Time range
        - previousClosingPrice: Previous closing price

    Examples:
        Get 1 year daily data:
        >>> get_stock_chart(instrument_id="5269", time_period="one_year")

        Get past week data:
        >>> get_stock_chart(instrument_id="5269", time_period="one_week")
    """
    ctx.info(f"Fetching chart data for ID: {instrument_id} (time_period={time_period})")

    try:
        async with AvanzaClient() as client:
            service = MarketDataService(client)
            chart_data = await service.get_chart_data(
                instrument_id=instrument_id,
                time_period=time_period,
            )

        data_points = len(chart_data.ohlc)
        ctx.info(f"Retrieved {data_points} OHLC data points")
        return chart_data.model_dump(by_alias=True, exclude_none=True)

    except Exception as e:
        ctx.error(f"Failed to fetch chart data: {str(e)}")
        raise


@mcp.tool()
async def get_orderbook(
    ctx: Context,
    instrument_id: str,
) -> dict:
    """Get real-time order book depth for an instrument.

    Shows current buy and sell orders with prices and volumes at each level.
    Useful for understanding market depth, liquidity, and bid-ask spread.

    Args:
        ctx: MCP context for logging
        instrument_id: Avanza instrument ID

    Returns:
        Order book depth data with:
        - receivedTime: Timestamp of order book data
        - levels: Array of price levels, each containing:
            - buySide: Buy order with price, volume, priceString
            - sellSide: Sell order with price, volume, priceString

    Examples:
        Get current order book:
        >>> get_orderbook(instrument_id="5269")
    """
    ctx.info(f"Fetching order book for ID: {instrument_id}")

    try:
        async with AvanzaClient() as client:
            service = MarketDataService(client)
            orderbook = await service.get_order_depth(instrument_id)

        levels_count = len(orderbook.levels)
        ctx.info(f"Retrieved order book with {levels_count} levels")
        return orderbook.model_dump(by_alias=True, exclude_none=True)

    except Exception as e:
        ctx.error(f"Failed to fetch order book: {str(e)}")
        raise


@mcp.tool()
async def get_stock_analysis(
    ctx: Context,
    instrument_id: str,
) -> dict:
    """Get detailed stock analysis with key financial ratios.

    Provides comprehensive financial analysis including key ratios grouped by:
    - Annual data (stockKeyRatiosByYear)
    - Quarterly data (stockKeyRatiosByQuarter)
    - Quarter-over-quarter comparisons (stockKeyRatiosByQuarterQuarter)
    - Trailing twelve months (TTM) data (stockKeyRatiosByQuarterTTM)
    - Company-level annual ratios (companyKeyRatiosByYear)

    Use search_instruments() first to find the instrument_id for a stock.

    Args:
        ctx: MCP context for logging
        instrument_id: Avanza instrument ID from search results

    Returns:
        Comprehensive analysis data with:
        - stockKeyRatiosByYear: Annual financial ratios
        - stockKeyRatiosByQuarter: Quarterly financial ratios
        - stockKeyRatiosByQuarterTTM: TTM financial ratios
        - stockKeyRatiosByQuarterQuarter: Q-o-Q comparisons
        - companyKeyRatiosByYear: Company-level annual metrics
        - And more detailed financial analysis data

    Examples:
        Get analysis for Volvo B (ID from search):
        >>> get_stock_analysis(instrument_id="5479")
    """
    ctx.info(f"Fetching stock analysis for ID: {instrument_id}")

    try:
        async with AvanzaClient() as client:
            service = MarketDataService(client)
            analysis = await service.get_stock_analysis(instrument_id)

        ctx.info(f"Retrieved analysis data")
        return analysis

    except Exception as e:
        ctx.error(f"Failed to fetch stock analysis: {str(e)}")
        raise


@mcp.tool()
async def get_stock_quote(
    ctx: Context,
    instrument_id: str,
) -> dict:
    """Get real-time stock quote with current pricing and trading data.

    Provides immediate price information including bid/ask spread, last trade,
    trading volumes, and real-time status. Lighter weight than get_stock_info.

    Args:
        ctx: MCP context for logging
        instrument_id: Avanza instrument ID from search results

    Returns:
        Real-time quote data with:
        - buy: Current buy (bid) price
        - sell: Current sell (ask) price
        - last: Last traded price
        - highest: Highest price today
        - lowest: Lowest price today
        - change: Price change
        - changePercent: Percentage change
        - totalValueTraded: Total value traded
        - totalVolumeTraded: Total volume traded
        - volumeWeightedAveragePrice: VWAP
        - isRealTime: Whether data is real-time

    Examples:
        Get current quote for a stock:
        >>> get_stock_quote(instrument_id="5269")
    """
    ctx.info(f"Fetching stock quote for ID: {instrument_id}")

    try:
        async with AvanzaClient() as client:
            service = MarketDataService(client)
            quote = await service.get_stock_quote(instrument_id)

        ctx.info(f"Retrieved quote: last={quote.last}, change={quote.changePercent}%")
        return quote.model_dump(by_alias=True, exclude_none=True)

    except Exception as e:
        ctx.error(f"Failed to fetch stock quote: {str(e)}")
        raise


@mcp.tool()
async def get_marketplace_info(
    ctx: Context,
    instrument_id: str,
) -> dict:
    """Get marketplace status and trading hours for an instrument.

    Provides information about whether the market is open, time remaining until close,
    and today's opening/closing times.

    Args:
        ctx: MCP context for logging
        instrument_id: Avanza instrument ID from search results

    Returns:
        Marketplace information with:
        - marketOpen: Boolean indicating if market is currently open
        - timeLeftMs: Milliseconds remaining until market close
        - openingTime: Today's market opening time
        - todayClosingTime: Today's market closing time
        - normalClosingTime: Standard market closing time

    Examples:
        Check if market is open:
        >>> get_marketplace_info(instrument_id="5269")
    """
    ctx.info(f"Fetching marketplace info for ID: {instrument_id}")

    try:
        async with AvanzaClient() as client:
            service = MarketDataService(client)
            marketplace = await service.get_marketplace_info(instrument_id)

        status = "open" if marketplace.marketOpen else "closed"
        ctx.info(f"Market is {status}")
        return marketplace.model_dump(by_alias=True, exclude_none=True)

    except Exception as e:
        ctx.error(f"Failed to fetch marketplace info: {str(e)}")
        raise


@mcp.tool()
async def get_recent_trades(
    ctx: Context,
    instrument_id: str,
) -> dict:
    """Get recent trades for an instrument.

    Returns a list of the most recent trades with price, volume, timestamp,
    and trade metadata. Useful for understanding recent trading activity.

    Args:
        ctx: MCP context for logging
        instrument_id: Avanza instrument ID from search results

    Returns:
        List of recent trades, each containing:
        - buyer: Buyer information
        - seller: Seller information
        - dealTime: Trade timestamp
        - price: Trade price
        - volume: Trade volume
        - matchedOnMarket: Market where trade was matched

    Examples:
        Get recent trades:
        >>> get_recent_trades(instrument_id="5269")
    """
    ctx.info(f"Fetching recent trades for ID: {instrument_id}")

    try:
        async with AvanzaClient() as client:
            service = MarketDataService(client)
            trades = await service.get_trades(instrument_id)

        ctx.info(f"Retrieved {len(trades)} recent trades")
        return {
            "trades": [trade.model_dump(by_alias=True, exclude_none=True) for trade in trades]
        }

    except Exception as e:
        ctx.error(f"Failed to fetch recent trades: {str(e)}")
        raise


@mcp.tool()
async def get_broker_trade_summary(
    ctx: Context,
    instrument_id: str,
) -> dict:
    """Get broker trade summary showing buy/sell activity.

    Returns aggregated broker trading data showing total buy and sell volumes.
    Useful for understanding institutional trading activity.

    Args:
        ctx: MCP context for logging
        instrument_id: Avanza instrument ID from search results

    Returns:
        List of broker trade summaries with:
        - brokerCode: Broker identifier
        - buyVolume: Total volume bought
        - sellVolume: Total volume sold
        - netVolume: Net volume (buy - sell)

    Examples:
        Get broker trading activity:
        >>> get_broker_trade_summary(instrument_id="5269")
    """
    ctx.info(f"Fetching broker trade summary for ID: {instrument_id}")

    try:
        async with AvanzaClient() as client:
            service = MarketDataService(client)
            summaries = await service.get_broker_trades(instrument_id)

        ctx.info(f"Retrieved {len(summaries)} broker trade summaries")
        return {
            "summaries": [
                summary.model_dump(by_alias=True, exclude_none=True) for summary in summaries
            ]
        }

    except Exception as e:
        ctx.error(f"Failed to fetch broker trade summary: {str(e)}")
        raise


@mcp.tool()
async def get_dividends(
    ctx: Context,
    instrument_id: str,
) -> dict:
    """Get historical dividend data for a stock.

    Returns dividend history by year including amounts, dates, and yields.
    Useful for income investors and dividend analysis.

    Args:
        ctx: MCP context for logging
        instrument_id: Avanza instrument ID from search results

    Returns:
        Dividend data with:
        - dividendsByYear: Array of yearly dividend data including:
            - year: Year of dividend
            - dividend: Dividend amount per share
            - exDate: Ex-dividend date
            - paymentDate: Payment date
            - yield: Dividend yield percentage
            - currency: Dividend currency

    Examples:
        Get dividend history for a stock:
        >>> get_dividends(instrument_id="5479")
    """
    ctx.info(f"Fetching dividend data for ID: {instrument_id}")

    try:
        async with AvanzaClient() as client:
            service = MarketDataService(client)
            dividends = await service.get_dividends(instrument_id)

        years = len(dividends.get("dividendsByYear", []))
        ctx.info(f"Retrieved {years} years of dividend data")
        return dividends

    except Exception as e:
        ctx.error(f"Failed to fetch dividend data: {str(e)}")
        raise


@mcp.tool()
async def get_company_financials(
    ctx: Context,
    instrument_id: str,
) -> dict:
    """Get company financial statements and metrics.

    Returns comprehensive financial data including revenue, profits, margins,
    and other key metrics by year and quarter.

    Args:
        ctx: MCP context for logging
        instrument_id: Avanza instrument ID from search results

    Returns:
        Financial data with:
        - companyFinancialsByYear: Annual financial data
        - companyFinancialsByQuarter: Quarterly financial data
        - companyFinancialsByQuarterTTM: Trailing twelve months data
        Each containing metrics like:
            - revenue: Total revenue
            - operatingProfit: Operating profit
            - netProfit: Net profit
            - grossMargin: Gross profit margin
            - operatingMargin: Operating margin
            - netMargin: Net profit margin

    Examples:
        Get financials for a company:
        >>> get_company_financials(instrument_id="5479")
    """
    ctx.info(f"Fetching company financials for ID: {instrument_id}")

    try:
        async with AvanzaClient() as client:
            service = MarketDataService(client)
            financials = await service.get_company_financials(instrument_id)

        years = len(financials.get("companyFinancialsByYear", []))
        quarters = len(financials.get("companyFinancialsByQuarter", []))
        ctx.info(f"Retrieved financials: {years} years, {quarters} quarters")
        return financials

    except Exception as e:
        ctx.error(f"Failed to fetch company financials: {str(e)}")
        raise
