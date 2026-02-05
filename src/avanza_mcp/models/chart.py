"""Chart data models for price charts."""

from pydantic import BaseModel, Field

from .stock import MODEL_CONFIG


class OHLCDataPoint(BaseModel):
    """OHLC (Open-High-Low-Close) candlestick data point."""

    model_config = MODEL_CONFIG

    timestamp: int
    open: float
    close: float
    low: float
    high: float
    totalVolumeTraded: int


class ChartResolution(BaseModel):
    """Chart resolution metadata."""

    model_config = MODEL_CONFIG

    chartResolution: str
    availableResolutions: list[str]


class ChartMetadata(BaseModel):
    """Chart metadata."""

    model_config = MODEL_CONFIG

    resolution: ChartResolution


class ChartData(BaseModel):
    """Price chart data response.

    Used for both stock charts and marketmaker charts.
    """

    model_config = MODEL_CONFIG

    ohlc: list[OHLCDataPoint]
    metadata: ChartMetadata
    from_date: str | None = Field(default=None, alias="from")  # 'from' is a Python keyword
    to: str | None = None
    marketMaker: list[dict] | None = None  # Only present in marketmaker charts
    previousClosingPrice: float | None = None  # Only present in some charts
