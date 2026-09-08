"""Common models and enums shared across Avanza API."""

from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_serializer


MODEL_CONFIG = ConfigDict(
    populate_by_name=True,
    str_strip_whitespace=True,
    validate_assignment=True,
    extra="allow",  # Don't fail on extra fields from API
    serialize_by_alias=True,
)


class AvanzaModel(BaseModel):
    """Shared validation configuration for Avanza API models."""

    model_config = MODEL_CONFIG

    @model_serializer(mode="wrap")
    def omit_unreported_optionals(self, handler, info):
        """Keep explicit null/zero/false, without adding absent optional fields to JSON."""
        data = handler(self)
        if info.mode == "json":
            by_alias = (
                info.by_alias
                if info.by_alias is not None
                else self.model_config.get("serialize_by_alias", False)
            )
            for name, field in type(self).model_fields.items():
                if name not in self.model_fields_set and field.default is None:
                    key = (
                        (field.serialization_alias or field.alias or name)
                        if by_alias
                        else name
                    )
                    data.pop(key, None)
        return data


OrderBookId = Annotated[
    str,
    Field(
        pattern=r"^[0-9]+$",
        min_length=1,
        description="Avanza order-book ID from discovery; not the separate instrumentId.",
    ),
]
Offset = Annotated[int, Field(ge=0)]
Limit = Annotated[int, Field(ge=1, le=100)]
SearchLimit = Annotated[int, Field(ge=1, le=50)]
SearchQuery = Annotated[str, Field(min_length=1, max_length=200, pattern=r"\S")]
StockPeriod = Literal[
    "today",
    "one_week",
    "one_month",
    "three_months",
    "this_year",
    "one_year",
    "three_years",
    "five_years",
]
MarketmakerPeriod = Literal[
    "today",
    "one_week",
    "one_month",
    "three_months",
    "six_months",
    "one_year",
    "three_years",
    "five_years",
]
FundPeriod = Literal[
    "one_week",
    "one_month",
    "three_months",
    "this_year",
    "one_year",
    "three_years",
    "five_years",
]


class InstrumentType(str, Enum):
    """Types of financial instruments available on Avanza."""

    STOCK = "STOCK"
    FUND = "FUND"
    BOND = "BOND"
    OPTION = "OPTION"
    FUTURE_FORWARD = "FUTURE_FORWARD"
    CERTIFICATE = "CERTIFICATE"
    WARRANT = "WARRANT"
    ETF = "ETF"
    EXCHANGE_TRADED_FUND = "EXCHANGE_TRADED_FUND"
    INDEX = "INDEX"
    PREMIUM_BOND = "PREMIUM_BOND"
    SUBSCRIPTION_OPTION = "SUBSCRIPTION_OPTION"
    EQUITY_LINKED_BOND = "EQUITY_LINKED_BOND"
    CONVERTIBLE = "CONVERTIBLE"
    FAQ = "FAQ"


class TimePeriod(str, Enum):
    """Time periods for chart data and performance metrics."""

    TODAY = "TODAY"
    ONE_WEEK = "ONE_WEEK"
    ONE_MONTH = "ONE_MONTH"
    THREE_MONTHS = "THREE_MONTHS"
    THIS_YEAR = "THIS_YEAR"
    ONE_YEAR = "ONE_YEAR"
    THREE_YEARS = "THREE_YEARS"
    FIVE_YEARS = "FIVE_YEARS"
    ALL_TIME = "ALL_TIME"


class Resolution(str, Enum):
    """Chart resolution/granularity."""

    MINUTE = "MINUTE"
    FIVE_MINUTES = "FIVE_MINUTES"
    TEN_MINUTES = "TEN_MINUTES"
    THIRTY_MINUTES = "THIRTY_MINUTES"
    HOUR = "HOUR"
    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"


class Direction(str, Enum):
    """Direction for leveraged instruments."""

    LONG = "long"
    SHORT = "short"


class SubType(str, Enum):
    """Sub-types for warrants and certificates."""

    TURBO = "TURBO"
    MINI = "MINI"
    KNOCK_OUT = "KNOCK_OUT"
