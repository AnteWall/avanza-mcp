"""Observed owner and short-selling history envelopes, without inferred units."""

from pydantic import Field

from .common import AvanzaModel


class OwnersPoint(AvanzaModel):
    timestamp: int
    numberOfOwners: int = Field(ge=0)


class OwnersHistorySummary(AvanzaModel):
    oneYearChangePercent: float | None = None
    oneYearChange: int | None = None
    thisYearChangePercent: float | None = None
    thisYearChange: int | None = None


class NumberOfOwners(AvanzaModel):
    """Required history array; an explicit empty array is valid."""

    ownersPoints: list[OwnersPoint]
    historySummary: OwnersHistorySummary | None = None


class ShortSellingPoint(AvanzaModel):
    timestamp: int
    ratio: float


class ShortSellingData(AvanzaModel):
    """Required history array; ratio is returned without conversion."""

    shortSellingHistory: list[ShortSellingPoint]
