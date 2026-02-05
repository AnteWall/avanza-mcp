"""Additional instrument data models."""

from pydantic import BaseModel

from .stock import MODEL_CONFIG


class NumberOfOwners(BaseModel):
    """Number of owners for an instrument."""

    model_config = MODEL_CONFIG

    orderbookId: str | None = None
    numberOfOwners: int | None = None
    timestamp: int | None = None


class ShortSellingData(BaseModel):
    """Short selling data for an instrument."""

    model_config = MODEL_CONFIG

    orderbookId: str | None = None
    shortSellingVolume: float | None = None
    shortSellingPercentage: float | None = None
    date: str | None = None
