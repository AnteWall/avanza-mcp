"""Shared integration fixtures."""

import pytest

from avanza_mcp.client import AvanzaClient
from avanza_mcp.services import MarketDataService


@pytest.fixture(scope="function")
async def service():
    """Keep one client open for each test, including multi-request flows."""
    async with AvanzaClient() as client:
        yield MarketDataService(client)
