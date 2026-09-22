"""Future and forward contract models."""

from datetime import date

from pydantic import Field, field_validator

from .common import MODEL_CONFIG as MODEL_CONFIG, AvanzaModel, OrderBookId
from .filter import (
    FilterOption,
    PaginationRequest,
    PaginationResponse,
    SortBy,
    UnderlyingInstrument,
)
from .stock import (
    BrokerTradeSummary,
    Documents,
    HistoricalClosingPrices,
    Listing,
    OrderDepth,
    Quote,
    Trade,
    UnderlyingInfo,
)


class FutureForwardKeyIndicators(AvanzaModel):
    parity: float | None = None
    endDate: str | None = None
    numberOfOwners: int | None = None


class FutureForwardInfo(AvanzaModel):
    """Detailed future/forward information."""

    orderbookId: str
    name: str
    isin: str | None = None
    tradable: str | None = None
    listing: Listing | None = None
    historicalClosingPrices: HistoricalClosingPrices | None = None
    keyIndicators: FutureForwardKeyIndicators | None = None
    quote: Quote | None = None
    type: str | None = None
    underlying: UnderlyingInfo | None = None


class FutureForwardDetails(AvanzaModel):
    """Detailed future/forward extended information."""

    underlying: UnderlyingInfo | None = None
    documents: Documents | None = None
    orderDepth: OrderDepth | None = None
    brokerTradeSummaries: list[BrokerTradeSummary] = Field(default_factory=list)
    trades: list[Trade] = Field(default_factory=list)
    collateralValue: float | None = None
    tradingUnit: float | None = None


class FutureForwardMatrixFilter(AvanzaModel):
    """Filter criteria for futures/forwards matrix."""

    underlyingInstruments: list[OrderBookId] = []
    optionTypes: list[str] = []
    endDates: list[str] = []
    callIndicators: list[str] = []

    @field_validator("endDates")
    @classmethod
    def validate_end_dates(cls, values: list[str]) -> list[str]:
        return [date.fromisoformat(value).isoformat() for value in values]


class FutureForwardMatrixRequest(PaginationRequest):
    """Request for futures/forwards matrix list."""

    filter: FutureForwardMatrixFilter
    sortBy: SortBy


class FutureForwardListItem(AvanzaModel):
    orderbookId: str
    countryCode: str
    name: str
    endDate: str
    hasPosition: bool
    change: float | None = None
    changePercent: float | None = None
    buyPrice: float | None = None
    sellPrice: float | None = None
    lastPrice: float | None = None
    highestPrice: float | None = None
    lowestPrice: float | None = None
    totalVolumeTraded: int | None = None


class FutureForwardOptionLeg(AvanzaModel):
    orderbookId: str
    countryCode: str
    name: str
    hasPosition: bool
    strikePrice: float
    buyPrice: float | None = None
    sellPrice: float | None = None
    buyVolume: int | None = None
    sellVolume: int | None = None
    callIndicator: str


class MatchedOption(AvanzaModel):
    put: FutureForwardOptionLeg | None = None
    call: FutureForwardOptionLeg | None = None


class FutureForwardResponseFilter(AvanzaModel):
    optionTypes: list[str] = Field(default_factory=list)
    yearMonths: list[str] = Field(default_factory=list)
    endDates: list[str] = Field(default_factory=list)
    underlyingInstruments: list[OrderBookId] = Field(default_factory=list)
    callIndicators: list[str] = Field(default_factory=list)


class FutureForwardUnderlyingOption(UnderlyingInstrument):
    highestPrice: float | None = None
    lowestPrice: float | None = None
    lastPrice: float | None = None
    change: float | None = None
    changePercent: float | None = None


class FutureForwardFilterOptions(AvanzaModel):
    underlyingInstruments: list[FilterOption] = Field(default_factory=list)
    optionTypes: list[FilterOption] = Field(default_factory=list)
    endDates: list[FilterOption] = Field(default_factory=list)
    callIndicators: list[FilterOption] = Field(default_factory=list)


class FutureForwardMatrixResponse(AvanzaModel):
    """Response from futures/forwards matrix endpoint."""

    futureForwards: list[FutureForwardListItem] = Field(default_factory=list)
    matchedOptions: list[MatchedOption] = Field(default_factory=list)
    filter: FutureForwardResponseFilter | None = None
    filterOptions: FutureForwardFilterOptions | None = None
    underlyingInstrument: FutureForwardUnderlyingOption | None = None
    pagination: PaginationResponse | None = None
    totalNumberOfOrderbooks: int | None = None
    sortBy: SortBy | None = None
