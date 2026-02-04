"""Analysis prompt templates for common workflows."""

from .. import mcp


@mcp.prompt()
def analyze_stock(stock_symbol: str) -> str:
    """Comprehensive stock analysis workflow.

    Guides the LLM through analyzing a stock including company information,
    price performance, recent news, and valuation metrics.

    Args:
        stock_symbol: Stock ticker symbol or name to analyze

    Returns:
        Prompt text for stock analysis
    """
    return f"""Please perform a comprehensive analysis of {stock_symbol}:

1. **Find the stock**: Use search_instruments() to find the stock and get its instrument_id
2. **Get detailed information**: Use get_stock_info() to retrieve:
   - Current price and recent performance
   - Company description and sector
   - Key financial ratios (P/E, dividend yield, etc.)
3. **Analyze price trends**: Use get_stock_chart() to get historical data (1 year, daily)
4. **Check recent news**: Use get_news() to see recent company announcements
5. **Assess the orderbook**: Use get_orderbook() to check current liquidity

Based on this data, provide:
- **Current valuation assessment** (is it overvalued/undervalued?)
- **Price trend analysis** (what's the recent momentum?)
- **Key risks and opportunities**
- **Overall investment perspective**

Focus on factual analysis based on the available data.
"""


@mcp.prompt()
def compare_funds(fund_names: str) -> str:
    """Compare multiple funds across key metrics.

    Analyzes and compares funds on performance, fees, risk metrics,
    and characteristics.

    Args:
        fund_names: Comma-separated list of fund names to compare

    Returns:
        Prompt text for fund comparison
    """
    funds = [f.strip() for f in fund_names.split(",")]
    funds_list = "\n".join([f"- {fund}" for fund in funds])

    return f"""Compare the following funds:
{funds_list}

For each fund:
1. **Find the fund**: Use search_instruments() with instrument_type="fund"
2. **Get fund details**: Use get_fund_info() to retrieve:
   - Current NAV and recent performance
   - Performance over multiple periods (YTD, 1Y, 3Y, 5Y)
   - Risk rating and metrics
   - Fees (ongoing charges, entry/exit fees)
   - Fund characteristics (type, category, AUM)

Then create a comparison showing:

| Metric | {' | '.join(funds)} |
|--------|{'-|' * len(funds)}
| NAV | ... | ... |
| YTD Return | ... | ... |
| 1Y Return | ... | ... |
| 3Y Return | ... | ... |
| 5Y Return | ... | ... |
| Risk Level (1-7) | ... | ... |
| Ongoing Charges | ... | ... |
| Fund Size (AUM) | ... | ... |

Conclude with:
- Which fund has the best risk-adjusted returns?
- Which has the lowest fees?
- Recommendation based on the comparison
"""


@mcp.prompt()
def screen_dividend_stocks(min_yield: float = 3.0) -> str:
    """Screen for dividend-paying stocks.

    Helps find stocks with attractive dividend yields.

    Args:
        min_yield: Minimum dividend yield percentage (default: 3.0)

    Returns:
        Prompt text for dividend screening
    """
    return f"""Help me find dividend stocks with yields above {min_yield}%.

Process:
1. Search for major Swedish stocks (you might start with well-known companies)
2. For each stock, use get_stock_info() to check the dividend yield
3. Filter for stocks with dividend_yield >= {min_yield}%

Present results as a table:

| Stock | Ticker | Price | Dividend Yield | P/E Ratio | Market Cap |
|-------|--------|-------|----------------|-----------|------------|
| ...   | ...    | ...   | ...%           | ...       | ...        |

Sort by dividend yield (highest first) and include:
- Brief assessment of sustainability (based on P/E and other metrics)
- Any notable risks or observations
"""
