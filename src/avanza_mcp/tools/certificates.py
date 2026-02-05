"""Certificate MCP tools."""

from fastmcp import Context

from .. import mcp
from ..client import AvanzaClient
from ..models.certificate import CertificateFilter, CertificateFilterRequest
from ..models.filter import SortBy
from ..services import MarketDataService


@mcp.tool()
async def filter_certificates(
    ctx: Context,
    offset: int = 0,
    limit: int = 20,
    directions: list[str] | None = None,
    leverages: list[float] | None = None,
    issuers: list[str] | None = None,
    categories: list[str] | None = None,
    exposures: list[str] | None = None,
    underlying_instruments: list[str] | None = None,
    sort_field: str = "name",
    sort_order: str = "asc",
) -> dict:
    """Filter and list certificates with optional filtering and pagination.

    Search through available certificates with optional filters for direction
    (long/short), leverage, issuer, category, exposure, and underlying instrument.
    Supports pagination for large result sets.

    Args:
        ctx: MCP context for logging
        offset: Number of results to skip (default: 0)
        limit: Maximum number of results to return (default: 20, max: 100)
        directions: Filter by direction, e.g., ["long"], ["short"]
        leverages: Filter by leverage values, e.g., [1.0, 2.0]
        issuers: Filter by issuer names, e.g., ["Valour", "21Shares"]
        categories: Filter by categories
        exposures: Filter by exposures
        underlying_instruments: Filter by underlying instrument IDs
        sort_field: Field to sort by (default: "name")
        sort_order: Sort order "asc" or "desc" (default: "asc")

    Returns:
        Filtered list of certificates with:
        - certificates: Array of certificate objects with orderbookId, name, price, etc.
        - pagination: Current offset and limit
        - totalNumberOfOrderbooks: Total matching certificates

    Examples:
        List first 20 certificates:
        >>> filter_certificates()

        Find long certificates with 1x leverage:
        >>> filter_certificates(directions=["long"], leverages=[1.0])

        Get next page of results:
        >>> filter_certificates(offset=20, limit=20)
    """
    ctx.info(f"Filtering certificates: offset={offset}, limit={limit}")

    try:
        filter_req = CertificateFilterRequest(
            filter=CertificateFilter(
                directions=directions or [],
                leverages=leverages or [],
                issuers=issuers or [],
                categories=categories or [],
                exposures=exposures or [],
                underlyingInstruments=underlying_instruments or [],
            ),
            offset=offset,
            limit=min(limit, 100),
            sortBy=SortBy(field=sort_field, order=sort_order),
        )

        async with AvanzaClient() as client:
            service = MarketDataService(client)
            result = await service.filter_certificates(filter_req)

        ctx.info(f"Retrieved {len(result.certificates)} certificates")
        return result.model_dump(by_alias=True, exclude_none=True)

    except Exception as e:
        ctx.error(f"Failed to filter certificates: {str(e)}")
        raise


@mcp.tool()
async def get_certificate_info(ctx: Context, instrument_id: str) -> dict:
    """Get detailed information about a specific certificate.

    Provides comprehensive certificate data including current price, leverage,
    underlying instrument, issuer, and historical performance.

    Args:
        ctx: MCP context for logging
        instrument_id: Avanza certificate ID (orderbookId from filter results)

    Returns:
        Detailed certificate information including:
        - Basic info: name, ISIN, issuer
        - Pricing: current quote, buy/sell prices
        - Characteristics: leverage, direction, underlying instrument
        - Historical data: price history over various periods

    Examples:
        Get info for a certificate:
        >>> get_certificate_info(instrument_id="1756318")
    """
    ctx.info(f"Fetching certificate info for ID: {instrument_id}")

    try:
        async with AvanzaClient() as client:
            service = MarketDataService(client)
            certificate = await service.get_certificate_info(instrument_id)

        ctx.info(f"Retrieved info for: {certificate.name}")
        return certificate.model_dump(by_alias=True, exclude_none=True)

    except Exception as e:
        ctx.error(f"Failed to fetch certificate info: {str(e)}")
        raise


@mcp.tool()
async def get_certificate_details(ctx: Context, instrument_id: str) -> dict:
    """Get extended details about a specific certificate.

    Provides additional detailed information beyond basic certificate info.

    Args:
        ctx: MCP context for logging
        instrument_id: Avanza certificate ID

    Returns:
        Extended certificate details

    Examples:
        Get detailed info:
        >>> get_certificate_details(instrument_id="1756318")
    """
    ctx.info(f"Fetching certificate details for ID: {instrument_id}")

    try:
        async with AvanzaClient() as client:
            service = MarketDataService(client)
            details = await service.get_certificate_details(instrument_id)

        ctx.info("Retrieved certificate details")
        return details.model_dump(by_alias=True, exclude_none=True)

    except Exception as e:
        ctx.error(f"Failed to fetch certificate details: {str(e)}")
        raise
