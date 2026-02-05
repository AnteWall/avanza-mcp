"""Workflow prompt templates emphasizing when to provide scripts vs using tools."""

from .. import mcp


@mcp.prompt()
def bulk_data_script_guide(item_count: int, operation_type: str) -> str:
    """Guide for providing scripts for bulk data operations.

    Use this when user requests data for 50+ items.

    Args:
        item_count: Number of items to fetch
        operation_type: Type of operation (e.g., "stock analysis", "ETF screening")

    Returns:
        Prompt explaining why and how to provide a script
    """
    return f"""For {operation_type} involving {item_count} items, I should provide a script instead of using MCP tools.

## Why Not Use MCP Tools?

Making {item_count} MCP tool calls would:
- Take 5-10 minutes to complete
- Overload the MCP connection
- Be inefficient and error-prone

## What to Provide Instead

I'll give you a ready-to-run script that:
- Fetches all {item_count} items in parallel (30-60 seconds)
- Saves data to a file for analysis
- Includes error handling and rate limiting

### Python Script Template (Recommended)
```python
import httpx
import asyncio
import json
from datetime import datetime

async def fetch_item(client, item_id):
    \"\"\"Fetch single item with error handling.\"\"\"
    try:
        url = "https://www.avanza.se/_api/..."  # Specific endpoint
        response = await client.get(url, timeout=30.0)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching {{item_id}}: {{e}}")
        return None

async def main():
    item_ids = [...]  # Your {item_count} IDs

    print(f"Fetching {{len(item_ids)}} items...")

    async with httpx.AsyncClient() as client:
        tasks = [fetch_item(client, iid) for iid in item_ids]
        results = await asyncio.gather(*tasks)

    # Filter out errors
    valid_results = [r for r in results if r is not None]

    # Save to file
    output_file = f"data_{{datetime.now().strftime('%Y%m%d_%H%M%S')}}.json"
    with open(output_file, 'w') as f:
        json.dump(valid_results, f, indent=2)

    print(f"✅ Fetched {{len(valid_results)}}/{{len(item_ids)}} items")
    print(f"📁 Saved to {{output_file}}")

if __name__ == "__main__":
    asyncio.run(main())
```

### How to Run
```bash
# Install dependencies
pip install httpx

# Run the script
python fetch_data.py

# Analyze the results
# I can help you analyze the JSON file after you run this!
```

## Next Steps

After you run the script:
1. Share the output file with me (or key findings)
2. I can help analyze patterns, create visualizations, etc.
3. We can drill down into specific interesting items using MCP tools
"""


@mcp.prompt()
def decide_tool_or_script(user_request: str, estimated_items: int) -> str:
    """Help decide whether to use tools or provide a script.

    Args:
        user_request: What the user wants to do
        estimated_items: Estimated number of items to process

    Returns:
        Decision prompt
    """
    if estimated_items <= 20:
        approach = "use MCP tools"
        reason = "small enough for interactive exploration"
    elif estimated_items <= 50:
        approach = "ask user preference"
        reason = "medium size - tools work but script is faster"
    else:
        approach = "provide script"
        reason = "too many for MCP tools - script is much more efficient"

    return f"""Request: "{user_request}"
Estimated items: {estimated_items}

## Decision: {approach.upper()}

**Reason**: {reason}

**Approach**:
{"I'll use MCP tools to fetch data interactively." if estimated_items <= 20 else
 "I'll ask if you prefer tools (interactive) or script (faster)." if estimated_items <= 50 else
 "I'll provide a Python/bash script for efficient bulk fetching."}

{"" if estimated_items <= 20 else f'''
## Script Template

For {estimated_items} items, here's what I'll provide:

```python
# Efficient parallel fetching
import httpx
import asyncio

async def fetch_all(ids):
    async with httpx.AsyncClient() as client:
        tasks = [client.get(f"https://www.avanza.se/_api/.../{{id}}") for id in ids]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        return [r.json() for r in responses if hasattr(r, 'json')]

# Run and save
results = asyncio.run(fetch_all(your_{estimated_items}_ids))
```

This completes in ~30-60 seconds vs {estimated_items * 2}+ seconds with MCP tools.
'''}
"""


