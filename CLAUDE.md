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

This is an MCP (Model Context Protocol) server for Avanza built with FastMCP 3.0.0b1 and Python 3.12.

## Commands

```bash
# Install dependencies (uses uv)
uv sync

# Run the MCP server locally
uv run avanza-mcp

# Run the test client (imports the server directly, no separate server needed)
uv run python examples/test_client.py
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

- **src/avanza_mcp/__init__.py** - MCP server entry point using FastMCP. Tools are defined as decorated functions with `@mcp.tool`. Exports `mcp` instance and `main()` entry point.
- **examples/** - Example client code demonstrating in-process testing with FastMCP's Client.

## FastMCP Patterns

Tools are registered using the `@mcp.tool` decorator:
```python
@mcp.tool
def tool_name(param: str) -> str:
    return result
```

For in-process testing, pass the FastMCP instance directly to Client:
```python
from fastmcp import Client
from avanza_mcp import mcp

async with Client(mcp) as client:
    result = await client.call_tool("tool_name", {"param": "value"})
```
