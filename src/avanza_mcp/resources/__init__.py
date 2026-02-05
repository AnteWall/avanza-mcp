"""MCP resources for Avanza API."""

# Import to register resources via decorators
from . import instruments  # noqa: F401
from . import usage  # noqa: F401

__all__ = ["instruments", "usage"]
