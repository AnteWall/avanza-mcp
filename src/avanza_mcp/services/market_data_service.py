"""Market data service for retrieving stock and fund information."""

from typing import Any

from pydantic import TypeAdapter, validate_call

from ..client.base import AvanzaClient
from ..client.endpoints import PublicEndpoint
from ..models.certificate import (
    CertificateDetails,
    CertificateFilterRequest,
    CertificateFilterResponse,
    CertificateInfo,
)
from ..models.chart import ChartData
from ..models.common import FundPeriod, MarketmakerPeriod, StockPeriod
from ..models.contracts import AnalysisPoint, FinancialSection
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
    """Service for retrieving market data.

    All instrument IDs are Avanza IDs. HTTP errors propagate to callers,
    and responses returned as models undergo model validation.
    """

    def __init__(self, client: AvanzaClient) -> None:
        """Initialize the service with an Avanza HTTP client."""
        self._client = client

    async def get_stock_info(self, instrument_id: str) -> StockInfo:
        """Fetch detailed stock information."""
        endpoint = PublicEndpoint.STOCK_INFO.format(id=instrument_id)
        raw_data = await self._client.get(endpoint)
        return StockInfo.model_validate(raw_data)

    async def get_fund_info(self, instrument_id: str) -> FundInfo:
        """Fetch detailed fund information."""
        endpoint = PublicEndpoint.FUND_INFO.format(id=instrument_id)
        raw_data = await self._client.get(endpoint)
        return FundInfo.model_validate(raw_data)

    async def get_order_depth(self, instrument_id: str) -> OrderDepth:
        """Fetch latest available order book depth with buy and sell levels."""
        endpoint = PublicEndpoint.STOCK_ORDERDEPTH.format(id=instrument_id)
        raw_data = await self._client.get(endpoint)
        return OrderDepth.model_validate(raw_data)

    @validate_call
    async def get_chart_data(
        self,
        instrument_id: str,
        time_period: StockPeriod = "one_year",
    ) -> StockChart:
        """Fetch historical chart data with OHLC values.

        Periods include one_week, one_month, three_months, one_year, etc.
        """
        endpoint = PublicEndpoint.STOCK_CHART.format(id=instrument_id)
        params = {"timePeriod": time_period}
        raw_data = await self._client.get(endpoint, params=params)
        return StockChart.model_validate(raw_data)

    async def get_marketplace_info(self, instrument_id: str) -> MarketplaceInfo:
        """Fetch marketplace status and trading hours."""
        endpoint = PublicEndpoint.STOCK_MARKETPLACE.format(id=instrument_id)
        raw_data = await self._client.get(endpoint)
        return MarketplaceInfo.model_validate(raw_data)

    async def get_trades(self, instrument_id: str) -> list[Trade]:
        """Fetch recent trades for an instrument."""
        endpoint = PublicEndpoint.STOCK_TRADES.format(id=instrument_id)
        raw_data = await self._client.get(endpoint)
        return TypeAdapter(list[Trade]).validate_python(raw_data)

    async def get_broker_trades(self, instrument_id: str) -> list[BrokerTradeSummary]:
        """Fetch broker trade summaries with buy/sell volumes."""
        endpoint = PublicEndpoint.STOCK_BROKER_TRADES.format(id=instrument_id)
        raw_data = await self._client.get(endpoint)
        return TypeAdapter(list[BrokerTradeSummary]).validate_python(raw_data)

    async def get_stock_analysis(
        self,
        instrument_id: str,
        selection: str | None = None,
    ) -> dict[str, Any]:
        """Validate the root object and only the requested section's metric series."""
        endpoint = PublicEndpoint.STOCK_ANALYSIS.format(id=instrument_id)
        analysis = TypeAdapter(dict[str, Any]).validate_python(
            await self._client.get(endpoint)
        )
        if selection is not None and selection in analysis:
            TypeAdapter(dict[str, list[AnalysisPoint] | None] | None).validate_python(
                analysis[selection]
            )
        return analysis

    async def get_dividends(self, instrument_id: str) -> dict[str, Any]:
        """Select the upstream dividend section; preserve absent versus empty data."""
        analysis = await self.get_stock_analysis(instrument_id, "dividendsByYear")
        return {key: analysis[key] for key in ("dividendsByYear",) if key in analysis}

    @validate_call
    async def get_company_financials(
        self,
        instrument_id: str,
        selection: FinancialSection = "companyFinancialsByYear",
    ) -> dict[str, Any]:
        """Fetch company financial data from stock analysis.

        Return yearly, quarterly, and quarterly TTM financials, including
        revenue, profit margins, earnings, and other financial metrics.
        """
        analysis = await self.get_stock_analysis(instrument_id, selection)
        return {selection: analysis[selection]} if selection in analysis else {}

    async def get_stock_quote(self, instrument_id: str) -> Quote:
        """Fetch latest available quote; reject envelopes without any quote fields."""
        endpoint = PublicEndpoint.STOCK_QUOTE.format(id=instrument_id)
        raw_data = await self._client.get(endpoint)
        if (
            not isinstance(raw_data, dict)
            or not Quote.model_fields.keys() & raw_data.keys()
        ):
            raise ValueError(
                "Expected a quote object containing recognized quote fields"
            )
        return Quote.model_validate(raw_data)

    async def get_fund_sustainability(self, instrument_id: str) -> FundSustainability:
        """Fetch fund sustainability, ESG scores, and environmental data."""
        endpoint = PublicEndpoint.FUND_SUSTAINABILITY.format(id=instrument_id)
        raw_data = await self._client.get(endpoint)
        return FundSustainability.model_validate(raw_data)

    @validate_call
    async def get_fund_chart(
        self, instrument_id: str, time_period: FundPeriod = "three_years"
    ) -> FundChart:
        """Fetch fund chart data for a specific time period.

        Periods include three_years, five_years, etc.; returns historical performance.
        """
        endpoint = PublicEndpoint.FUND_CHART.format(
            id=instrument_id, time_period=time_period
        )
        raw_data = await self._client.get(endpoint)
        return FundChart.model_validate(raw_data)

    async def get_fund_chart_periods(self, instrument_id: str) -> list[FundChartPeriod]:
        """Fetch available fund chart periods with performance changes."""
        endpoint = PublicEndpoint.FUND_CHART_PERIODS.format(id=instrument_id)
        raw_data = await self._client.get(endpoint)
        return TypeAdapter(list[FundChartPeriod]).validate_python(raw_data)

    async def get_fund_description(self, instrument_id: str) -> FundDescription:
        """Fetch fund description and detailed category information."""
        endpoint = PublicEndpoint.FUND_DESCRIPTION.format(id=instrument_id)
        raw_data = await self._client.get(endpoint)
        return FundDescription.model_validate(raw_data)

    # === Certificates ===

    async def filter_certificates(
        self, filter_request: CertificateFilterRequest
    ) -> CertificateFilterResponse:
        """Filter and list certificates with pagination."""
        endpoint = PublicEndpoint.CERTIFICATE_FILTER.value
        raw_data = await self._client.post(
            endpoint,
            json=filter_request.model_dump(
                mode="json", by_alias=True, exclude_none=True
            ),
        )
        return CertificateFilterResponse.model_validate(raw_data)

    async def get_certificate_info(self, instrument_id: str) -> CertificateInfo:
        """Fetch detailed certificate information."""
        endpoint = PublicEndpoint.CERTIFICATE_INFO.format(id=instrument_id)
        raw_data = await self._client.get(endpoint)
        return CertificateInfo.model_validate(raw_data)

    async def get_certificate_details(self, instrument_id: str) -> CertificateDetails:
        """Fetch extended certificate details."""
        endpoint = PublicEndpoint.CERTIFICATE_DETAILS.format(id=instrument_id)
        raw_data = await self._client.get(endpoint)
        return CertificateDetails.model_validate(raw_data)

    # === Warrants ===

    async def filter_warrants(
        self, filter_request: WarrantFilterRequest
    ) -> WarrantFilterResponse:
        """Filter and list warrants with pagination."""
        endpoint = PublicEndpoint.WARRANT_FILTER.value
        raw_data = await self._client.post(
            endpoint,
            json=filter_request.model_dump(
                mode="json", by_alias=True, exclude_none=True
            ),
        )
        return WarrantFilterResponse.model_validate(raw_data)

    async def get_warrant_info(self, instrument_id: str) -> WarrantInfo:
        """Fetch detailed warrant information."""
        endpoint = PublicEndpoint.WARRANT_INFO.format(id=instrument_id)
        raw_data = await self._client.get(endpoint)
        return WarrantInfo.model_validate(raw_data)

    async def get_warrant_details(self, instrument_id: str) -> WarrantDetails:
        """Fetch extended warrant details."""
        endpoint = PublicEndpoint.WARRANT_DETAILS.format(id=instrument_id)
        raw_data = await self._client.get(endpoint)
        return WarrantDetails.model_validate(raw_data)

    # === ETFs ===

    async def filter_etfs(self, filter_request: ETFFilterRequest) -> ETFFilterResponse:
        """Filter and list ETFs with pagination."""
        endpoint = PublicEndpoint.ETF_FILTER.value
        raw_data = await self._client.post(
            endpoint,
            json=filter_request.model_dump(
                mode="json", by_alias=True, exclude_none=True
            ),
        )
        return ETFFilterResponse.model_validate(raw_data)

    async def get_etf_info(self, instrument_id: str) -> ETFInfo:
        """Fetch detailed ETF information."""
        endpoint = PublicEndpoint.ETF_INFO.format(id=instrument_id)
        raw_data = await self._client.get(endpoint)
        return ETFInfo.model_validate(raw_data)

    async def get_etf_details(self, instrument_id: str) -> ETFDetails:
        """Fetch extended ETF details."""
        endpoint = PublicEndpoint.ETF_DETAILS.format(id=instrument_id)
        raw_data = await self._client.get(endpoint)
        return ETFDetails.model_validate(raw_data)

    # === Futures/Forwards ===

    async def list_futures_forwards(
        self, request: FutureForwardMatrixRequest
    ) -> FutureForwardMatrixResponse:
        """List futures and forwards using the matrix endpoint."""
        endpoint = PublicEndpoint.FUTURE_FORWARD_MATRIX.value
        raw_data = await self._client.post(
            endpoint,
            json=request.model_dump(mode="json", by_alias=True, exclude_none=True),
        )
        return FutureForwardMatrixResponse.model_validate(raw_data)

    async def get_future_forward_info(self, instrument_id: str) -> FutureForwardInfo:
        """Fetch detailed future/forward information."""
        endpoint = PublicEndpoint.FUTURE_FORWARD_INFO.format(id=instrument_id)
        raw_data = await self._client.get(endpoint)
        return FutureForwardInfo.model_validate(raw_data)

    async def get_future_forward_details(
        self, instrument_id: str
    ) -> FutureForwardDetails:
        """Fetch extended future/forward details."""
        endpoint = PublicEndpoint.FUTURE_FORWARD_DETAILS.format(id=instrument_id)
        raw_data = await self._client.get(endpoint)
        return FutureForwardDetails.model_validate(raw_data)

    async def get_future_forward_filter_options(self) -> dict[str, Any]:
        """Get futures/forwards filter options, including underlying instruments and dates."""
        endpoint = PublicEndpoint.FUTURE_FORWARD_FILTER_OPTIONS.value
        raw_data = await self._client.get(endpoint)
        return TypeAdapter(dict[str, Any]).validate_python(raw_data)

    # === Additional Features ===

    async def get_number_of_owners(self, instrument_id: str) -> NumberOfOwners:
        """Get number of owners for an instrument."""
        endpoint = PublicEndpoint.NUMBER_OF_OWNERS.format(id=instrument_id)
        raw_data = await self._client.get(endpoint)
        return NumberOfOwners.model_validate(raw_data)

    async def get_short_selling(self, instrument_id: str) -> ShortSellingData:
        """Get short selling data for an instrument."""
        endpoint = PublicEndpoint.SHORT_SELLING.format(id=instrument_id)
        raw_data = await self._client.get(endpoint)
        return ShortSellingData.model_validate(raw_data)

    @validate_call
    async def get_marketmaker_chart(
        self, instrument_id: str, time_period: MarketmakerPeriod = "today"
    ) -> ChartData:
        """Get price chart data for traded products (certificates, warrants, ETFs).

        Return OHLC (Open-High-Low-Close) candlesticks with market maker
        information and metadata. Periods include today (default), one_week,
        one_month, three_months, six_months, one_year, three_years, five_years, etc.
        """
        endpoint = PublicEndpoint.MARKETMAKER_CHART.format(id=instrument_id)
        raw_data = await self._client.get(endpoint, params={"timePeriod": time_period})
        return ChartData.model_validate(raw_data)
