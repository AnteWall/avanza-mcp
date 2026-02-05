"""Usage guide resources for AI callers."""

from .. import mcp

USAGE_GUIDE = """# Avanza MCP Server - Usage Guide for AI Assistants

## 🎯 Critical: When NOT to Use MCP Tools

### MCP Tools Are For Interactive Exploration, NOT Bulk Data Processing

**Use MCP tools for**:
- ✅ Single instrument lookups (1-5 items)
- ✅ Small comparisons (2-10 instruments)
- ✅ Quick searches and exploration
- ✅ Interactive data analysis

**DO NOT use MCP tools for**:
- ❌ Fetching data for 50+ instruments
- ❌ Bulk screening operations
- ❌ Large-scale data analysis
- ❌ Building datasets

## 📏 The Threshold Rule

| Number of Items | Action |
|----------------|---------|
| 1-20 items | Use MCP tools directly |
| 20-50 items | Ask user if they want to continue with tools OR get a script |
| 50+ items | **DO NOT USE MCP TOOLS** - Provide a script instead |

## 🚫 Common Anti-Pattern (DON'T DO THIS)

```
User: "Analyze the top 100 Swedish stocks"

❌ BAD Response:
for stock_id in top_100_stocks:
    get_stock_info(stock_id)  # This will make 100 MCP calls!
    get_stock_chart(stock_id)  # Another 100 calls!
```

**Problem**: This creates 200+ MCP tool calls, which is:
- Slow and inefficient
- Overloads the MCP connection
- Not what MCP tools are designed for

## ✅ Correct Approach for Large Data Fetching

### Option 1: Provide a Python Script

```python
User: "Analyze the top 100 Swedish stocks"

✅ GOOD Response:
"For analyzing 100 stocks, you should fetch the data directly using a script
rather than MCP tools. Here's a Python script you can run:

```python
import httpx
import asyncio
import json

async def fetch_stock_info(client, stock_id):
    url = f"https://www.avanza.se/_api/market-guide/stock/{stock_id}"
    response = await client.get(url)
    return response.json()

async def main():
    stock_ids = ["5247", "5361", ...]  # Your 100 stock IDs

    async with httpx.AsyncClient() as client:
        tasks = [fetch_stock_info(client, sid) for sid in stock_ids]
        results = await asyncio.gather(*tasks)

    # Save to file
    with open('stocks_data.json', 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Fetched {len(results)} stocks")

asyncio.run(main())
```

This will efficiently fetch all 100 stocks in parallel and save to a JSON file."
```

### Option 2: Provide curl Commands

```bash
User: "Get data for 50 certificates"

✅ GOOD Response:
"For fetching 50 certificates, use the filter endpoint directly with a script:

```bash
# Get all certificates at once with pagination
curl 'https://www.avanza.se/_api/market-certificate-filter/' \\
  -H 'Content-Type: application/json' \\
  --data-raw '{
    "filter": {},
    "offset": 0,
    "limit": 50,
    "sortBy": {"field": "name", "order": "asc"}
  }' > certificates.json

# For more than 50, fetch next page:
curl 'https://www.avanza.se/_api/market-certificate-filter/' \\
  -H 'Content-Type: application/json' \\
  --data-raw '{
    "filter": {},
    "offset": 50,
    "limit": 50,
    "sortBy": {"field": "name", "order": "asc"}
  }' >> certificates.json
```

This fetches the data directly from Avanza's public API."
```

### Option 3: Provide a Shell Script for Multiple Items

```bash
User: "Get stock info for these 100 companies"

✅ GOOD Response:
"Here's a shell script to fetch data for all 100 stocks:

```bash
#!/bin/bash

# Array of stock IDs
stock_ids=(5247 5361 5239 ...)  # All 100 IDs

# Create output directory
mkdir -p stock_data

# Fetch each stock
for id in "${stock_ids[@]}"; do
  echo "Fetching stock $id..."
  curl -s "https://www.avanza.se/_api/market-guide/stock/$id" \\
    > "stock_data/stock_$id.json"
  sleep 0.5  # Be nice to the API
done

echo "Done! Data saved in stock_data/"
```

Run with: `chmod +x fetch_stocks.sh && ./fetch_stocks.sh`"
```

## 📋 API Endpoint Reference (For Script Writing)

When instructing users to write scripts, these are the public endpoints:

### Search & Discovery
```bash
# Search instruments
curl 'https://www.avanza.se/_api/search/filtered-search' \\
  -H 'Content-Type: application/json' \\
  --data-raw '{"query": "Tesla", "instrumentTypes": ["STOCK"]}'
```

### Stock Data
```bash
# Stock info
curl 'https://www.avanza.se/_api/market-guide/stock/{id}'

# Stock quote
curl 'https://www.avanza.se/_api/market-guide/stock/{id}/quote'

# Stock chart
curl 'https://www.avanza.se/_api/price-chart/stock/{id}?timePeriod=one_month'

# Order book
curl 'https://www.avanza.se/_api/market-guide/stock/{id}/orderdepth'
```

### Filter Endpoints (Bulk Operations)
```bash
# Filter certificates (POST request)
curl 'https://www.avanza.se/_api/market-certificate-filter/' \\
  -H 'Content-Type: application/json' \\
  --data-raw '{
    "filter": {"directions": ["long"]},
    "offset": 0,
    "limit": 100,
    "sortBy": {"field": "name", "order": "asc"}
  }'

# Filter ETFs (POST request)
curl 'https://www.avanza.se/_api/market-etf-filter/' \\
  -H 'Content-Type: application/json' \\
  --data-raw '{
    "filter": {"exposures": ["usa"]},
    "offset": 0,
    "limit": 100,
    "sortBy": {"field": "managementFee", "order": "asc"}
  }'

# Filter warrants (POST request)
curl 'https://www.avanza.se/_api/market-warrant-filter/' \\
  -H 'Content-Type: application/json' \\
  --data-raw '{
    "filter": {"subTypes": ["TURBO"]},
    "offset": 0,
    "limit": 100,
    "sortBy": {"field": "name", "order": "asc"}
  }'
```

### Fund Data
```bash
# Fund info
curl 'https://www.avanza.se/_api/fund-guide/guide/{id}'

# Fund chart
curl 'https://www.avanza.se/_api/fund-guide/chart/{id}/three_years'
```

## 🔄 Decision Tree: Tool vs Script

```
User request → Count number of items needed
    │
    ├─ 1-20 items? → Use MCP tools directly
    │
    ├─ 20-50 items? → Ask user:
    │   "This will require ~{count} API calls. Would you like me to:
    │    1. Proceed with MCP tools (slower, interactive)
    │    2. Provide a script for you to run (faster, bulk)"
    │
    └─ 50+ items? → ALWAYS provide script
        │
        ├─ User is technical? → Python script with async
        ├─ User wants simple? → Bash script with curl
        └─ User wants data file? → curl command + jq
```

## 🎓 Examples of Correct Responses

### Example 1: Small Request (Use Tools)

```
User: "What's the current price of Volvo?"

✅ Response:
search_instruments(query="Volvo B", instrument_types=["STOCK"])
get_stock_quote(instrument_id="5247")
"Volvo B is currently trading at 265.40 SEK, up 1.2%"
```

### Example 2: Medium Request (Ask User)

```
User: "Compare these 30 ETFs"

✅ Response:
"Comparing 30 ETFs will require approximately 60 API calls through MCP tools.
I have two options for you:

1. **Use MCP Tools** (slower, ~2-3 minutes):
   I'll fetch each ETF's data interactively. Good if you want to explore
   the data step-by-step.

2. **Provide a Script** (faster, ~30 seconds):
   I'll give you a Python script that fetches all 30 ETFs in parallel,
   saves to JSON, and you can analyze the results.

Which would you prefer?"
```

### Example 3: Large Request (Provide Script)

```
User: "Analyze all Swedish stocks with market cap > 1B SEK"

✅ Response:
"To analyze 100+ stocks efficiently, you should fetch the data directly
rather than using MCP tools. Here's a Python script:

```python
import httpx
import asyncio
import pandas as pd

async def fetch_stock(client, stock_id):
    try:
        response = await client.get(
            f"https://www.avanza.se/_api/market-guide/stock/{stock_id}"
        )
        return response.json()
    except Exception as e:
        print(f"Error fetching {stock_id}: {e}")
        return None

async def main():
    # First, get Swedish stock IDs (you'd need to search or have a list)
    stock_ids = [...]  # Your list of stock IDs

    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = [fetch_stock(client, sid) for sid in stock_ids]
        results = await asyncio.gather(*tasks)

    # Filter for market cap > 1B
    large_caps = [
        s for s in results
        if s and s.get('company', {}).get('marketCapital', 0) > 1_000_000_000
    ]

    # Convert to DataFrame for analysis
    df = pd.DataFrame([{
        'name': s['name'],
        'price': s['quote']['last'],
        'market_cap': s['company']['marketCapital'],
        'pe_ratio': s.get('keyIndicators', {}).get('priceEarningsRatio'),
    } for s in large_caps])

    df.to_csv('large_cap_stocks.csv', index=False)
    print(f"Analyzed {len(large_caps)} large-cap stocks")
    print(df.head())

asyncio.run(main())
```

Save this as `analyze_stocks.py` and run with:
```bash
pip install httpx pandas
python analyze_stocks.py
```

After running this, I can help you analyze the results in `large_cap_stocks.csv`."
```

## 💡 Key Principles

1. **MCP tools = Interactive exploration** (1-20 items)
2. **Scripts = Bulk data processing** (50+ items)
3. **Always explain why** you're recommending a script over tools
4. **Provide working code** that users can run immediately
5. **Include error handling** in scripts (timeouts, retries)
6. **Be nice to the API** (rate limiting, delays)

## 🚀 Script Templates You Can Use

### Python: Async Bulk Fetcher
```python
import httpx
import asyncio

async def fetch_data(url):
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30.0)
        return response.json()

async def bulk_fetch(urls):
    tasks = [fetch_data(url) for url in urls]
    return await asyncio.gather(*tasks, return_exceptions=True)

# Usage
urls = [f"https://www.avanza.se/_api/market-guide/stock/{i}" for i in stock_ids]
results = asyncio.run(bulk_fetch(urls))
```

### Bash: Simple Sequential Fetcher
```bash
#!/bin/bash
for id in $(cat stock_ids.txt); do
  curl -s "https://www.avanza.se/_api/market-guide/stock/$id" \\
    > "data/stock_$id.json"
  sleep 0.5
done
```

### curl + jq: Filter and Extract
```bash
# Fetch and extract just the fields you need
curl -s 'https://www.avanza.se/_api/market-certificate-filter/' \\
  -H 'Content-Type: application/json' \\
  --data-raw '{"filter":{},"offset":0,"limit":100,"sortBy":{"field":"name","order":"asc"}}' \\
  | jq '.certificates[] | {name, orderbookId, leverage, direction}'
```

## ⚠️ Important Reminders

- **No authentication required** - All endpoints shown are public
- **Rate limiting** - Add delays (0.5-1s) between requests in loops
- **Timeout handling** - Use appropriate timeouts (10-30s)
- **Error handling** - Check for HTTP errors and null responses
- **Respect the API** - Don't hammer the servers with concurrent requests

## 📊 Summary

| Scenario | Items | Action |
|----------|-------|--------|
| Quick lookup | 1-5 | Use MCP tools |
| Comparison | 5-20 | Use MCP tools |
| Small screening | 20-50 | Ask user preference |
| Bulk screening | 50-200 | Provide script |
| Large analysis | 200+ | Provide script + pagination guide |

**Golden Rule**: If you're thinking about calling the same tool in a loop more than 20 times, provide a script instead.
"""


