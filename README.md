# Avanza MCP Server

A Model Context Protocol (MCP) server providing access to Avanza's public market data API. Get real-time Swedish stock quotes, fund information, charts, and comprehensive market data.

## ⚠️ Disclaimer

This is an unofficial API client/MCP Server. Not affiliated with Avanza Bank AB. The underlying API can be taken down or changed without warning at any point in time.

The author of this software is not responsible for any indirect damages (foreseeable or unforeseeable), such as, if necessary, loss or alteration of or fraudulent access to data, accidental transmission of viruses or of any other harmful element, loss of profits or opportunities, the cost of replacement goods and services or the attitude and behavior of a third party.

### 🛠️ MCP Tools

**Search & Discovery:**
- `search_instruments` - Find stocks, funds, ETFs by name or symbol
- `get_instrument_by_isin` - Look up instruments by ISIN code

**Stock Analysis:**
- `get_stock_info` - Complete stock information with fundamentals
- `get_stock_quote` - Real-time price and volume data
- `get_stock_analysis` - Analyst ratings and financial ratios
- `get_stock_chart` - Historical OHLC price data
- `get_orderbook` - Order book depth with bid/ask levels
- `get_marketplace_info` - Trading hours and market status
- `get_recent_trades` - Latest executed trades
- `get_broker_trade_summary` - Broker buy/sell activity

**Fund Analysis:**
- `get_fund_info` - Complete fund information
- `get_fund_sustainability` - ESG scores and sustainability metrics
- `get_fund_chart` - Historical performance charts
- `get_fund_chart_periods` - Performance across all time periods
- `get_fund_description` - Detailed fund description

### 📄 MCP Resources

- `avanza://stock/{id}` - Stock information as formatted markdown
- `avanza://fund/{id}` - Fund information as formatted markdown

### 💡 MCP Prompts

- `analyze_stock` - Comprehensive stock analysis workflow
- `compare_funds` - Multi-fund comparison template
- `screen_dividend_stocks` - Dividend stock screening

## 🚀 Quick Start

### Configuration for MCP Clients

For Claude Desktop or other MCP clients, add to your configuration:

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
### Usage in Claude Desktop

Once configured, you can ask Claude:

- "Search for Volvo stock on Avanza"
- "Get the latest stock quote for Ericsson"
- "Show me sustainable Swedish funds"
- "What's in the order book for H&M?"
- "Compare the performance of these three funds"


## 📄 License

See [LICENSE.md](LICENSE.md) for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

