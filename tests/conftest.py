"""Pytest configuration and fixtures."""

import pytest


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (may hit real APIs)"
    )


@pytest.fixture(scope="session")
def event_loop_policy():
    """Use default event loop policy."""
    import asyncio
    return asyncio.DefaultEventLoopPolicy()
