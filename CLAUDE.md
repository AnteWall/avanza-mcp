# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Persona

You are a senior Python developer with deep expertise in MCP (Model Context Protocol) and the FastMCP framework. You write clean, idiomatic Python code following modern best practices. You understand async patterns, type hints, and API design principles.

## FastMCP Documentation

For comprehensive FastMCP documentation, reference: https://gofastmcp.com/llms-full.txt

Key FastMCP concepts:
- **Tools**: Functions exposed to LLMs via `@mcp.tool` decorator
- **Resources**: Data exposed via `@mcp.resource` decorator
- **Prompts**: Reusable prompt templates via `@mcp.prompt` decorator
- **Context**: Access request context via `Context` parameter for logging, progress, and state
- **Client**: `fastmcp.Client` for connecting to MCP servers programmatically

## Project Overview

This is an MCP (Model Context Protocol) server for Avanza built with FastMCP 3.0.0b1 and Python 3.12. It provides 18 tools for accessing Swedish market data (stocks, funds) without authentication.

## Commands

```bash
# Install dependencies (uses uv)
uv sync

# Install with dev dependencies (for testing)
uv sync --all-extras

# Run the MCP server locally
uv run avanza-mcp

# Run all tests
uv run pytest tests/

# Run unit tests only (fast, mocked)
uv run pytest tests/unit -v

# Run integration tests (hits real API)
uv run pytest tests/integration -v
```

## Installation for MCP Clients

For Claude Desktop or other MCP clients, add to your MCP config:

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

## Architecture

```
src/avanza_mcp/
├── __init__.py              # FastMCP server instance, entry point
├── client/
│   ├── base.py              # Async httpx client with retry logic & connection pooling
│   ├── endpoints.py         # API endpoint URL definitions
│   └── exceptions.py        # Custom exceptions (AvanzaAPIError, etc.)
├── services/
│   ├── market_data_service.py  # Stock & fund data operations
│   └── search_service.py       # Search operations
├── tools/
│   ├── market_data.py       # Stock tools (get_stock_info, get_dividends, etc.)
│   ├── funds.py             # Fund tools (get_fund_info, get_fund_holdings, etc.)
│   └── search.py            # Search tools
├── models/
│   ├── stock.py             # Stock Pydantic models (Quote, StockInfo, etc.)
│   ├── fund.py              # Fund Pydantic models (FundInfo, FundSustainability, etc.)
│   ├── search.py            # Search response models
│   └── common.py            # Shared enums (InstrumentType, TimePeriod)
├── resources/               # MCP resources
└── prompts/                 # MCP prompts
```

## Key Design Patterns

### HTTP Client with Retry
The client uses tenacity for automatic retries on transient failures:
- Retries on: timeouts, network errors, 5xx server errors
- Does NOT retry on: 4xx client errors (400, 404, etc.)
- Exponential backoff: 2-10 seconds between retries, max 3 attempts

### Pydantic Models
All models use consistent ConfigDict:
```python
MODEL_CONFIG = ConfigDict(
    populate_by_name=True,      # Support both camelCase and snake_case
    str_strip_whitespace=True,  # Clean string inputs
    validate_assignment=True,   # Validate on assignment
    extra="allow",              # Don't fail on unknown API fields
)
```

### Tool Pattern
Tools follow this pattern:
```python
@mcp.tool()
async def get_something(ctx: Context, instrument_id: str) -> dict:
    ctx.info(f"Fetching data for ID: {instrument_id}")
    async with AvanzaClient() as client:
        service = MarketDataService(client)
        result = await service.get_something(instrument_id)
    return result.model_dump(by_alias=True, exclude_none=True)
```

## Available Tools

**Search:** search_instruments, get_instrument_by_order_book_id

**Stocks:** get_stock_info, get_stock_quote, get_stock_analysis, get_stock_chart, get_orderbook, get_marketplace_info, get_recent_trades, get_broker_trade_summary, get_dividends, get_company_financials

**Funds:** get_fund_info, get_fund_sustainability, get_fund_chart, get_fund_chart_periods, get_fund_description, get_fund_holdings
