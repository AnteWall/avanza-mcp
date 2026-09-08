"""Additional instrument data models."""

from .common import MODEL_CONFIG as MODEL_CONFIG, AvanzaModel


class NumberOfOwners(AvanzaModel):
    """Number of owners for an instrument."""

    orderbookId: str | None = None
    numberOfOwners: int | None = None
    timestamp: int | None = None


class ShortSellingData(AvanzaModel):
    """Short selling data for an instrument."""

    orderbookId: str | None = None
    shortSellingVolume: float | None = None
    shortSellingPercentage: float | None = None
    date: str | None = None
