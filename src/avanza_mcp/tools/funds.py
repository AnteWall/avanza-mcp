"""Fund-specific MCP tools."""

from typing import Literal

from fastmcp import Context

from .. import mcp
from ..client import AvanzaClient
from ..services import MarketDataService


@mcp.tool()
async def get_fund_sustainability(
    ctx: Context,
    instrument_id: str,
) -> dict:
    """Get fund sustainability and ESG (Environmental, Social, Governance) metrics.

    Provides comprehensive ESG ratings, carbon metrics, product involvement data,
    and sustainability development goals aligned with the fund.

    Use search_instruments() with instrument_type="fund" to find fund IDs.

    Args:
        ctx: MCP context for logging
        instrument_id: Avanza fund ID from search results

    Returns:
        Sustainability metrics including:
        - lowCarbon: Whether fund is low carbon
        - esgScore: Overall ESG score
        - environmentalScore: Environmental performance score
        - socialScore: Social responsibility score
        - governanceScore: Corporate governance score
        - controversyScore: Controversy involvement score
        - sustainabilityRating: Overall sustainability rating (1-5)
        - productInvolvements: List of controversial product involvements
        - sustainabilityDevelopmentGoals: UN SDG alignments
        - Various fossil fuel and carbon involvement metrics

    Examples:
        Get ESG metrics for a fund:
        >>> get_fund_sustainability(instrument_id="41567")
    """
    ctx.info(f"Fetching fund sustainability for ID: {instrument_id}")

    try:
        async with AvanzaClient() as client:
            service = MarketDataService(client)
            sustainability = await service.get_fund_sustainability(instrument_id)

        ctx.info(
            f"Retrieved sustainability data: ESG={sustainability.esgScore}, rating={sustainability.sustainabilityRating}"
        )
        return sustainability.model_dump(by_alias=True, exclude_none=True)

    except Exception as e:
        ctx.error(f"Failed to fetch fund sustainability: {str(e)}")
        raise


@mcp.tool()
async def get_fund_chart(
    ctx: Context,
    instrument_id: str,
    time_period: Literal[
        "one_week",
        "one_month",
        "three_months",
        "one_year",
        "three_years",
        "five_years",
        "this_year",
    ] = "three_years",
) -> dict:
    """Get fund chart data with historical performance.

    Returns time series data showing fund performance over the selected period.
    Perfect for visualizing fund NAV history and performance trends.

    Args:
        ctx: MCP context for logging
        instrument_id: Avanza fund ID from search results
        time_period: Time period for chart data. Options:
            - "one_week": Past week
            - "one_month": Past month
            - "three_months": Past 3 months
            - "one_year": Past year
            - "three_years": Past 3 years (default)
            - "five_years": Past 5 years
            - "this_year": Year to date

    Returns:
        Chart data with:
        - id: Fund identifier
        - name: Fund name
        - dataSerie: Array of data points with timestamp (x) and value (y)
        - fromDate: Start date of chart data
        - toDate: End date of chart data

    Examples:
        Get 3-year performance chart:
        >>> get_fund_chart(instrument_id="41567", time_period="three_years")

        Get year-to-date performance:
        >>> get_fund_chart(instrument_id="41567", time_period="this_year")
    """
    ctx.info(f"Fetching fund chart for ID: {instrument_id} (time_period={time_period})")

    try:
        async with AvanzaClient() as client:
            service = MarketDataService(client)
            chart = await service.get_fund_chart(instrument_id, time_period)

        data_points = len(chart.dataSerie)
        ctx.info(f"Retrieved chart with {data_points} data points")
        return chart.model_dump(by_alias=True, exclude_none=True)

    except Exception as e:
        ctx.error(f"Failed to fetch fund chart: {str(e)}")
        raise


