"""Market data service for retrieving stock and fund information."""

from typing import Any

from ..client.base import AvanzaClient
from ..client.endpoints import PublicEndpoint
from ..models.certificate import (
    CertificateDetails,
    CertificateFilterRequest,
    CertificateFilterResponse,
    CertificateInfo,
)
from ..models.chart import ChartData
from ..models.etf import (
    ETFDetails,
    ETFFilterRequest,
    ETFFilterResponse,
    ETFInfo,
)
from ..models.future_forward import (
    FutureForwardDetails,
    FutureForwardInfo,
    FutureForwardMatrixRequest,
    FutureForwardMatrixResponse,
)
from ..models.instrument_data import NumberOfOwners, ShortSellingData
from ..models.warrant import (
    WarrantDetails,
    WarrantFilterRequest,
    WarrantFilterResponse,
    WarrantInfo,
)
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

    async def get_dividends(self, instrument_id: str) -> dict[str, Any]:
        """Fetch dividend history from stock analysis data.

        Args:
            instrument_id: Avanza instrument ID

        Returns:
            Dividend data by year including:
            - dividend: Dividend amount per share
            - exDate: Ex-dividend date
            - paymentDate: Payment date
            - yield: Dividend yield percentage

        Raises:
            AvanzaError: If request fails
        """
        endpoint = PublicEndpoint.STOCK_ANALYSIS.format(id=instrument_id)
        analysis = await self._client.get(endpoint)
        return {
            "dividendsByYear": analysis.get("dividendsByYear", []),
        }

    async def get_company_financials(self, instrument_id: str) -> dict[str, Any]:
        """Fetch company financial data from stock analysis.

        Args:
            instrument_id: Avanza instrument ID

        Returns:
            Company financials by year and quarter including revenue,
            profit margins, earnings, and other financial metrics

        Raises:
            AvanzaError: If request fails
        """
        endpoint = PublicEndpoint.STOCK_ANALYSIS.format(id=instrument_id)
        analysis = await self._client.get(endpoint)
        return {
            "companyFinancialsByYear": analysis.get("companyFinancialsByYear", []),
            "companyFinancialsByQuarter": analysis.get("companyFinancialsByQuarter", []),
            "companyFinancialsByQuarterTTM": analysis.get(
                "companyFinancialsByQuarterTTM", []
            ),
        }

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

    # === Certificates ===

    async def filter_certificates(
        self, filter_request: CertificateFilterRequest
    ) -> CertificateFilterResponse:
        """Filter and list certificates with pagination.

        Args:
            filter_request: Filter criteria and pagination parameters

        Returns:
            Filtered list of certificates

        Raises:
            AvanzaError: If request fails
        """
        endpoint = PublicEndpoint.CERTIFICATE_FILTER.value
        raw_data = await self._client.post(
            endpoint, json=filter_request.model_dump(by_alias=True, exclude_none=True)
        )
        return CertificateFilterResponse.model_validate(raw_data)

    async def get_certificate_info(self, instrument_id: str) -> CertificateInfo:
        """Fetch detailed certificate information.

        Args:
            instrument_id: Avanza certificate ID

        Returns:
            Detailed certificate information

        Raises:
            AvanzaError: If request fails
        """
        endpoint = PublicEndpoint.CERTIFICATE_INFO.format(id=instrument_id)
        raw_data = await self._client.get(endpoint)
        return CertificateInfo.model_validate(raw_data)

    async def get_certificate_details(self, instrument_id: str) -> CertificateDetails:
        """Fetch extended certificate details.

        Args:
            instrument_id: Avanza certificate ID

        Returns:
            Extended certificate details

        Raises:
            AvanzaError: If request fails
        """
        endpoint = PublicEndpoint.CERTIFICATE_DETAILS.format(id=instrument_id)
        raw_data = await self._client.get(endpoint)
        return CertificateDetails.model_validate(raw_data)

    # === Warrants ===

    async def filter_warrants(
        self, filter_request: WarrantFilterRequest
    ) -> WarrantFilterResponse:
        """Filter and list warrants with pagination.

        Args:
            filter_request: Filter criteria and pagination parameters

        Returns:
            Filtered list of warrants

        Raises:
            AvanzaError: If request fails
        """
        endpoint = PublicEndpoint.WARRANT_FILTER.value
        raw_data = await self._client.post(
            endpoint, json=filter_request.model_dump(by_alias=True, exclude_none=True)
        )
        return WarrantFilterResponse.model_validate(raw_data)

    async def get_warrant_info(self, instrument_id: str) -> WarrantInfo:
        """Fetch detailed warrant information.

        Args:
            instrument_id: Avanza warrant ID

        Returns:
            Detailed warrant information

        Raises:
            AvanzaError: If request fails
        """
        endpoint = PublicEndpoint.WARRANT_INFO.format(id=instrument_id)
        raw_data = await self._client.get(endpoint)
        return WarrantInfo.model_validate(raw_data)

    async def get_warrant_details(self, instrument_id: str) -> WarrantDetails:
        """Fetch extended warrant details.

        Args:
            instrument_id: Avanza warrant ID

        Returns:
            Extended warrant details

        Raises:
            AvanzaError: If request fails
        """
        endpoint = PublicEndpoint.WARRANT_DETAILS.format(id=instrument_id)
        raw_data = await self._client.get(endpoint)
        return WarrantDetails.model_validate(raw_data)

    # === ETFs ===

    async def filter_etfs(self, filter_request: ETFFilterRequest) -> ETFFilterResponse:
        """Filter and list ETFs with pagination.

        Args:
            filter_request: Filter criteria and pagination parameters

        Returns:
            Filtered list of ETFs

        Raises:
            AvanzaError: If request fails
        """
        endpoint = PublicEndpoint.ETF_FILTER.value
        raw_data = await self._client.post(
            endpoint, json=filter_request.model_dump(by_alias=True, exclude_none=True)
        )
        return ETFFilterResponse.model_validate(raw_data)

    async def get_etf_info(self, instrument_id: str) -> ETFInfo:
        """Fetch detailed ETF information.

        Args:
            instrument_id: Avanza ETF ID

        Returns:
            Detailed ETF information

        Raises:
            AvanzaError: If request fails
        """
        endpoint = PublicEndpoint.ETF_INFO.format(id=instrument_id)
        raw_data = await self._client.get(endpoint)
        return ETFInfo.model_validate(raw_data)

    async def get_etf_details(self, instrument_id: str) -> ETFDetails:
        """Fetch extended ETF details.

        Args:
            instrument_id: Avanza ETF ID

        Returns:
            Extended ETF details

        Raises:
            AvanzaError: If request fails
        """
        endpoint = PublicEndpoint.ETF_DETAILS.format(id=instrument_id)
        raw_data = await self._client.get(endpoint)
        return ETFDetails.model_validate(raw_data)

    # === Futures/Forwards ===

    async def list_futures_forwards(
        self, request: FutureForwardMatrixRequest
    ) -> FutureForwardMatrixResponse:
        """List futures and forwards using matrix endpoint.

        Args:
            request: Matrix list request parameters

        Returns:
            Matrix response with futures/forwards

        Raises:
            AvanzaError: If request fails
        """
        endpoint = PublicEndpoint.FUTURE_FORWARD_MATRIX.value
        raw_data = await self._client.post(
            endpoint, json=request.model_dump(by_alias=True, exclude_none=True)
        )
        return FutureForwardMatrixResponse.model_validate(raw_data)

    async def get_future_forward_info(self, instrument_id: str) -> FutureForwardInfo:
        """Fetch detailed future/forward information.

        Args:
            instrument_id: Avanza future/forward ID

        Returns:
            Detailed future/forward information

        Raises:
            AvanzaError: If request fails
        """
        endpoint = PublicEndpoint.FUTURE_FORWARD_INFO.format(id=instrument_id)
        raw_data = await self._client.get(endpoint)
        return FutureForwardInfo.model_validate(raw_data)

    async def get_future_forward_details(
        self, instrument_id: str
    ) -> FutureForwardDetails:
        """Fetch extended future/forward details.

        Args:
            instrument_id: Avanza future/forward ID

        Returns:
            Extended future/forward details

        Raises:
            AvanzaError: If request fails
        """
        endpoint = PublicEndpoint.FUTURE_FORWARD_DETAILS.format(id=instrument_id)
        raw_data = await self._client.get(endpoint)
        return FutureForwardDetails.model_validate(raw_data)

    async def get_future_forward_filter_options(self) -> dict[str, Any]:
        """Get available filter options for futures/forwards.

        Returns:
            Available filter options including underlying instruments, dates, etc.

        Raises:
            AvanzaError: If request fails
        """
        endpoint = PublicEndpoint.FUTURE_FORWARD_FILTER_OPTIONS.value
        raw_data = await self._client.get(endpoint)
        return raw_data

    # === Additional Features ===

    async def get_number_of_owners(self, instrument_id: str) -> NumberOfOwners:
        """Get number of owners for an instrument.

        Args:
            instrument_id: Avanza instrument ID

        Returns:
            Number of owners data

        Raises:
            AvanzaError: If request fails
        """
        endpoint = PublicEndpoint.NUMBER_OF_OWNERS.format(id=instrument_id)
        raw_data = await self._client.get(endpoint)
        return NumberOfOwners.model_validate(raw_data)

    async def get_short_selling(self, instrument_id: str) -> ShortSellingData:
        """Get short selling data for an instrument.

        Args:
            instrument_id: Avanza instrument ID

        Returns:
            Short selling data

        Raises:
            AvanzaError: If request fails
        """
        endpoint = PublicEndpoint.SHORT_SELLING.format(id=instrument_id)
        raw_data = await self._client.get(endpoint)
        return ShortSellingData.model_validate(raw_data)

    async def get_marketmaker_chart(
        self, instrument_id: str, time_period: str = "today"
    ) -> ChartData:
        """Get price chart data for traded products (certificates, warrants, ETFs).

        This endpoint provides OHLC (Open-High-Low-Close) candlestick data
        with market maker information for traded products.

        Args:
            instrument_id: Avanza instrument ID
            time_period: Time period for chart data (default: "today")
                Available periods: today, one_week, one_month, three_months,
                six_months, one_year, three_years, five_years, etc.

        Returns:
            Chart data with OHLC candlesticks and metadata

        Raises:
            AvanzaError: If request fails
        """
        endpoint = PublicEndpoint.MARKETMAKER_CHART.format(id=instrument_id)
        raw_data = await self._client.get(endpoint, params={"timePeriod": time_period})
        return ChartData.model_validate(raw_data)

