"""Stock-related Pydantic models matching Avanza API."""

from pydantic import BaseModel, ConfigDict, Field


# Standard model config for all models
MODEL_CONFIG = ConfigDict(
    populate_by_name=True,
    str_strip_whitespace=True,
    validate_assignment=True,
    extra="allow",  # Don't fail on extra fields from API
)


class Quote(BaseModel):
    """Real-time stock quote data."""

    model_config = MODEL_CONFIG

    buy: float | None = None
    sell: float | None = None
    last: float | None = None
    highest: float | None = None
    lowest: float | None = None
    change: float | None = None
    changePercent: float | None = None
    spread: float | None = None
    timeOfLast: int | None = None
    totalValueTraded: float | None = None
    totalVolumeTraded: float | None = None
    updated: int | None = None
    volumeWeightedAveragePrice: float | None = None
    isRealTime: bool | None = None


class Listing(BaseModel):
    """Stock listing information."""

    model_config = MODEL_CONFIG

    shortName: str
    tickerSymbol: str | None = None
    countryCode: str | None = None
    currency: str
    marketPlaceCode: str | None = None
    marketPlaceName: str
    tickSizeListId: str | None = None
    marketTradesAvailable: bool | None = None


class MarketPlace(BaseModel):
    """Market place information."""

    model_config = MODEL_CONFIG

    marketOpen: bool
    tradingTime: str | None = None
    closingTime: str | None = None
    country: str | None = None
    name: str | None = None


class ShareInfo(BaseModel):
    """Share value information."""

    model_config = MODEL_CONFIG

    value: float
    currency: str


class ReportInfo(BaseModel):
    """Company report information."""

    model_config = MODEL_CONFIG

    date: str
    reportType: str


class Sector(BaseModel):
    """Stock sector classification."""

    model_config = MODEL_CONFIG

    sectorId: str
    sectorName: str


class KeyIndicators(BaseModel):
    """Stock key financial indicators."""

    model_config = MODEL_CONFIG

    numberOfOwners: int | None = None
    reportDate: str | None = None
    volatility: float | None = None
    beta: float | None = None
    priceEarningsRatio: float | None = None
    priceSalesRatio: float | None = None
    evEbitRatio: float | None = None
    returnOnEquity: float | None = None
    returnOnTotalAssets: float | None = None
    equityRatio: float | None = None
    capitalTurnover: float | None = None
    operatingProfitMargin: float | None = None
    netMargin: float | None = None
    marketCapital: ShareInfo | None = None
    equityPerShare: ShareInfo | None = None
    turnoverPerShare: ShareInfo | None = None
    earningsPerShare: ShareInfo | None = None
    dividendsPerYear: int | None = None
    nextReport: ReportInfo | None = None
    previousReport: ReportInfo | None = None
    directYield: float | None = None


class HistoricalClosingPrices(BaseModel):
    """Historical closing prices."""

    model_config = MODEL_CONFIG

    oneDay: float | None = None
    oneWeek: float | None = None
    oneMonth: float | None = None
    threeMonths: float | None = None
    startOfYear: float | None = None
    oneYear: float | None = None
    threeYears: float | None = None
    fiveYears: float | None = None
    start: float | None = None


class Company(BaseModel):
    """Company information."""

    model_config = MODEL_CONFIG

    name: str | None = None
    description: str | None = None
    ceo: str | None = None
    chairman: str | None = None
    url: str | None = None
    marketCapital: ShareInfo | None = None


class StockInfo(BaseModel):
    """Complete stock information from Avanza API."""

    model_config = MODEL_CONFIG

    orderbookId: str
    name: str
    isin: str | None = None
    instrumentId: str | None = None
    sectors: list[Sector] = []
    tradable: str | None = None
    listing: Listing
    marketPlace: MarketPlace | None = None
    historicalClosingPrices: HistoricalClosingPrices | None = None
    keyIndicators: KeyIndicators | None = None
    quote: Quote
    type: str | None = None
    company: Company | None = None
    relatedStocks: list | None = None
    dividends: list | None = None


# === Models for additional endpoints ===


class OHLCDataPoint(BaseModel):
    """OHLC (Open, High, Low, Close) data point for price charts."""

    model_config = MODEL_CONFIG

    timestamp: int
    open: float
    close: float
    low: float
    high: float
    totalVolumeTraded: int


class ChartMetadata(BaseModel):
    """Metadata for price chart responses."""

    model_config = MODEL_CONFIG

    resolution: str | dict | None = None  # Can be string or dict


class StockChart(BaseModel):
    """Stock price chart data with OHLC values."""

    model_config = MODEL_CONFIG

    ohlc: list[OHLCDataPoint]
    metadata: ChartMetadata | None = None
    from_: int | str | None = Field(None, alias="from")  # 'from' is a Python keyword
    to: int | str | None = None  # Can be int or date string
    previousClosingPrice: float | None = None


class MarketplaceInfo(BaseModel):
    """Marketplace status and trading hours."""

    model_config = MODEL_CONFIG

    marketOpen: bool
    timeLeftMs: int | None = None
    openingTime: str | None = None
    todayClosingTime: str | None = None
    normalClosingTime: str | None = None


class BrokerTradeSummary(BaseModel):
    """Summary of broker trades for a stock."""

    model_config = MODEL_CONFIG

    brokerCode: str
    sellVolume: int
    buyVolume: int
    netBuyVolume: int
    brokerName: str


class Trade(BaseModel):
    """Individual trade information."""

    model_config = MODEL_CONFIG

    buyer: str
    seller: str
    dealTime: int
    price: float
    volume: int
    matchedOnMarket: bool
    cancelled: bool


class OrderSide(BaseModel):
    """Buy or sell side of an order."""

    model_config = MODEL_CONFIG

    price: float
    volume: int
    priceString: str


class OrderLevel(BaseModel):
    """Single level in the order book depth."""

    model_config = MODEL_CONFIG

    buySide: OrderSide | None = None
    sellSide: OrderSide | None = None


class OrderDepth(BaseModel):
    """Order book depth showing buy and sell orders."""

    model_config = MODEL_CONFIG

    receivedTime: int | None = None  # May be None when market is closed
    levels: list[OrderLevel] = []  # Empty list when no order book data available
