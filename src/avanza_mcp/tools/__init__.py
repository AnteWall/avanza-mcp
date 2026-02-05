"""MCP tools for Avanza API."""

# Import to register tools via decorators
from . import certificates  # noqa: F401
from . import etfs  # noqa: F401
from . import funds  # noqa: F401
from . import futures_forwards  # noqa: F401
from . import instrument_data  # noqa: F401
from . import market_data  # noqa: F401
from . import search  # noqa: F401
from . import warrants  # noqa: F401

__all__ = [
    "certificates",
    "etfs",
    "funds",
    "futures_forwards",
    "instrument_data",
    "market_data",
    "search",
    "warrants",
]
