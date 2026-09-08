"""Shared error logging for tool operations."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastmcp import Context


@asynccontextmanager
async def log_errors(ctx: Context, prefix: str) -> AsyncIterator[None]:
    """Log operation failures without suppressing them."""
    try:
        yield
    except Exception as e:
        await ctx.error(f"{prefix}: {str(e)}")
        raise