@mcp.resource("avanza://docs/usage")
async def get_usage_guide() -> str:
    """Get comprehensive usage guide for AI assistants.

    URI: avanza://docs/usage

    This resource provides critical guidance on:
    - When to use MCP tools (small, interactive queries)
    - When to provide scripts instead (bulk data fetching)
    - How to write curl commands and Python scripts for users
    - API endpoint reference for script writing

    Returns:
        Markdown-formatted usage guide
    """
    return USAGE_GUIDE


@mcp.resource("avanza://docs/quick-start")
async def get_quick_start() -> str:
    """Get quick start guide focused on tool vs script decision.

    URI: avanza://docs/quick-start

    Returns:
        Quick reference guide
    """
    return """# Avanza MCP - Quick Decision Guide

## 🚦 When to Use What

### Use MCP Tools (✅)
- Single lookups: "What's Tesla's price?"
- Small comparisons: "Compare these 5 funds"
- Quick exploration: "Find ETFs with USA exposure"
- Interactive analysis: Step-by-step investigation

### Provide Script (📝)
- Bulk operations: "Analyze 100 stocks"
- Large screenings: "Get all certificates"
- Dataset building: "Fetch all Swedish funds"
- Repeated operations: "Daily price monitoring"

## 📏 The Rule

```
if items > 50:
    provide_script()
elif items > 20:
    ask_user_preference()
else:
    use_mcp_tools()
```

## 🔧 Quick Script Templates

### Fetch Multiple Stocks (Python)
```python
import httpx
import asyncio

async def main():
    stock_ids = ["5247", "5361", ...]
    async with httpx.AsyncClient() as client:
        for sid in stock_ids:
            r = await client.get(f"https://www.avanza.se/_api/market-guide/stock/{sid}")
            print(r.json()['name'], r.json()['quote']['last'])

asyncio.run(main())
```

### Bulk Filter (curl)
```bash
curl 'https://www.avanza.se/_api/market-etf-filter/' \\
  -H 'Content-Type: application/json' \\
  --data-raw '{"filter":{},"offset":0,"limit":100,"sortBy":{"field":"name","order":"asc"}}'
```

## 💭 Example Responses

**User**: "Check Volvo stock"
**You**: ✅ Use `get_stock_quote("5247")`

**User**: "Compare 10 funds"
**You**: ✅ Use `get_fund_info()` for each

**User**: "Analyze 80 Swedish stocks"
**You**: 📝 "Here's a Python script to fetch all 80 stocks..."

**User**: "Screen all ETFs"
**You**: 📝 "Here's a curl command using filter_etfs endpoint..."

## 🎯 Remember

MCP = Interactive exploration (1-20 items)
Script = Bulk processing (50+ items)

Read full guide: `avanza://docs/usage`
"""
