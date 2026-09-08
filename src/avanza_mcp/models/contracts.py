"""Small typed tool envelopes. Pages retain source order and unmodified records."""

from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from .chart import ChartData
from .common import AvanzaModel, Limit, Offset
from .fund import ChartDataPoint, FundChart, FundChartPeriod
from .stock import BrokerTradeSummary, StockChart, Trade
from .instrument_data import NumberOfOwners, ShortSellingData


class PageMetadata(BaseModel):
    offset: Offset
    limit: Limit
    total: int | None = Field(
        description="Source count; null when the selected section is unavailable"
    )
    returned: int
    has_more: bool


class StockChartPage(BaseModel):
    data: StockChart
    pagination: PageMetadata


class FundChartPage(BaseModel):
    data: FundChart
    pagination: PageMetadata


class MarketmakerChartPage(BaseModel):
    data: ChartData
    pagination: PageMetadata
    marketMakerPagination: PageMetadata | None = None


class TradesPage(AvanzaModel):
    trades: list[Trade]
    pagination: PageMetadata


class OwnersPage(BaseModel):
    data: NumberOfOwners
    pagination: PageMetadata


class ShortSellingPage(BaseModel):
    data: ShortSellingData
    pagination: PageMetadata


class BrokerSummaries(AvanzaModel):
    summaries: list[BrokerTradeSummary]


class FundPeriods(AvanzaModel):
    periods: list[FundChartPeriod]


class FundHoldings(AvanzaModel):
    countryChartData: list[ChartDataPoint] | None
    sectorChartData: list[ChartDataPoint] | None
    holdingChartData: list[ChartDataPoint] | None
    portfolioDate: date | None


AnalysisSection = Literal[
    "stockKeyRatiosByYear",
    "stockKeyRatiosByQuarter",
    "stockKeyRatiosByQuarterQuarter",
    "stockKeyRatiosByQuarterTTM",
    "companyKeyRatiosByYear",
    "companyKeyRatiosByQuarter",
    "companyKeyRatiosByQuarterTTM",
    "companyKeyRatiosByQuarterQuarter",
]
FinancialSection = Literal[
    "companyFinancialsByYear",
    "companyFinancialsByQuarter",
    "companyFinancialsByQuarterTTM",
    "companyFinancialsByQuarterQuarter",
]

MetricName = Annotated[
    str, Field(min_length=1, max_length=100, pattern=r"^[A-Za-z][A-Za-z0-9]*$")
]


class AnalysisPoint(AvanzaModel):
    """Observed upstream point fields. Values retain their source-specific scale."""

    reportType: str
    financialYear: int
    value: float | None
    date: str | None = None


class AnalysisPage(BaseModel):
    """One named metric in one selected section, without sibling series or summaries."""

    selection: str
    metric: str
    available_metrics: list[str]
    data: dict[str, dict[str, list[AnalysisPoint] | None] | None]
    pagination: PageMetadata
