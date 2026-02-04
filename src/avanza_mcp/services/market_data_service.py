"""Market data service for retrieving stock and fund information."""

from typing import Any

from ..client.base import AvanzaClient
from ..client.endpoints import PublicEndpoint
from ..models.fund import (
    FundChart,
    FundChartPeriod,
    FundDescription,
    FundInfo,
    FundSustainability,
)
from ..models.stock import (
    BrokerTradeSummary,
    MarketplaceInfo,
    OrderDepth,
    Quote,
    StockChart,
    StockInfo,
    Trade,
)


class MarketDataService:
    """Service for retrieving market data."""

    def __init__(self, client: AvanzaClient) -> None:
        """Initialize market data service.

        Args:
            client: Avanza HTTP client
        """
        self._client = client

    async def get_stock_info(self, instrument_id: str) -> StockInfo:
        """Fetch detailed stock information.

        Args:
            instrument_id: Avanza instrument ID

        Returns:
            Detailed stock information

        Raises:
            AvanzaError: If request fails
        """
        endpoint = PublicEndpoint.STOCK_INFO.format(id=instrument_id)
        raw_data = await self._client.get(endpoint)
        return StockInfo.model_validate(raw_data)

    async def get_fund_info(self, instrument_id: str) -> FundInfo:
        """Fetch detailed fund information.

        Args:
            instrument_id: Avanza fund ID

        Returns:
            Detailed fund information

        Raises:
            AvanzaError: If request fails
        """
        endpoint = PublicEndpoint.FUND_INFO.format(id=instrument_id)
        raw_data = await self._client.get(endpoint)
        return FundInfo.model_validate(raw_data)

    async def get_order_depth(self, instrument_id: str) -> OrderDepth:
        """Fetch real-time order book depth data.

        Args:
            instrument_id: Avanza instrument ID

        Returns:
            Order book depth with buy and sell levels

        Raises:
            AvanzaError: If request fails
        """
        endpoint = PublicEndpoint.STOCK_ORDERDEPTH.format(id=instrument_id)
        raw_data = await self._client.get(endpoint)
        return OrderDepth.model_validate(raw_data)

    async def get_chart_data(
        self,
        instrument_id: str,
        time_period: str = "one_year",
    ) -> StockChart:
        """Fetch historical chart data with OHLC values.

        Args:
            instrument_id: Avanza instrument ID
            time_period: Time period - one_week, one_month, three_months, one_year, etc.

        Returns:
            Chart data with OHLC values

        Raises:
            AvanzaError: If request fails
        """
        endpoint = PublicEndpoint.STOCK_CHART.format(id=instrument_id)
        params = {"timePeriod": time_period}
        raw_data = await self._client.get(endpoint, params=params)
        return StockChart.model_validate(raw_data)

    async def get_marketplace_info(self, instrument_id: str) -> MarketplaceInfo:
        """Fetch marketplace status and trading hours.

        Args:
            instrument_id: Avanza instrument ID

        Returns:
            Marketplace information including open/close times

        Raises:
            AvanzaError: If request fails
        """
        endpoint = PublicEndpoint.STOCK_MARKETPLACE.format(id=instrument_id)
        raw_data = await self._client.get(endpoint)
        return MarketplaceInfo.model_validate(raw_data)

    async def get_trades(self, instrument_id: str) -> list[Trade]:
        """Fetch recent trades for an instrument.

        Args:
            instrument_id: Avanza instrument ID

        Returns:
            List of recent trades

        Raises:
            AvanzaError: If request fails
        """
        endpoint = PublicEndpoint.STOCK_TRADES.format(id=instrument_id)
        raw_data = await self._client.get(endpoint)
        return [Trade.model_validate(trade) for trade in raw_data]

    async def get_broker_trades(self, instrument_id: str) -> list[BrokerTradeSummary]:
        """Fetch broker trade summaries.

        Args:
            instrument_id: Avanza instrument ID

        Returns:
            List of broker trade summaries with buy/sell volumes

        Raises:
            AvanzaError: If request fails
        """
        endpoint = PublicEndpoint.STOCK_BROKER_TRADES.format(id=instrument_id)
        raw_data = await self._client.get(endpoint)
        return [BrokerTradeSummary.model_validate(trade) for trade in raw_data]

    async def get_stock_analysis(self, instrument_id: str) -> dict[str, Any]:
        """Fetch stock analysis with key ratios by year and quarter.

        Args:
            instrument_id: Avanza instrument ID

        Returns:
            Stock analysis data with key ratios grouped by time periods

        Raises:
            AvanzaError: If request fails
        """
        endpoint = PublicEndpoint.STOCK_ANALYSIS.format(id=instrument_id)
        return await self._client.get(endpoint)

    async def get_stock_quote(self, instrument_id: str) -> Quote:
        """Fetch real-time stock quote with current pricing.

        Args:
            instrument_id: Avanza instrument ID

        Returns:
            Real-time quote with buy, sell, last price, and trading volumes

        Raises:
            AvanzaError: If request fails
        """
        endpoint = PublicEndpoint.STOCK_QUOTE.format(id=instrument_id)
        raw_data = await self._client.get(endpoint)
        return Quote.model_validate(raw_data)

    async def get_fund_sustainability(self, instrument_id: str) -> FundSustainability:
        """Fetch fund sustainability and ESG metrics.

        Args:
            instrument_id: Avanza fund ID

        Returns:
            Sustainability metrics including ESG scores and environmental data

        Raises:
            AvanzaError: If request fails
        """
        endpoint = PublicEndpoint.FUND_SUSTAINABILITY.format(id=instrument_id)
        raw_data = await self._client.get(endpoint)
        return FundSustainability.model_validate(raw_data)

    async def get_fund_chart(
        self, instrument_id: str, time_period: str = "three_years"
    ) -> FundChart:
        """Fetch fund chart data for a specific time period.

        Args:
            instrument_id: Avanza fund ID
            time_period: Time period (e.g., three_years, five_years, etc.)

        Returns:
            Fund chart with historical performance data

        Raises:
            AvanzaError: If request fails
        """
        endpoint = PublicEndpoint.FUND_CHART.format(
            id=instrument_id, time_period=time_period
        )
        raw_data = await self._client.get(endpoint)
        return FundChart.model_validate(raw_data)

    async def get_fund_chart_periods(self, instrument_id: str) -> list[FundChartPeriod]:
        """Fetch available fund chart periods with performance data.

        Args:
            instrument_id: Avanza fund ID

        Returns:
            List of time periods with performance changes

        Raises:
            AvanzaError: If request fails
        """
        endpoint = PublicEndpoint.FUND_CHART_PERIODS.format(id=instrument_id)
        raw_data = await self._client.get(endpoint)
        return [FundChartPeriod.model_validate(period) for period in raw_data]

    async def get_fund_description(self, instrument_id: str) -> FundDescription:
        """Fetch fund description and category information.

        Args:
            instrument_id: Avanza fund ID

        Returns:
            Fund description with detailed category information

        Raises:
            AvanzaError: If request fails
        """
        endpoint = PublicEndpoint.FUND_DESCRIPTION.format(id=instrument_id)
        raw_data = await self._client.get(endpoint)
        return FundDescription.model_validate(raw_data)

