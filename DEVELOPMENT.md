# Development Guide - Avanza MCP Server

This guide explains how to develop and test the Avanza MCP server locally, including integration with Claude Desktop.

## 🚀 Quick Start

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- [Claude Desktop](https://claude.ai/download) (optional, for MCP testing)

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/avanza-mcp.git
cd avanza-mcp

# Install dependencies
uv sync

# Verify installation
uv run python -c "from avanza_mcp import mcp; print('✓ Import successful')"
```

### Test with Claude Desktop

This is the **recommended way** to test the full MCP integration.

#### Step 1: Configure Claude Desktop for Local Development

Edit your Claude Desktop configuration file:

**Linux:** `~/.claude.json`

Add the local development configuration:

```json
{
  "mcpServers": {
    "avanza-dev": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/avanza-mcp",
        "run",
        "avanza-mcp"
      ]
    }
  }
}
```

**Replace `/absolute/path/to/avanza-mcp`** with your actual project path:

```bash
# Get the absolute path
pwd
# Example: /Users/username/projects/avanza-mcp
```

#### Step 2: Restart Claude Desktop

1. Quit Claude Desktop completely
2. Start Claude Desktop again
3. The MCP server will be loaded automatically

#### Step 3: Verify Connection

In Claude Desktop, ask:

```
Can you list the available MCP tools?
```

You should see all 15 Avanza tools listed.

#### Step 4: Test Tools

Try these queries in Claude Desktop:

```
# Search for stocks
Search for Volvo stock on Avanza

# Get stock quote
Get the current stock quote for Volvo B (ID: 5269)

# Get historical chart
Show me a 3-month price chart for Ericsson (ID: 5286)

# Get fund sustainability
What's the ESG score for Avanza Zero fund (ID: 41567)?

# Get order book
Show me the order book depth for H&M (ID: 5364)
```
