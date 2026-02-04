"""Common models and enums shared across Avanza API."""

from enum import Enum


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
