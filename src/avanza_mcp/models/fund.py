"""Fund-related Pydantic models."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class FundPerformance(BaseModel):
    """Fund performance metrics over various time periods."""

    model_config = ConfigDict(populate_by_name=True)

    today: Decimal | None = Field(None, description="Performance today (%)")
    one_week: Decimal | None = Field(None, alias="oneWeek", description="1 week return (%)")
    one_month: Decimal | None = Field(
        None, alias="oneMonth", description="1 month return (%)"
    )
    three_months: Decimal | None = Field(
        None, alias="threeMonths", description="3 month return (%)"
    )
    this_year: Decimal | None = Field(
        None, alias="thisYear", description="Year to date return (%)"
    )
    one_year: Decimal | None = Field(None, alias="oneYear", description="1 year return (%)")
    three_years: Decimal | None = Field(
        None, alias="threeYears", description="3 year return (%)"
    )
    five_years: Decimal | None = Field(
        None, alias="fiveYears", description="5 year return (%)"
    )
    ten_years: Decimal | None = Field(
        None, alias="tenYears", description="10 year return (%)"
    )


class FundFee(BaseModel):
    """Fund fee information."""

    model_config = ConfigDict(populate_by_name=True)

    ongoing_charges: Decimal | None = Field(
        None, alias="ongoingCharges", description="Ongoing charges (%)"
    )
    entry_charge: Decimal | None = Field(
        None, alias="entryCharge", description="Entry fee (%)"
    )
    exit_charge: Decimal | None = Field(None, alias="exitCharge", description="Exit fee (%)")


class FundInfo(BaseModel):
    """Detailed fund information."""

    model_config = ConfigDict(populate_by_name=True)

    # Basic info
    id: str | None = Field(None, description="Fund ID")
    name: str = Field(..., description="Fund name")
    isin: str | None = Field(None, description="ISIN identifier")
    description: str | None = Field(None, description="Fund description")

    # Price and NAV
    nav: Decimal | None = Field(None, description="Net Asset Value")
    nav_date: date | None = Field(None, alias="navDate", description="NAV date")
    currency: str = Field(default="SEK", description="Fund currency")

    # Performance
    development: FundPerformance | None = Field(
        None, description="Performance over time periods"
    )
    change_since_three_months: Decimal | None = Field(
        None, alias="changeSinceThreeMonths", description="3 month change (%)"
    )
    change_since_one_year: Decimal | None = Field(
        None, alias="changeSinceOneYear", description="1 year change (%)"
    )

    # Risk metrics
    risk: int | None = Field(None, description="Risk level (1-7)")
    risk_level: str | None = Field(None, alias="riskLevel", description="Risk category")
    rating: int | None = Field(None, description="Rating (e.g., Morningstar)")
    standard_deviation: Decimal | None = Field(
        None, alias="standardDeviation", description="Standard deviation"
    )
    sharpe_ratio: Decimal | None = Field(
        None, alias="sharpeRatio", description="Sharpe ratio"
    )

    # Fees
    fee: FundFee | None = Field(None, description="Fee information")

    # Fund characteristics
    fund_company: str | None = Field(None, alias="fundCompany", description="Fund company")
    fund_type_name: str | None = Field(
        None, alias="fundTypeName", description="Fund type"
    )
    category: str | None = Field(None, description="Fund category")
    aum: Decimal | None = Field(
        None, alias="capital", description="Assets under management"
    )
    start_date: date | None = Field(None, alias="startDate", description="Fund inception date")

    # Trading
    tradeable: bool = Field(default=True, description="Whether fund is tradeable")
    buy_fee: Decimal | None = Field(None, alias="buyFee", description="Buy fee (%)")
    sell_fee: Decimal | None = Field(None, alias="sellFee", description="Sell fee (%)")
    prospectus: str | None = Field(None, description="Prospectus URL")

    # Timestamps
    last_updated: datetime | None = Field(
        None, alias="lastUpdated", description="Last update time"
    )


# === New models for additional fund endpoints ===


class ProductInvolvement(BaseModel):
    """Product involvement information for sustainability metrics."""

    product: str
    productDescription: str
    value: float
    name: str


class SustainabilityGoal(BaseModel):
    """UN Sustainable Development Goal information."""

    goalId: int | None = None
    goalName: str | None = None
    goalDescription: str | None = None


class FundSustainability(BaseModel):
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
    euArticleType: dict | str | None = None  # Can be dict with 'value' and 'name' or string
    aumCoveredCarbon: float | None = None
    fossilFuelInvolvement: float | None = None
    carbonRiskScore: float | None = None
    sustainabilityDevelopmentGoals: list[SustainabilityGoal] = []


class FundChartDataPoint(BaseModel):
    """Single data point in fund chart."""

    x: int  # timestamp
    y: float  # value (typically percentage)


class FundChart(BaseModel):
    """Fund chart data with historical performance."""

    id: str
    dataSerie: list[FundChartDataPoint]
    name: str | None = None
    fromDate: str | None = None
    toDate: str | None = None


class FundChartPeriod(BaseModel):
    """Fund performance for a specific time period."""

    timePeriod: str
    change: float
    startDate: str


class FundDescription(BaseModel):
    """Fund description and category information."""

    response: str
    heading: str
    detailedCategoryDescription: str