@mcp.prompt()
def filter_large_dataset(instrument_type: str, criteria: str) -> str:
    """Guide for filtering large datasets using API endpoints directly.

    Args:
        instrument_type: Type (certificates, etfs, warrants, etc.)
        criteria: Filtering criteria

    Returns:
        Prompt with curl/script for bulk filtering
    """
    filter_endpoints = {
        "certificates": "market-certificate-filter",
        "etfs": "market-etf-filter",
        "warrants": "market-warrant-filter",
    }

    endpoint = filter_endpoints.get(instrument_type.lower(), "market-etf-filter")

    return f"""To screen {instrument_type} with criteria: {criteria}

## Use the Filter API Directly (Don't Loop Through MCP Tools)

Instead of calling MCP tools repeatedly, use the filter endpoint:

### Option 1: curl Command (Quick & Simple)

```bash
curl 'https://www.avanza.se/_api/{endpoint}/' \\
  -H 'Content-Type: application/json' \\
  --data-raw '{{
    "filter": {{
      {{"// Add your filters here based on criteria"}}
    }},
    "offset": 0,
    "limit": 100,
    "sortBy": {{"field": "name", "order": "asc"}}
  }}' | jq '.' > results.json
```

### Option 2: Python Script (For Processing)

```python
import httpx
import json

def filter_{instrument_type}(filters, limit=100):
    \"\"\"Filter {instrument_type} directly via API.\"\"\"
    url = "https://www.avanza.se/_api/{endpoint}/"

    payload = {{
        "filter": filters,
        "offset": 0,
        "limit": limit,
        "sortBy": {{"field": "name", "order": "asc"}}
    }}

    response = httpx.post(url, json=payload, timeout=30.0)
    return response.json()

# Example: Apply your criteria
filters = {{
    # Map your criteria to filter parameters
}}

results = filter_{instrument_type}(filters, limit=100)

# Save
with open('{instrument_type}_filtered.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"Found {{results.get('totalNumberOfOrderbooks', 0)}} matches")
```

## Available Filter Parameters

**For {instrument_type}**:
{_get_filter_params(instrument_type)}

## Pagination for Large Results

If results exceed 100:

```bash
# Get next page
curl 'https://www.avanza.se/_api/{endpoint}/' \\
  -H 'Content-Type: application/json' \\
  --data-raw '{{
    "filter": {{}},
    "offset": 100,  # Next page
    "limit": 100,
    "sortBy": {{"field": "name", "order": "asc"}}
  }}'
```

## After Fetching

Once you have the results:
1. I can help analyze patterns in the data
2. Pick interesting items for deep dives using MCP tools
3. Create comparisons or visualizations
"""


def _get_filter_params(instrument_type: str) -> str:
    """Get filter parameters for instrument type."""
    params = {
        "certificates": """
- `directions`: ["long", "short"]
- `leverages`: [1.0, 2.0, 3.0, ...]
- `issuers`: ["Valour", "WisdomTree", ...]
- `underlyingInstruments`: [orderbookIds]
""",
        "etfs": """
- `exposures`: ["usa", "europe", "global", ...]
- `assetCategories`: ["stock", "bond", "commodity", ...]
- `riskScores`: ["risk_one", "risk_two", ...]
- `managementFee`: (use sortBy to filter)
""",
        "warrants": """
- `directions`: ["long", "short"]
- `subTypes`: ["TURBO", "MINI", ...]
- `issuers`: ["Societe Generale", ...]
- `underlyingInstruments`: [orderbookIds]
""",
    }
    return params.get(instrument_type.lower(), "Check API documentation")


