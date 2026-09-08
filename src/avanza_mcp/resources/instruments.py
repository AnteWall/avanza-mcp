"""Human-readable instrument summaries using the server's shared HTTP client."""

from fastmcp import Context
from fastmcp.resources import ResourceContent, ResourceResult

from .. import mcp
from ..models.common import OrderBookId
from ..services import MarketDataService


def format_stock_markdown(stock_data: dict) -> str:
    """Preserve unknown and zero values without inferring upstream units."""
    quote = stock_data.get("quote") or {}
    company = stock_data.get("company") or {}
    listing = stock_data.get("listing") or {}
    ratios = stock_data.get("keyIndicators") or {}
    lines = [f"# {stock_data.get('name', 'Unknown')}", ""]
    fields = {
        "Order-book ID": stock_data.get("orderbookId"),
        "ISIN": stock_data.get("isin"),
        "Currency": listing.get("currency"),
        "Price": quote.get("last"),
        "Change (source value)": quote.get("change"),
        "Change percent (source value)": quote.get("changePercent"),
        "Quote time (source value)": quote.get("timeOfLast"),
        "Quote updated (source value)": quote.get("updated"),
        "Real-time flag": quote.get("isRealTime"),
        "P/E": ratios.get("priceEarningsRatio"),
        "Dividend yield (source value)": ratios.get("directYield"),
        "Report date": ratios.get("reportDate"),
    }
    for label, value in fields.items():
        lines.append(f"**{label}:** {value if value is not None else 'Unknown'}")
    market_cap = ratios.get("marketCapital")
    if market_cap is None:
        market_cap = company.get("marketCapital")
    if isinstance(market_cap, dict):
        value = market_cap.get("value")
        currency = market_cap.get("currency")
        lines.append(
            f"**Market cap:** {value if value is not None else 'Unknown'} {currency or 'Unknown currency'}"
        )
    if company.get("description"):
        lines.extend(["", "## Company (Upstream Text)", company["description"]])
    lines.extend(
        [
            "",
            "Latest available data, not guaranteed live. Source values are not rescaled; timestamp units must be verified before conversion.",
        ]
    )
    return "\n".join(lines)


def format_fund_markdown(fund_data: dict) -> str:
    """Render reported values, including zero fees/returns, without assumed currency."""
    development = fund_data.get("development") or {}
    fee = fund_data.get("fee") or {}
    lines = [f"# {fund_data.get('name', 'Unknown')}", ""]
    fields = {
        "ISIN": fund_data.get("isin"),
        "NAV": fund_data.get("nav"),
        "Currency": fund_data.get("currency"),
        "NAV date": fund_data.get("navDate"),
        "Portfolio date": fund_data.get("portfolioDate"),
        "Last updated": fund_data.get("lastUpdated"),
        "YTD (source value)": fund_data.get(
            "developmentThisYear", development.get("thisYear")
        ),
        "1 year (source value)": fund_data.get(
            "developmentOneYear", development.get("oneYear")
        ),
        "3 years (source value)": fund_data.get(
            "developmentThreeYears", development.get("threeYears")
        ),
        "Risk level": fund_data.get("risk"),
        "Ongoing charges (source value)": fee.get("ongoingCharges"),
        "Product fee (source value)": fund_data.get("productFee"),
        "Management fee (source value)": fund_data.get("managementFee"),
    }
    for label, value in fields.items():
        lines.append(f"**{label}:** {value if value is not None else 'Unknown'}")
    if fund_data.get("description"):
        lines.extend(["", "## Description (Upstream Text)", fund_data["description"]])
    lines.extend(
        [
            "",
            "Latest available data, not guaranteed live. Return/fee scales and cumulative versus annualized conventions must be verified before comparison.",
        ]
    )
    return "\n".join(lines)


@mcp.resource("avanza://stock/{order_book_id}", mime_type="text/markdown")
async def get_stock_resource(
    order_book_id: OrderBookId, ctx: Context
) -> ResourceResult:
    """Stock summary by Avanza order-book ID, with source timestamps when supplied."""
    stock = await MarketDataService(ctx.lifespan_context["client"]).get_stock_info(
        order_book_id
    )
    return ResourceResult(
        [
            ResourceContent(
                format_stock_markdown(stock.model_dump(by_alias=True)),
                mime_type="text/markdown",
            )
        ]
    )


@mcp.resource("avanza://fund/{order_book_id}", mime_type="text/markdown")
async def get_fund_resource(order_book_id: OrderBookId, ctx: Context) -> ResourceResult:
    """Fund summary by Avanza order-book ID, with NAV/portfolio dates when supplied."""
    fund = await MarketDataService(ctx.lifespan_context["client"]).get_fund_info(
        order_book_id
    )
    return ResourceResult(
        [
            ResourceContent(
                format_fund_markdown(
                    fund.model_dump(by_alias=True, exclude_unset=True)
                ),
                mime_type="text/markdown",
            )
        ]
    )
