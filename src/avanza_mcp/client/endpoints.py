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

    # Market data - Charts (for traded products: certificates, warrants, ETFs)
    MARKETMAKER_CHART = "/_api/price-chart/marketmaker/{id}"  # Requires timePeriod param

    # Market data - Funds
    FUND_INFO = "/_api/fund-guide/guide/{id}"
    FUND_SUSTAINABILITY = "/_api/fund-reference/sustainability/{id}"
    FUND_CHART = "/_api/fund-guide/chart/{id}/{time_period}"  # time_period: three_years, etc.
    FUND_CHART_PERIODS = "/_api/fund-guide/chart/timeperiods/{id}"
    FUND_DESCRIPTION = "/_api/fund-guide/description/{id}"

    # Market data - Certificates
    CERTIFICATE_FILTER = "/_api/market-certificate-filter/"
    CERTIFICATE_INFO = "/_api/market-guide/certificate/{id}"
    CERTIFICATE_DETAILS = "/_api/market-guide/certificate/{id}/details"

    # Market data - Warrants
    WARRANT_FILTER = "/_api/market-warrant-filter/"
    WARRANT_INFO = "/_api/market-guide/warrant/{id}"
    WARRANT_DETAILS = "/_api/market-guide/warrant/{id}/details"

    # Market data - ETFs
    ETF_FILTER = "/_api/market-etf-filter/"
    ETF_INFO = "/_api/market-etf/{id}"
    ETF_DETAILS = "/_api/market-etf/{id}/details"

    # Market data - Futures/Forwards
    FUTURE_FORWARD_MATRIX = "/_api/market-option-future-forward-list/matrix"
    FUTURE_FORWARD_FILTER_OPTIONS = "/_api/market-option-future-forward-list/filter-options"
    FUTURE_FORWARD_INFO = "/_api/market-guide/futureforward/{id}"
    FUTURE_FORWARD_DETAILS = "/_api/market-guide/futureforward/{id}/details"

    # Additional features
    NUMBER_OF_OWNERS = "/_api/market-guide/number-of-owners/{id}"
    SHORT_SELLING = "/_api/market-guide/short-selling/{id}"

    def format(self, **kwargs: str | int) -> str:
        """Format endpoint path with variables.

        Args:
            **kwargs: Variables to format into the endpoint path

        Returns:
            Formatted endpoint path
        """
        return self.value.format(**kwargs)
