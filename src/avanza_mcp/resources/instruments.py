"""URI-based instrument resources."""

from .. import mcp
from ..client import AvanzaClient
from ..services import MarketDataService


def format_stock_markdown(stock_data: dict) -> str:
    """Format stock info as markdown.

    Args:
        stock_data: Stock information dictionary

    Returns:
        Formatted markdown string
    """
    quote = stock_data.get("quote", {})
    company = stock_data.get("company", {})
    listing = stock_data.get("listing", {})
    key_ratios = stock_data.get("key_ratios") or stock_data.get("keyIndicators", {})

    name = stock_data.get("name", "Unknown")
    price = quote.get("last", "N/A")
    change = quote.get("change", 0)
    change_pct = quote.get("changePercent", 0)
    currency = listing.get("currency", "SEK")

    md = f"# {name}\n\n"
    md += f"**Price:** {price} {currency}\n"
    md += f"**Change:** {change:+.2f} ({change_pct:+.2f}%)\n\n"

    if company:
        if desc := company.get("description"):
            md += f"## Company\n{desc}\n\n"
        if market_cap := company.get("marketCapital"):
            if isinstance(market_cap, dict):
                cap_value = market_cap.get("value", 0)
                cap_currency = market_cap.get("currency", currency)
                md += f"**Market Cap:** {cap_value:,.0f} {cap_currency}\n"
            else:
                md += f"**Market Cap:** {market_cap:,.0f} {currency}\n"

    if key_ratios:
        md += "\n## Key Ratios\n"
        if pe := key_ratios.get("priceEarningsRatio"):
            md += f"- **P/E Ratio:** {pe:.2f}\n"
        if div_yield := key_ratios.get("directYield"):
            md += f"- **Dividend Yield:** {div_yield:.2f}%\n"

    return md


def format_fund_markdown(fund_data: dict) -> str:
    """Format fund info as markdown.

    Args:
        fund_data: Fund information dictionary

    Returns:
        Formatted markdown string
    """
    name = fund_data.get("name", "Unknown")
    nav = fund_data.get("nav", "N/A")
    currency = fund_data.get("currency", "SEK")

    md = f"# {name}\n\n"
    md += f"**NAV:** {nav} {currency}\n\n"

    if desc := fund_data.get("description"):
        md += f"{desc}\n\n"

    if development := fund_data.get("development"):
        md += "## Performance\n"
        if ytd := development.get("thisYear"):
            md += f"- **YTD:** {ytd:+.2f}%\n"
        if one_year := development.get("oneYear"):
            md += f"- **1 Year:** {one_year:+.2f}%\n"
        if three_years := development.get("threeYears"):
            md += f"- **3 Years:** {three_years:+.2f}%\n"

    if risk := fund_data.get("risk"):
        md += f"\n**Risk Level:** {risk}/7\n"

    if fee := fund_data.get("fee", {}).get("ongoingCharges"):
        md += f"**Ongoing Charges:** {fee:.2f}%\n"

    return md


@mcp.resource("avanza://stock/{instrument_id}")
async def get_stock_resource(instrument_id: str) -> str:
    """Get stock information as a markdown resource.

    URI: avanza://stock/{instrument_id}

    Args:
        instrument_id: Avanza stock ID

    Returns:
        Formatted markdown with stock information
    """
    async with AvanzaClient() as client:
        service = MarketDataService(client)
        stock_info = await service.get_stock_info(instrument_id)

    stock_data = stock_info.model_dump(by_alias=True, exclude_none=True)
    return format_stock_markdown(stock_data)


@mcp.resource("avanza://fund/{instrument_id}")
async def get_fund_resource(instrument_id: str) -> str:
    """Get fund information as a markdown resource.

    URI: avanza://fund/{instrument_id}

    Args:
        instrument_id: Avanza fund ID

    Returns:
        Formatted markdown with fund information
    """
    async with AvanzaClient() as client:
        service = MarketDataService(client)
        fund_info = await service.get_fund_info(instrument_id)

    fund_data = fund_info.model_dump(by_alias=True, exclude_none=True)
    return format_fund_markdown(fund_data)
