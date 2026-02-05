"""ETF MCP tools."""

from fastmcp import Context

from .. import mcp
from ..client import AvanzaClient
from ..models.etf import ETFFilter, ETFFilterRequest
from ..models.filter import SortBy
from ..services import MarketDataService


@mcp.tool()
async def filter_etfs(
    ctx: Context,
    offset: int = 0,
    limit: int = 20,
    asset_categories: list[str] | None = None,
    sub_categories: list[str] | None = None,
    exposures: list[str] | None = None,
    risk_scores: list[str] | None = None,
    directions: list[str] | None = None,
    issuers: list[str] | None = None,
    currency_codes: list[str] | None = None,
    sort_field: str = "numberOfOwners",
    sort_order: str = "desc",
) -> dict:
    """Filter and list ETFs with optional filtering and pagination.

    Search through exchange-traded funds with filters for asset category,
    geographic exposure, issuer, risk score, and more.

    Args:
        ctx: MCP context for logging
        offset: Number of results to skip (default: 0)
        limit: Maximum number of results (default: 20, max: 100)
        asset_categories: Filter by category, e.g., ["stock"], ["commodity"]
        sub_categories: Filter by sub-category, e.g., ["teknologi"], ["fastigheter"]
        exposures: Filter by geographic exposure, e.g., ["usa"], ["global"]
        risk_scores: Filter by risk score levels
        directions: Filter by direction (for leveraged ETFs)
        issuers: Filter by issuer, e.g., ["iShares"], ["Vanguard"]
        currency_codes: Filter by currency, e.g., ["SEK"], ["USD"]
        sort_field: Field to sort by (default: "numberOfOwners")
        sort_order: Sort order "asc" or "desc" (default: "desc")

    Returns:
        Filtered list of ETFs with fees, yield, number of owners, etc.

    Examples:
        List most popular ETFs:
        >>> filter_etfs(sort_field="numberOfOwners", sort_order="desc")

        Find US technology ETFs:
        >>> filter_etfs(exposures=["usa"], sub_categories=["teknologi"])

        Get affordable ETFs with low fees:
        >>> filter_etfs(sort_field="managementFee", sort_order="asc")
    """
    ctx.info(f"Filtering ETFs: offset={offset}, limit={limit}")

    try:
        filter_req = ETFFilterRequest(
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
            limit=min(limit, 100),
            sortBy=SortBy(field=sort_field, order=sort_order),
        )

        async with AvanzaClient() as client:
            service = MarketDataService(client)
            result = await service.filter_etfs(filter_req)

        ctx.info(f"Retrieved {len(result.etfs)} ETFs")
        return result.model_dump(by_alias=True, exclude_none=True)

    except Exception as e:
        ctx.error(f"Failed to filter ETFs: {str(e)}")
        raise


@mcp.tool()
async def get_etf_info(ctx: Context, instrument_id: str) -> dict:
    """Get detailed information about a specific ETF.

    Provides comprehensive ETF data including current NAV, dividend yield,
    management fees, risk score, and historical performance.

    Args:
        ctx: MCP context for logging
        instrument_id: Avanza ETF ID

    Returns:
        Detailed ETF information with fees, yield, performance, etc.

    Examples:
        Get ETF info:
        >>> get_etf_info(instrument_id="742236")
    """
    ctx.info(f"Fetching ETF info for ID: {instrument_id}")

    try:
        async with AvanzaClient() as client:
            service = MarketDataService(client)
            etf = await service.get_etf_info(instrument_id)

        ctx.info(f"Retrieved info for: {etf.name}")
        return etf.model_dump(by_alias=True, exclude_none=True)

    except Exception as e:
        ctx.error(f"Failed to fetch ETF info: {str(e)}")
        raise


@mcp.tool()
async def get_etf_details(ctx: Context, instrument_id: str) -> dict:
    """Get extended details about a specific ETF.

    Provides additional detailed information beyond basic ETF info.

    Args:
        ctx: MCP context for logging
        instrument_id: Avanza ETF ID

    Returns:
        Extended ETF details

    Examples:
        Get detailed info:
        >>> get_etf_details(instrument_id="742236")
    """
    ctx.info(f"Fetching ETF details for ID: {instrument_id}")

    try:
        async with AvanzaClient() as client:
            service = MarketDataService(client)
            details = await service.get_etf_details(instrument_id)

        ctx.info("Retrieved ETF details")
        return details.model_dump(by_alias=True, exclude_none=True)

    except Exception as e:
        ctx.error(f"Failed to fetch ETF details: {str(e)}")
        raise
