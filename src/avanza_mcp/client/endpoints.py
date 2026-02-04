"""Avanza API endpoint definitions.

All endpoints are public and require no authentication.
"""

from enum import Enum


class PublicEndpoint(Enum):
    """Public Avanza API endpoints - no authentication required."""

    # Search
    SEARCH = "/_api/search/filtered-search"

    # Market data - Stocks
    STOCK_INFO = "/_api/market-guide/stock/{id}"
    STOCK_ANALYSIS = "/_api/market-guide/stock/{id}/analysis"
    STOCK_QUOTE = "/_api/market-guide/stock/{id}/quote"
    STOCK_MARKETPLACE = "/_api/market-guide/stock/{id}/marketplace"
    STOCK_ORDERDEPTH = "/_api/market-guide/stock/{id}/orderdepth"
    STOCK_TRADES = "/_api/market-guide/stock/{id}/trades"
    STOCK_BROKER_TRADES = "/_api/market-guide/stock/{id}/broker-trade-summaries"
    STOCK_CHART = "/_api/price-chart/stock/{id}"  # Requires timePeriod param

    # Market data - Funds
    FUND_INFO = "/_api/fund-guide/guide/{id}"
    FUND_SUSTAINABILITY = "/_api/fund-reference/sustainability/{id}"
    FUND_CHART = "/_api/fund-guide/chart/{id}/{time_period}"  # time_period: three_years, etc.
    FUND_CHART_PERIODS = "/_api/fund-guide/chart/timeperiods/{id}"
    FUND_DESCRIPTION = "/_api/fund-guide/description/{id}"

    def format(self, **kwargs: str | int) -> str:
        """Format endpoint path with variables.

        Args:
            **kwargs: Variables to format into the endpoint path

        Returns:
            Formatted endpoint path
        """
        return self.value.format(**kwargs)