@mcp.prompt()
def analyze_vs_fetch(operation_description: str, requires_bulk_data: bool) -> str:
    """Distinguish between analysis (use tools) and fetching (use scripts).

    Args:
        operation_description: What the user wants to do
        requires_bulk_data: Whether it needs 50+ items

    Returns:
        Guidance prompt
    """
    if requires_bulk_data:
        return f"""Operation: "{operation_description}"

## This Requires Bulk Data Fetching

### Two-Step Approach:

**Step 1: Fetch Data (You Do This)**
I'll provide a script to fetch the data:
- Runs in 30-60 seconds
- Saves to JSON/CSV file
- Handles errors gracefully

**Step 2: Analyze Data (I Help With This)**
After you have the data:
- Share the file or key metrics
- I'll use MCP tools for specific deep dives
- We can explore patterns together

### Why This Approach?

- **Efficient**: Parallel fetching vs sequential MCP calls
- **Reliable**: Better error handling, can resume if failed
- **Flexible**: You own the data for other analyses

### Script I'll Provide

```python
# Fast parallel data fetcher
import httpx, asyncio, json

async def fetch_all():
    ids = [...]  # Your list
    async with httpx.AsyncClient() as c:
        tasks = [c.get(f"https://www.avanza.se/_api/.../{{id}}") for id in ids]
        return await asyncio.gather(*tasks, return_exceptions=True)

results = asyncio.run(fetch_all())
with open('data.json', 'w') as f:
    json.dump([r.json() for r in results if hasattr(r, 'json')], f)
```

### Next: Share Results & Analyze Together
"""
    else:
        return f"""Operation: "{operation_description}"

## This Can Use MCP Tools Directly

I'll use MCP tools interactively because:
- Small enough dataset (< 20 items)
- Interactive exploration is valuable
- Results available immediately

I'll proceed with using the appropriate MCP tools for this analysis.
"""


@mcp.prompt()
def script_template_selector(
    task: str, data_source: str, output_format: str = "json"
) -> str:
    """Provide appropriate script template based on task.

    Args:
        task: What to accomplish
        data_source: Where to get data (endpoint type)
        output_format: Desired output format

    Returns:
        Complete script template
    """
    return f"""Task: {task}
Data Source: {data_source}
Output: {output_format}

## Recommended Script

```python
#!/usr/bin/env python3
\"\"\"
{task}

Fetches data from Avanza's public API and saves to {output_format}.
No authentication required.
\"\"\"

import httpx
import asyncio
import json
from pathlib import Path
from datetime import datetime

# Configuration
BASE_URL = "https://www.avanza.se/_api"
OUTPUT_DIR = Path("avanza_data")
MAX_CONCURRENT = 10  # Limit concurrent requests

async def fetch_item(client, item_id, semaphore):
    \"\"\"Fetch single item with rate limiting.\"\"\"
    async with semaphore:
        try:
            url = f"{{BASE_URL}}/{data_source}/{{item_id}}"
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            return {{"id": item_id, "data": response.json(), "error": None}}
        except Exception as e:
            return {{"id": item_id, "data": None, "error": str(e)}}

async def main():
    # TODO: Replace with your actual IDs
    item_ids = [
        # "5247",  # Example: Volvo
        # "5361",  # Example: Ericsson
        # Add your IDs here
    ]

    if not item_ids:
        print("⚠️  Please add item IDs to the script")
        return

    print(f"📊 Fetching {{len(item_ids)}} items...")

    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Rate limiting semaphore
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    # Fetch all items
    async with httpx.AsyncClient() as client:
        tasks = [fetch_item(client, iid, semaphore) for iid in item_ids]
        results = await asyncio.gather(*tasks)

    # Separate successful and failed
    successful = [r for r in results if r["error"] is None]
    failed = [r for r in results if r["error"] is not None]

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"results_{{timestamp}}.{output_format}"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            {{
                "metadata": {{
                    "timestamp": timestamp,
                    "total": len(item_ids),
                    "successful": len(successful),
                    "failed": len(failed),
                }},
                "data": [r["data"] for r in successful],
                "errors": [{{"id": r["id"], "error": r["error"]}} for r in failed],
            }},
            f,
            indent=2,
            ensure_ascii=False,
        )

    # Print summary
    print(f"\\n✅ Successfully fetched: {{len(successful)}}/{{len(item_ids)}}")
    if failed:
        print(f"❌ Failed: {{len(failed)}}")
        for fail in failed[:5]:  # Show first 5 errors
            print(f"   - {{fail['id']}}: {{fail['error']}}")
    print(f"\\n📁 Saved to: {{output_file}}")

if __name__ == "__main__":
    asyncio.run(main())
```

## How to Use

1. **Save the script**: `save as fetch_data.py`
2. **Add your IDs**: Edit the `item_ids` list
3. **Install dependency**: `pip install httpx`
4. **Run**: `python fetch_data.py`

## What You Get

- JSON file with all results
- Error tracking for failed requests
- Timestamp for record keeping
- Summary of success/failure rates

## After Running

Share the results file and I can help you:
- Analyze patterns
- Create visualizations
- Filter and sort data
- Deep dive on specific items
"""
