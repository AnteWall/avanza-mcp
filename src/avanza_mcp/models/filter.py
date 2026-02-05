"""Shared filter models for list/filter endpoints."""

from pydantic import BaseModel, ConfigDict, Field
from typing import Literal


# Standard model config for all models
MODEL_CONFIG = ConfigDict(
    populate_by_name=True,
    str_strip_whitespace=True,
    validate_assignment=True,
    extra="allow",  # Don't fail on extra fields from API
)


class SortBy(BaseModel):
    """Sort configuration for filter endpoints."""

    model_config = MODEL_CONFIG

    field: str
    order: Literal["asc", "desc"]


class PaginationRequest(BaseModel):
    """Pagination parameters for filter endpoints."""

    model_config = MODEL_CONFIG

    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)


class UnderlyingInstrument(BaseModel):
    """Underlying instrument for derivatives."""

    model_config = MODEL_CONFIG

    name: str | None = None
    orderbookId: str | None = None
    instrumentType: str | None = None
    countryCode: str | None = None


class FilterResponse(BaseModel):
    """Base response for filter endpoints with pagination."""

    model_config = MODEL_CONFIG

    pagination: dict | None = None
    totalNumberOfOrderbooks: int | None = None
