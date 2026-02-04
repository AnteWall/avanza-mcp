"""MCP tools for Avanza API."""

# Import to register tools via decorators
from . import funds  # noqa: F401
from . import market_data  # noqa: F401
from . import search  # noqa: F401

__all__ = ["search", "market_data", "funds"]
