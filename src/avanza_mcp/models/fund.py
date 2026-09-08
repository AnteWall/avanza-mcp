"""Fund-related Pydantic models."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import Field, field_validator

from .common import MODEL_CONFIG as MODEL_CONFIG, AvanzaModel


class FundPerformance(AvanzaModel):
    """Fund performance metrics over various time periods."""

    today: Decimal | None = Field(None, description="Upstream performance today")
    one_week: Decimal | None = Field(
        None, alias="oneWeek", description="Upstream 1 week return"
    )
    one_month: Decimal | None = Field(
        None, alias="oneMonth", description="Upstream 1 month return"
    )
    three_months: Decimal | None = Field(
        None, alias="threeMonths", description="Upstream 3 month return"
    )
    this_year: Decimal | None = Field(
        None, alias="thisYear", description="Upstream year to date return"
    )
    one_year: Decimal | None = Field(
        None, alias="oneYear", description="Upstream 1 year return"
    )
    three_years: Decimal | None = Field(
        None, alias="threeYears", description="Upstream 3 year return"
    )
    five_years: Decimal | None = Field(
        None, alias="fiveYears", description="Upstream 5 year return"
    )
    ten_years: Decimal | None = Field(
        None, alias="tenYears", description="Upstream 10 year return"
    )


class FundFee(AvanzaModel):
    """Fund fee information."""

    ongoing_charges: Decimal | None = Field(
        None, alias="ongoingCharges", description="Upstream ongoing charges"
    )
    entry_charge: Decimal | None = Field(
        None, alias="entryCharge", description="Upstream entry fee"
    )
    exit_charge: Decimal | None = Field(
        None, alias="exitCharge", description="Upstream exit fee"
    )


class ChartDataPoint(AvanzaModel):
    """Data point for portfolio allocation charts."""

    name: str | None = None
    y: float | None = None


class FundAdminCompany(AvanzaModel):
    """Administration company as supplied by the fund guide."""

    name: str | None = None
    country: str | None = None
    url: str | None = None


class FundInfo(AvanzaModel):
    """Fund guide fields; fees and development retain source scales and basis."""

    # Basic info
    id: str | None = Field(None, description="Fund ID")
    name: str = Field(..., description="Fund name")
    isin: str | None = Field(None, description="ISIN identifier")
    description: str | None = Field(None, description="Fund description")

    # Price and NAV
    nav: Decimal | None = Field(None, description="Net Asset Value")
    nav_date: date | datetime | None = Field(
        None,
        alias="navDate",
        description="Source NAV date or timestamp; no timezone inferred",
    )
    currency: str | None = Field(
        default=None, description="Fund currency, when supplied"
    )

    # Performance
    developmentOneDay: Decimal | None = None
    developmentOneMonth: Decimal | None = None
    developmentThreeMonths: Decimal | None = None
    developmentSixMonths: Decimal | None = None
    developmentOneYear: Decimal | None = None
    developmentThisYear: Decimal | None = None
    developmentThreeYears: Decimal | None = None
    developmentFiveYears: Decimal | None = None
    development: FundPerformance | None = Field(
        None, description="Performance over time periods"
    )
    change_since_three_months: Decimal | None = Field(
        None, alias="changeSinceThreeMonths", description="Upstream 3 month change"
    )
    change_since_one_year: Decimal | None = Field(
        None, alias="changeSinceOneYear", description="Upstream 1 year change"
    )

    # Risk metrics
    risk: int | None = Field(None, description="Risk level (1-7)")
    risk_level: str | None = Field(None, alias="riskLevel", description="Risk category")
    riskText: str | None = None
    rating: int | None = Field(None, description="Rating (e.g., Morningstar)")
    standard_deviation: Decimal | None = Field(
        None, alias="standardDeviation", description="Standard deviation"
    )
    sharpe_ratio: Decimal | None = Field(
        None, alias="sharpeRatio", description="Sharpe ratio"
    )

    # Fees
    productFee: Decimal | None = Field(
        None, description="Raw upstream product fee; scale not inferred"
    )
    managementFee: Decimal | None = Field(
        None, description="Raw upstream management fee; scale not inferred"
    )
    fee: FundFee | None = Field(None, description="Fee information")

    # Fund characteristics
    adminCompany: FundAdminCompany | None = None
    categories: list[str] | None = None
    fund_company: str | None = Field(
        None, alias="fundCompany", description="Fund company"
    )
    fund_type_name: str | None = Field(
        None, alias="fundTypeName", description="Fund type"
    )
    category: str | None = Field(None, description="Fund category")
    aum: Decimal | None = Field(
        None, alias="capital", description="Assets under management"
    )
    start_date: date | None = Field(
        None, alias="startDate", description="Fund inception date"
    )

    # Trading
    tradeable: bool | None = Field(
        default=None, description="Whether fund is tradeable, when supplied"
    )
    buy_fee: Decimal | None = Field(
        None, alias="buyFee", description="Upstream buy fee"
    )
    sell_fee: Decimal | None = Field(
        None, alias="sellFee", description="Upstream sell fee"
    )
    prospectus: str | None = Field(None, description="Prospectus URL")
    prospectusLink: str | None = Field(
        None, description="Upstream prospectus link; may be a relative path"
    )

    # Portfolio allocations
    country_chart_data: list[ChartDataPoint] | None = Field(
        default=None,
        alias="countryChartData",
        description="Geographic allocation by country",
    )
    sector_chart_data: list[ChartDataPoint] | None = Field(
        default=None,
        alias="sectorChartData",
        description="Sector allocation",
    )
    holding_chart_data: list[ChartDataPoint] | None = Field(
        default=None,
        alias="holdingChartData",
        description="Top holdings",
    )
    portfolio_date: date | None = Field(
        None, alias="portfolioDate", description="Date of portfolio data"
    )

    # Timestamps
    last_updated: datetime | None = Field(
        None, alias="lastUpdated", description="Last update time"
    )

    @field_validator("nav_date", mode="before")
    @classmethod
    def preserve_nav_timestamp(cls, value: object) -> object:
        # A midnight timestamp must not be coerced into a date by the union.
        if isinstance(value, str) and "T" in value:
            return datetime.fromisoformat(value)
        return value


# === Models for additional fund endpoints ===


class ProductInvolvement(AvanzaModel):
    """Product involvement information for sustainability metrics."""

    product: str
    productDescription: str
    value: float
    name: str | None = None


class SustainabilityGoal(AvanzaModel):
    """UN Sustainable Development Goal information."""

    value: str
    name: str
    type: str
    status: str


class FundSustainability(AvanzaModel):
    """Fund sustainability and ESG metrics."""

    lowCarbon: bool | None = None
    esgScore: float | None = None
    environmentalScore: float | None = None
    socialScore: float | None = None
    governanceScore: float | None = None
    controversyScore: float | None = None
    carbonSolutionsInvolvement: float | None = None
    productInvolvements: list[ProductInvolvement] = []
    sustainabilityRating: int | None = None
    sustainabilityRatingCategoryName: str | None = None
    oilSandsExtractionInvolvement: float | None = None
    arcticOilAndGasExplorationInvolvement: float | None = None
    thermalCoalPowerGenerationInvolvement: float | None = None
    thermalCoalInvolvement: float | None = None
    oilAndGasProductionInvolvement: float | None = None
    environmentalRating: int | None = None
    socialRating: int | None = None
    governanceRating: int | None = None
    svanen: bool | None = None
    euArticleType: dict | str | None = (
        None  # Can be dict with 'value' and 'name' or string
    )
    aumCoveredCarbon: float | None = None
    fossilFuelInvolvement: float | None = None
    carbonRiskScore: float | None = None
    sustainabilityDevelopmentGoals: list[SustainabilityGoal] = []


class FundChartDataPoint(AvanzaModel):
    """Single data point in fund chart."""

    x: int  # timestamp
    y: float  # Upstream value; no unit conversion


class FundChart(AvanzaModel):
    """Fund chart data with historical performance."""

    id: str
    dataSerie: list[FundChartDataPoint]
    name: str | None = None
    fromDate: str | None = None
    toDate: str | None = None


class FundChartPeriod(AvanzaModel):
    """Fund performance for a specific time period."""

    timePeriod: str
    change: float
    startDate: date


class FundDescription(AvanzaModel):
    """Fund description and category information."""

    response: str
    heading: str
    detailedCategoryDescription: str
