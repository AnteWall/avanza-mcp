# Avanza MCP Server

A Model Context Protocol (MCP) server providing access to Avanza's public API. Get real-time Swedish stock quotes, fund information, charts, and comprehensive market data.

## ⚠️ Disclaimer

This is an unofficial API client/MCP Server. Not affiliated with Avanza Bank AB. The underlying API can be taken down or changed without warning at any point in time.

The author of this software is not responsible for any indirect damages (foreseeable or unforeseeable), such as, if necessary, loss or alteration of or fraudulent access to data, accidental transmission of viruses or of any other harmful element, loss of profits or opportunities, the cost of replacement goods and services or the attitude and behavior of a third party.

## 🛠️ MCP Tools

### Search & Discovery
| Tool | Description |
|------|-------------|
| `search_instruments` | Find stocks, funds, ETFs by name or symbol |
| `get_instrument_by_order_book_id` | Look up instruments by order book ID |

### Stock Analysis
| Tool | Description |
|------|-------------|
| `get_stock_info` | Complete stock information with fundamentals |
| `get_stock_quote` | Real-time price and volume data |
| `get_stock_analysis` | Financial ratios by year and quarter |
| `get_stock_chart` | Historical OHLC price data |
| `get_orderbook` | Order book depth with bid/ask levels |
| `get_marketplace_info` | Trading hours and market status |
| `get_recent_trades` | Latest executed trades |
| `get_broker_trade_summary` | Broker buy/sell activity |
| `get_dividends` | Historical dividend data |
| `get_company_financials` | Annual and quarterly financial statements |

### Fund Analysis
| Tool | Description |
|------|-------------|
| `get_fund_info` | Complete fund information with performance |
| `get_fund_sustainability` | ESG scores and sustainability metrics |
| `get_fund_chart` | Historical performance charts |
| `get_fund_chart_periods` | Performance across all time periods |
| `get_fund_description` | Detailed fund description |
| `get_fund_holdings` | Portfolio allocation (country, sector, top holdings) |

### Certificates
| Tool | Description |
|------|-------------|
| `filter_certificates` | Search and filter certificates with pagination |
| `get_certificate_info` | Get detailed certificate information |
| `get_certificate_details` | Get extended certificate details |

### Warrants
| Tool | Description |
|------|-------------|
| `filter_warrants` | Search and filter warrants (turbos, minis) |
| `get_warrant_info` | Get detailed warrant information |
| `get_warrant_details` | Get extended warrant details |

### ETFs
| Tool | Description |
|------|-------------|
| `filter_etfs` | Search and filter exchange-traded funds |
| `get_etf_info` | Get detailed ETF information |
| `get_etf_details` | Get extended ETF details |

### Futures/Forwards
| Tool | Description |
|------|-------------|
| `list_futures_forwards` | List available futures and forwards |
| `get_future_forward_filter_options` | Get available filter options |
| `get_future_forward_info` | Get contract information |
| `get_future_forward_details` | Get extended contract details |

### Additional Data
| Tool | Description |
|------|-------------|
| `get_number_of_owners` | Get owner count for any instrument |
| `get_short_selling` | Get short selling data for instruments |
| `get_marketmaker_chart` | Get OHLC price chart data for traded products (certificates, warrants, ETFs) |

## 💡 MCP Prompts

- `analyze_stock` - Comprehensive stock analysis workflow
- `compare_funds` - Multi-fund comparison template
- `screen_dividend_stocks` - Dividend stock screening


### Configuration for MCP Clients

For Claude Desktop or other MCP clients, add to your configuration:

```json
{
  "mcpServers": {
    "avanza": {
      "command": "uvx",
      "args": ["--prerelease=allow", "avanza-mcp"]
    }
  }
}
```

> **Note:** The `--prerelease=allow` flag is required because this package depends on fastmcp 3.0 (currently in beta). This will no longer be needed once fastmcp 3.0 stable is released.

### Usage in Claude Desktop

Once configured, you can ask Claude:

- "Search for Volvo stock on Avanza"
- "Get the latest stock quote for Ericsson"
- "Show me sustainable Swedish funds"
- "What's in the order book for H&M?"
- "Compare the performance of these three funds"
- "What dividends has SEB paid over the years?"
- "Show me the portfolio holdings for Avanza Global fund"

## 📄 License

MIT License - See [LICENSE.md](LICENSE.md) for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
