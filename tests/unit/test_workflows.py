"""Offline checks for the shared prompt and resource guidance."""

import ast
import re

import pytest
from fastmcp import Client

from avanza_mcp import mcp
from avanza_mcp.prompts import workflows
from avanza_mcp.resources.usage import DECISION_GUIDE, bulk_script, filter_guide


@pytest.mark.parametrize("count, decision", [
    (20, "USE MCP TOOLS"), (21, "ASK USER PREFERENCE"),
    (50, "ASK USER PREFERENCE"), (51, "PROVIDE SCRIPT"),
])
def test_decision_boundaries(count, decision):
    text = workflows.decide_tool_or_script("Compare funds", count)
    assert f"## Decision: {decision}" in text
    assert DECISION_GUIDE in text
    assert (bulk_script() in text) == (count > 20)


def test_workflows_reuse_valid_script_examples():
    assert bulk_script() in workflows.bulk_data_script_guide(100, "stock analysis")
    assert bulk_script() in workflows.analyze_vs_fetch("Fetch stocks", True)
    assert "```python" not in workflows.analyze_vs_fetch("Compare funds", False)
    text = workflows.script_template_selector("Fetch", "market-guide/stock", "json")
    assert bulk_script("market-guide/stock", "json") in text
    for kind in ("certificates", "etfs", "warrants"):
        filtered = workflows.filter_large_dataset(kind.upper(), "long exposure")
        assert "long exposure" in filtered
        assert workflows._get_filter_params(kind) in filtered
        assert f"market-{kind[:-1]}-filter" in filtered
    for guide in (text, bulk_script('path/with"quotes', 'json"'), filter_guide()):
        blocks = re.findall(r"```python\n(.*?)```", guide, re.DOTALL)
        assert blocks
        for block in blocks:
            ast.parse(block)


async def test_mcp_guidance_registration():
    async with Client(mcp) as client:
        assert len(await client.list_tools()) == 34
        prompts = await client.list_prompts()
        assert {p.name for p in prompts} == {
            "analyze_stock", "compare_funds", "screen_dividend_stocks",
            "bulk_data_script_guide", "decide_tool_or_script", "filter_large_dataset",
            "analyze_vs_fetch", "script_template_selector",
        }
        result = await client.get_prompt(
            "decide_tool_or_script", {"user_request": "Compare funds", "estimated_items": "21"}
        )
        assert "ASK USER PREFERENCE" in result.messages[0].content.text
        for uri in ("avanza://docs/usage", "avanza://docs/quick-start"):
            contents = await client.read_resource(uri)
            assert DECISION_GUIDE in contents[0].text
        templates = await client.list_resource_templates()
        assert {t.uriTemplate for t in templates} == {
            "avanza://stock/{instrument_id}", "avanza://fund/{instrument_id}"
        }
