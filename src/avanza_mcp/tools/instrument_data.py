"""Additional instrument data MCP tools."""

from fastmcp import Context

from .. import mcp
from ..client import AvanzaClient
from ..services import MarketDataService


@mcp.tool()
async def get_number_of_owners(ctx: Context, instrument_id: str) -> dict:
    """Get the number of owners for any instrument.

    Returns the current number of Avanza customers who own this instrument.
    Works for stocks, funds, ETFs, certificates, warrants, etc.

    Args:
        ctx: MCP context for logging
        instrument_id: Avanza instrument ID (orderbookId)

    Returns:
        Number of owners data:
        - orderbookId: Instrument identifier
        - numberOfOwners: Current owner count
        - timestamp: When data was retrieved

    Examples:
        Check ownership for a stock:
        >>> get_number_of_owners(instrument_id="5247")

        Check ownership for an ETF:
        >>> get_number_of_owners(instrument_id="742236")
    """
    ctx.info(f"Fetching number of owners for ID: {instrument_id}")

    try:
        async with AvanzaClient() as client:
            service = MarketDataService(client)
            result = await service.get_number_of_owners(instrument_id)

        if result.numberOfOwners is not None:
            ctx.info(f"Instrument has {result.numberOfOwners} owners")
        else:
            ctx.info("Retrieved number of owners data")
        return result.model_dump(by_alias=True, exclude_none=True)

    except Exception as e:
        ctx.error(f"Failed to fetch number of owners: {str(e)}")
        raise


@mcp.tool()
async def get_short_selling(ctx: Context, instrument_id: str) -> dict:
    """Get short selling data for an instrument.

    Returns short selling volume and percentage for the instrument,
    indicating how heavily shorted it is.

    Args:
        ctx: MCP context for logging
        instrument_id: Avanza instrument ID (orderbookId)

    Returns:
        Short selling data:
        - orderbookId: Instrument identifier
        - shortSellingVolume: Volume of shares sold short
        - shortSellingPercentage: Percentage of float sold short
        - date: Date of data

    Examples:
        Check short interest for a stock:
        >>> get_short_selling(instrument_id="5247")
    """
    ctx.info(f"Fetching short selling data for ID: {instrument_id}")

    try:
        async with AvanzaClient() as client:
            service = MarketDataService(client)
            result = await service.get_short_selling(instrument_id)

        ctx.info("Retrieved short selling data")
        return result.model_dump(by_alias=True, exclude_none=True)

    except Exception as e:
        ctx.error(f"Failed to fetch short selling data: {str(e)}")
        raise


@mcp.tool()
async def get_marketmaker_chart(
    ctx: Context, instrument_id: str, time_period: str = "today"
) -> dict:
    """Get price chart data for traded products (certificates, warrants, ETFs).

    Returns OHLC (Open-High-Low-Close) candlestick data with market maker
    information for certificates, warrants, ETFs, and other traded products.

    Args:
        ctx: MCP context for logging
        instrument_id: Avanza instrument ID (orderbookId)
        time_period: Time period for chart data (default: "today")
            Available: today, one_week, one_month, three_months, six_months,
            one_year, three_years, five_years

    Returns:
        Chart data with:
        - ohlc: Array of OHLC candlestick data points
        - metadata: Chart resolution and available resolutions
        - from/to: Date range covered
        - marketMaker: Array of market maker data (may be empty)

    Examples:
        Get today's chart for a certificate:
        >>> get_marketmaker_chart(instrument_id="2090357", time_period="today")

        Get 1-month chart for an ETF:
        >>> get_marketmaker_chart(instrument_id="5649", time_period="one_month")

        Get chart for a warrant:
        >>> get_marketmaker_chart(instrument_id="2267542")
    """
    ctx.info(f"Fetching chart data for ID: {instrument_id}, period: {time_period}")

    try:
        async with AvanzaClient() as client:
            service = MarketDataService(client)
            result = await service.get_marketmaker_chart(instrument_id, time_period)

        data_points = len(result.ohlc) if result.ohlc else 0
        ctx.info(f"Retrieved chart with {data_points} data points")
        return result.model_dump(by_alias=True, exclude_none=True)

    except Exception as e:
        ctx.error(f"Failed to fetch chart data: {str(e)}")
        raise
