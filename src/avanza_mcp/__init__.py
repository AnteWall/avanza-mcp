"""Avanza MCP Server - Public API Access via FastMCP.

This server provides read-only access to Avanza's public market data API.
No authentication required - all endpoints are publicly accessible.

Provides access to:
- Stock information, quotes, and charts
- Fund information, sustainability metrics, and performance
- Certificates, Warrants, ETFs, Futures/Forwards data
- Market data including order depth, trades, and broker activity
- Additional data (number of owners, short selling info)
- Real-time market status and trading hours
"""

__version__ = "1.3.0"

from fastmcp import FastMCP

# Create FastMCP instance
mcp = FastMCP("Avanza MCP Server")

# Import modules to register tools/resources/prompts via decorators
# The @mcp.tool/@mcp.resource/@mcp.prompt decorators handle registration
from . import prompts  # noqa: F401, E402
from . import resources  # noqa: F401, E402
from . import tools  # noqa: F401, E402


def main() -> None:
    """Entry point for the MCP server."""
    mcp.run()
