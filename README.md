# Avanza MCP Server

![PyPI - Version](https://img.shields.io/pypi/v/avanza-mcp)
[![CI](https://github.com/AnteWall/avanza-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/AnteWall/avanza-mcp/actions/workflows/ci.yml)

Read-only access to Avanza's public market data from your MCP client. No Avanza account required.

## Disclaimer

This is an unofficial API client/MCP Server. Not affiliated with Avanza Bank AB. The underlying API can be taken down or changed without warning at any point in time.

The author of this software is not responsible for any indirect damages (foreseeable or unforeseeable), such as, if necessary, loss or alteration of or fraudulent access to data, accidental transmission of viruses or of any other harmful element, loss of profits or opportunities, the cost of replacement goods and services or the attitude and behavior of a third party.

## Features

- Stocks, funds, ETFs, certificates, warrants and futures/forwards.
- Quotes, charts, financial ratios, dividends, order books and ownership data.
- Fund performance, fees, holdings, sustainability and research prompts.

## Setup

Requires [uv](https://docs.astral.sh/uv/) and Python 3.12+. Local clients launch the server over stdio.

<details>
<summary>Claude Desktop and Cursor</summary>

Both use this configuration:

```json
{
  "mcpServers": {
    "avanza": {
      "command": "uvx",
      "args": ["avanza-mcp"]
    }
  }
}
```

- **Claude Desktop:** open Settings > Developer > Edit Config, merge the configuration, then fully restart Claude Desktop.
- **Cursor:** add it to `.cursor/mcp.json` in your project, or `~/.cursor/mcp.json` globally. Enable the server in Cursor's MCP settings.

</details>

<details>
<summary>Claude Code</summary>

Run in your project:

```bash
claude mcp add avanza -- uvx avanza-mcp
```

Use `/mcp` in Claude Code to check the connection.

</details>

<details>
<summary>Visual Studio Code</summary>

Add to `.vscode/mcp.json`, or open **MCP: Open User Configuration** for global setup:

```json
{
  "servers": {
    "avanza": {
      "type": "stdio",
      "command": "uvx",
      "args": ["avanza-mcp"]
    }
  }
}
```

Run **MCP: List Servers**, start `avanza`, and enable its tools in agent chat.

</details>

<details>
<summary>OpenCode</summary>

Add to your project's `opencode.json` or global `~/.config/opencode/opencode.json`:

```json
{
  "mcp": {
    "avanza": {
      "type": "local",
      "command": ["uvx", "avanza-mcp"],
      "enabled": true
    }
  }
}
```

</details>

<details>
<summary>HTTP and ChatGPT</summary>

From a source checkout:

```bash
uv sync
uv run fastmcp run src/avanza_mcp/__init__.py:mcp --transport http
```

Connect HTTP clients to `http://localhost:8000/mcp`. ChatGPT requires a remotely reachable HTTPS deployment; add its `/mcp` URL using [ChatGPT's developer-mode setup](https://platform.openai.com/docs/guides/developer-mode).

This project does not provide a hosted endpoint. Configure access controls before exposing your server publicly.

</details>

<details>
<summary>Python</summary>

Install with `uv add avanza-mcp`, then use FastMCP's in-process client:

```python
import asyncio
from fastmcp import Client
from avanza_mcp import mcp

async def main():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "search_instruments", {"query": "Volvo", "instrument_type": "stock"}
        )
        print(result.structured_content)

asyncio.run(main())
```

</details>

If a desktop client cannot find `uvx`, use its absolute executable path. See [DEVELOPMENT.md](DEVELOPMENT.md) for running from source and tests.

## Tools

All 34 tools are read-only. Search first to obtain an `order_book_id`; history tools expose pagination. Data is latest available, not guaranteed live.

| Category | Tool | Description |
|----------|------|-------------|
| Search | `search_instruments` | Find instruments by name, ticker or ISIN |
| Search | `get_instrument_by_order_book_id` | Match an exact ID within search candidates |
| Stocks | `get_stock_info` | Company, listing, fundamentals and quote |
| Stocks | `get_stock_quote` | Latest price and trading volume |
| Stocks | `get_stock_chart` | Historical OHLC price points |
| Stocks | `get_stock_analysis` | A named financial-ratio history |
| Stocks | `get_dividends` | A named dividend metric by financial year |
| Stocks | `get_company_financials` | A named annual or quarterly financial metric |
| Market | `get_orderbook` | Bid/ask depth |
| Market | `get_marketplace_info` | Trading hours and market status |
| Market | `get_recent_trades` | Recent trade snapshot |
| Market | `get_broker_trade_summary` | Broker buy/sell activity |
| Funds | `get_fund_info` | NAV, performance, fees and fund information |
| Funds | `get_fund_sustainability` | ESG and sustainability metrics |
| Funds | `get_fund_chart` | Historical fund chart points |
| Funds | `get_fund_chart_periods` | Available performance periods |
| Funds | `get_fund_description` | Investment strategy and category |
| Funds | `get_fund_holdings` | Country, sector and top-holding allocations |
| Certificates | `filter_certificates` | Filter and list certificates |
| Certificates | `get_certificate_info` | Certificate information |
| Certificates | `get_certificate_details` | Extended certificate details |
| Warrants | `filter_warrants` | Filter and list warrants |
| Warrants | `get_warrant_info` | Warrant information |
| Warrants | `get_warrant_details` | Extended warrant details |
| ETFs | `filter_etfs` | Filter and list ETFs |
| ETFs | `get_etf_info` | ETF information |
| ETFs | `get_etf_details` | Extended ETF details |
| Futures/Forwards | `list_futures_forwards` | Filter and list contracts |
| Futures/Forwards | `get_future_forward_filter_options` | Available contract filters |
| Futures/Forwards | `get_future_forward_info` | Contract information |
| Futures/Forwards | `get_future_forward_details` | Extended contract details |
| Additional | `get_number_of_owners` | Avanza ownership history |
| Additional | `get_short_selling` | Short-selling history |
| Additional | `get_marketmaker_chart` | Traded-product OHLC and market-maker data |

## Prompts

- `analyze_stock(stock_symbol)` - Research a stock's fundamentals and price history.
- `compare_funds(fund_names)` - Compare two or more supplied funds.
- `screen_dividend_stocks(candidates, min_yield=3.0)` - Screen supplied stocks by dividend yield.

## Resources

- `avanza://docs/usage` - Tool usage guide.
- `avanza://docs/quick-start` - Common workflows.
- `avanza://stock/{order_book_id}` - Stock summary as Markdown.
- `avanza://fund/{order_book_id}` - Fund summary as Markdown.

## License

[MIT](LICENSE.md)
