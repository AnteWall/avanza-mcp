"""Workflow prompts sharing tool/script guidance and fetch examples."""

from .. import mcp
from ..resources.usage import DECISION_GUIDE, bulk_script, filter_guide


@mcp.prompt()
def bulk_data_script_guide(item_count: int, operation_type: str) -> str:
    """Guide bulk operations with a bounded-concurrency script and error tracking.

    Args:
        item_count: Number of items to fetch
        operation_type: Type of operation, e.g. stock analysis or ETF screening
    """
    return (
        f"For {operation_type} involving {item_count} items, provide a script.\n\n"
        + DECISION_GUIDE
        + bulk_script()
    )


@mcp.prompt()
def decide_tool_or_script(user_request: str, estimated_items: int) -> str:
    """Choose tools, user preference, or a script based on the number of items.

    Args:
        user_request: What the user wants to do
        estimated_items: Estimated number of items to process
    """
    if estimated_items <= 20:
        approach = "use MCP tools"
        reason = "small enough for interactive exploration"
    elif estimated_items <= 50:
        approach = "ask user preference"
        reason = "medium size - tools work but a script can fetch in bulk"
    else:
        approach = "provide script"
        reason = "bulk fetching avoids repeated individual MCP calls"

    return (
        f'Request: "{user_request}"\nEstimated items: {estimated_items}\n\n'
        f"## Decision: {approach.upper()}\n\nReason: {reason}\n\n"
        + DECISION_GUIDE
        + (bulk_script() if estimated_items > 20 else "")
    )


@mcp.prompt()
def filter_large_dataset(instrument_type: str, criteria: str) -> str:
    """Provide filter API examples and pagination guidance instead of per-item calls.

    Args:
        instrument_type: Type, e.g. certificates, etfs, or warrants
        criteria: Filtering criteria
    """
    filter_endpoints = {
        "certificates": "market-certificate-filter",
        "etfs": "market-etf-filter",
        "warrants": "market-warrant-filter",
    }
    endpoint = filter_endpoints.get(instrument_type.lower(), "market-etf-filter")
    return (
        f"Screen {instrument_type} with criteria: {criteria}\n\n"
        + filter_guide(endpoint)
        + f"\n## Available Filter Parameters\n{_get_filter_params(instrument_type)}"
        + "\nAnalyze the results, then use MCP tools for selected instruments."
    )


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
- `managementFee`: (use sortBy to order)
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
    """Distinguish interactive analysis from bulk fetching followed by analysis.

    Args:
        operation_description: What the user wants to do
        requires_bulk_data: Whether it needs bulk data
    """
    return (
        f'Operation: "{operation_description}"\n\n'
        + (
            "Fetch with a script, then analyze the saved results.\n\n" + bulk_script()
            if requires_bulk_data
            else "Use MCP tools directly for interactive analysis.\n"
        )
    )


@mcp.prompt()
def script_template_selector(
    task: str, data_source: str, output_format: str = "json"
) -> str:
    """Provide a bulk-fetch template for the requested endpoint and output file.

    Args:
        task: What to accomplish
        data_source: Endpoint path relative to /_api, before the instrument ID
        output_format: Desired output format; adapt the JSON serializer if needed
    """
    return (
        f"Task: {task}\nData Source: {data_source}\nOutput: {output_format}\n\n"
        + bulk_script(data_source, output_format)
    )