@mcp.tool()
async def get_fund_chart_periods(
    ctx: Context,
    instrument_id: str,
) -> dict:
    """Get available fund performance periods with returns.

    Returns a list of all available time periods with the fund's performance
    (percentage change) for each period. Useful for quick performance overview.

    Args:
        ctx: MCP context for logging
        instrument_id: Avanza fund ID from search results

    Returns:
        List of performance periods, each containing:
        - timePeriod: Period identifier (e.g., "one_year", "three_years")
        - change: Performance change as percentage
        - startDate: Start date for the period

    Examples:
        Get all available performance periods:
        >>> get_fund_chart_periods(instrument_id="41567")
    """
    ctx.info(f"Fetching fund chart periods for ID: {instrument_id}")

    try:
        async with AvanzaClient() as client:
            service = MarketDataService(client)
            periods = await service.get_fund_chart_periods(instrument_id)

        ctx.info(f"Retrieved {len(periods)} time periods")
        return {
            "periods": [period.model_dump(by_alias=True, exclude_none=True) for period in periods]
        }

    except Exception as e:
        ctx.error(f"Failed to fetch fund chart periods: {str(e)}")
        raise


@mcp.tool()
async def get_fund_description(
    ctx: Context,
    instrument_id: str,
) -> dict:
    """Get detailed fund description and category information.

    Provides comprehensive textual description of the fund, its investment
    strategy, and detailed category classification.

    Args:
        ctx: MCP context for logging
        instrument_id: Avanza fund ID from search results

    Returns:
        Fund description data with:
        - response: Main fund description text
        - heading: Description heading/title
        - detailedCategoryDescription: Detailed category explanation

    Examples:
        Get fund description:
        >>> get_fund_description(instrument_id="41567")
    """
    ctx.info(f"Fetching fund description for ID: {instrument_id}")

    try:
        async with AvanzaClient() as client:
            service = MarketDataService(client)
            description = await service.get_fund_description(instrument_id)

        ctx.info("Retrieved fund description")
        return description.model_dump(by_alias=True, exclude_none=True)

    except Exception as e:
        ctx.error(f"Failed to fetch fund description: {str(e)}")
        raise


@mcp.tool()
async def get_fund_holdings(
    ctx: Context,
    instrument_id: str,
) -> dict:
    """Get fund portfolio holdings and allocation breakdown.

    Returns the fund's portfolio composition including geographic allocation,
    sector allocation, and top holdings. Useful for understanding what the
    fund invests in.

    Args:
        ctx: MCP context for logging
        instrument_id: Avanza fund ID from search results

    Returns:
        Portfolio allocation data with:
        - countryChartData: Geographic allocation by country (name, y=percentage)
        - sectorChartData: Sector allocation (name, y=percentage)
        - holdingChartData: Top holdings (name, y=percentage)
        - portfolioDate: Date of portfolio data

    Examples:
        Get holdings for a fund:
        >>> get_fund_holdings(instrument_id="878733")
    """
    ctx.info(f"Fetching fund holdings for ID: {instrument_id}")

    try:
        async with AvanzaClient() as client:
            service = MarketDataService(client)
            fund_info = await service.get_fund_info(instrument_id)

        holdings = {
            "countryChartData": [
                c.model_dump(by_alias=True, exclude_none=True)
                for c in fund_info.country_chart_data
            ],
            "sectorChartData": [
                s.model_dump(by_alias=True, exclude_none=True)
                for s in fund_info.sector_chart_data
            ],
            "holdingChartData": [
                h.model_dump(by_alias=True, exclude_none=True)
                for h in fund_info.holding_chart_data
            ],
            "portfolioDate": (
                fund_info.portfolio_date.isoformat()
                if fund_info.portfolio_date
                else None
            ),
        }

        countries = len(holdings["countryChartData"])
        sectors = len(holdings["sectorChartData"])
        top_holdings = len(holdings["holdingChartData"])
        ctx.info(
            f"Retrieved holdings: {countries} countries, {sectors} sectors, {top_holdings} top holdings"
        )
        return holdings

    except Exception as e:
        ctx.error(f"Failed to fetch fund holdings: {str(e)}")
        raise
