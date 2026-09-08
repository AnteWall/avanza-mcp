"""Usage guide resources and shared workflow examples for AI callers."""

from .. import mcp

DECISION_GUIDE = """## Tools or Scripts?

| Number of items | Action |
|-----------------|--------|
| 1-20 | Use MCP tools for interactive exploration |
| 21-50 | Ask whether the user prefers tools or a script |
| More than 50 | Provide a script for bulk fetching |

Use tools for individual quotes, small comparisons, and follow-up analysis.
Use scripts for datasets and repeated bulk operations instead of hundreds of
individual MCP calls. Explain the choice, fetch the data, then analyze the output
and use tools for specific deep dives.

Examples: check Volvo with a tool; compare 10 funds interactively; ask before
comparing 30 ETFs; provide a bulk-fetch script for 100 stocks.
"""


def bulk_script(data_source: str = "market-guide/stock", output_format: str = "json") -> str:
    """Return the shared bounded-concurrency fetcher with JSON output."""
    return f"""## Python Bulk Fetcher

Replace the IDs and endpoint path for the task. The template writes JSON;
adapt the serializer if another output format is requested.
Install `httpx`, then run `python fetch_data.py`.

```python
import asyncio
import json
from datetime import datetime
from pathlib import Path

import httpx

BASE_URL = "https://www.avanza.se/_api"
DATA_SOURCE = {data_source!r}
OUTPUT_FORMAT = {output_format!r}
OUTPUT_DIR = Path("avanza_data")
MAX_CONCURRENT = 10

async def fetch_item(client, item_id, semaphore):
    async with semaphore:
        try:
            response = await client.get(f"{{BASE_URL}}/{{DATA_SOURCE}}/{{item_id}}")
            response.raise_for_status()
            return {{"id": item_id, "data": response.json(), "error": None}}
        except Exception as error:
            return {{"id": item_id, "data": None, "error": str(error)}}

async def main():
    item_ids = []  # Add Avanza instrument IDs here.
    if not item_ids:
        print("Add instrument IDs before running.")
        return

    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    async with httpx.AsyncClient(timeout=30.0) as client:
        results = await asyncio.gather(
            *(fetch_item(client, item_id, semaphore) for item_id in item_ids)
        )
    successful = [r for r in results if r["error"] is None]
    failed = [r for r in results if r["error"] is not None]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_file = OUTPUT_DIR / f"results_{{timestamp}}.{{OUTPUT_FORMAT}}"
    with output_file.open("w", encoding="utf-8") as output:
        json.dump({{
            "metadata": {{"timestamp": timestamp, "total": len(item_ids),
                         "successful": len(successful), "failed": len(failed)}},
            "data": [r["data"] for r in successful],
            "errors": [{{"id": r["id"], "error": r["error"]}} for r in failed],
        }}, output, indent=2, ensure_ascii=False)
    print(f"Fetched {{len(successful)}}/{{len(item_ids)}}; saved to {{output_file}}")
    for failure in failed[:5]:
        print(f"{{failure['id']}}: {{failure['error']}}")

if __name__ == "__main__":
    asyncio.run(main())
```

Limit concurrency and reduce it if the API rate-limits requests. For sequential
loops, allow 0.5-1 seconds between requests. Keep timeouts, check HTTP errors,
and retain failed IDs for a later retry rather than silently dropping them.
"""


def filter_guide(endpoint: str = "market-etf-filter") -> str:
    """Return shared curl/Python filtering and pagination examples."""
    return f"""## Bulk Filtering

Set `filter` to the desired criteria; use `sortBy` for ordering.

```bash
curl --fail 'https://www.avanza.se/_api/{endpoint}/' \\
  -H 'Content-Type: application/json' \\
  --data-raw '{{"filter":{{}},"offset":0,"limit":100,"sortBy":{{"field":"name","order":"asc"}}}}' \\
  > results.json
```

For Python processing:

```python
import json
import httpx

payload = {{"filter": {{}}, "offset": 0, "limit": 100,
           "sortBy": {{"field": "name", "order": "asc"}}}}
response = httpx.post({('https://www.avanza.se/_api/' + endpoint + '/')!r},
                      json=payload, timeout=30.0)
response.raise_for_status()
results = response.json()
with open("results.json", "w", encoding="utf-8") as output:
    json.dump(results, output, indent=2)
print(f"Found {{results.get('totalNumberOfOrderbooks', 0)}} matches")
```

For the next page, keep the filters and sorting unchanged and increase `offset`
by `limit` (0, 100, 200, ...). Store pages separately or merge their result arrays;
do not append whole JSON documents into one JSON file. Stop when results are
exhausted. Use `jq` or Python to select fields for analysis.
"""


USAGE_GUIDE = "# Avanza MCP Server - Usage Guide\n\n" + DECISION_GUIDE + """
## Public Endpoint Reference

No authentication is required. Paths below are relative to
`https://www.avanza.se/_api`.

| Data | Method | Path |
|------|--------|------|
| Search | POST | `/search/filtered-search` |
| Stock info | GET | `/market-guide/stock/{id}` |
| Stock quote | GET | `/market-guide/stock/{id}/quote` |
| Stock chart | GET | `/price-chart/stock/{id}?timePeriod=one_month` |
| Order book | GET | `/market-guide/stock/{id}/orderdepth` |
| Certificates | POST | `/market-certificate-filter/` |
| ETFs | POST | `/market-etf-filter/` |
| Warrants | POST | `/market-warrant-filter/` |
| Fund info | GET | `/fund-guide/guide/{id}` |
| Fund chart | GET | `/fund-guide/chart/{id}/three_years` |

For search, send a JSON body such as `{"query":"Tesla","instrumentType":"STOCK"}`.
Filter examples: certificates `{"directions":["long"]}`, ETFs
`{"exposures":["usa"]}`, and warrants `{"subTypes":["TURBO"]}`.
ETF fees can be ordered with `sortBy: {"field":"managementFee","order":"asc"}`.

For a simple shell alternative, loop through known IDs, use `curl --fail` on the
stock-info endpoint, save each response separately, and sleep between requests.
For tabular output, extract the desired fields from the saved JSON and write CSV.
""" + bulk_script() + filter_guide()


@mcp.resource("avanza://docs/usage")
async def get_usage_guide() -> str:
    """Get tool/script guidance, public endpoints, and bulk-fetch examples."""
    return USAGE_GUIDE


@mcp.resource("avanza://docs/quick-start")
async def get_quick_start() -> str:
    """Get quick tool/script guidance and a bulk-filter example."""
    return (
        "# Avanza MCP - Quick Decision Guide\n\n"
        + DECISION_GUIDE
        + filter_guide()
        + "\nRead `avanza://docs/usage` for the Python fetcher and endpoint reference."
    )
