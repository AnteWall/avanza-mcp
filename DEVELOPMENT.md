# Development Guide

## Setup

Requires Python >=3.12 and [uv](https://docs.astral.sh/uv/). FastMCP is pinned to
3.4.7. Run from the repository root:

```bash
uv sync --all-extras
uv run avanza-mcp
```

The application entry point defaults to local stdio. For a local MCP client that
launches a subprocess, use its documented configuration format. A common format is:

```json
{
  "mcpServers": {
    "avanza-dev": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/avanza-mcp", "run", "avanza-mcp"]
    }
  }
}
```

Do not write diagnostic output to stdout on stdio transport.

For HTTP using the [FastMCP v3 CLI](https://gofastmcp.com/v3/getting-started/quickstart):

```bash
uv run fastmcp run src/avanza_mcp/__init__.py:mcp --transport http
```

This starts a transport endpoint; it does not deploy a hosted service. A ChatGPT
remote connection needs a separate reachable deployment, not a local stdio command.
Public upstream endpoints need no account authentication; remote MCP access controls
are deployment-specific, not implied by upstream public access.

## Tests

```bash
uv run pytest tests/unit/test_workflows.py -v
uv run pytest tests/unit -v
uv run pytest tests/integration -v
```

Unit tests use mocks or an in-process FastMCP client. Integration tests contact the
real public API and can be affected by upstream availability or schema changes.
Offline transport checks also start a stdio subprocess and a loopback HTTP server;
neither makes upstream API calls. Release publishing is gated on the unit suite.
The guidance test checks rendered prompts, JSON list validation, the 34-tool /
3-prompt inventory, two static Markdown resources and two instrument templates.

## Public Contract

v2 uses `order_book_id` for public tool ID inputs, without an `instrument_id`
compatibility alias. Resource templates also use `{order_book_id}`. Search hits are
compact typed discovery records from at most 50 candidates; matching candidate
totals differ from `upstreamTotalNumberOfHits`. Most other keys remain upstream names.
Upstream-model JSON omits absent optional fields and preserves explicit null/zero/false.

All charts (fund included), owners and short selling use `data` plus `pagination`;
trades use `trades` plus `pagination`. Analysis/dividends/financials require `metric`
and return one series at `data[selection][metric]`, with `available_metrics` and
pagination. Use documented names such as `priceEarningsRatio` for stock ratios,
not invented probes. History pages default to offset=0 and limit=20 (charts: 100),
with limits 1..100.

Local history pagination bounds MCP output, not upstream traffic: each page call
refetches the source payload. The lifespan HTTP pool enables connection reuse, not
a data cache; no data cache is added. Separate pages can see changed snapshots.
Source metadata describes the full source period/history, not necessarily the page.
Fund-guide flat `development*` fields and `productFee`/`managementFee` retain source
scales; do not equate them with fund-period `change` or assume chart `y` is NAV/return.

Keep public type annotations accurate: FastMCP derives input/output schemas from
Python signatures and return annotations. A Python consumer should inspect the
registered `inputSchema`/`outputSchema` and use structured tool results rather than
scraping human-readable text. Do not claim that every upstream field has a known
unit, that a generic dictionary describes a stable typed payload, or that a
requested chart period guarantees complete daily data.

Prompt arguments are strings in MCP. FastMCP decodes JSON strings for `list[str]`:

```python
result = await client.get_prompt(
    "compare_funds", {"fund_names": '["Avanza Zero", "Avanza Global"]'}
)
```

Its Python client can also serialize native lists; other clients may not. No
prompt-to-tool transform is enabled, so clients without prompt support use tools
directly. Keep validation and rendered-content tests at this boundary. Templates
and static usage resources use `text/markdown`; essential behavior belongs in
server instructions, not only optional resources.

FastMCP's Python client may warn that its inferred Decimal-string regex is not
supported by Pydantic's regex engine. Server-side Decimal validation and JSON
Schema checks still apply; JSON Decimal values are strings. Client-side type
inference is not a substitute for validating structured results.
