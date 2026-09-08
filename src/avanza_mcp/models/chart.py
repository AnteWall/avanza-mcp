"""Chart data models for price charts."""

from pydantic import Field

from .common import MODEL_CONFIG as MODEL_CONFIG, AvanzaModel


class OHLCDataPoint(AvanzaModel):
    """OHLC (Open-High-Low-Close) candlestick data point."""

    timestamp: int
    open: float
    close: float
    low: float
    high: float
    totalVolumeTraded: int


class ChartResolution(AvanzaModel):
    """Chart resolution metadata."""

    chartResolution: str
    availableResolutions: list[str]


class ChartMetadata(AvanzaModel):
    """Chart metadata."""

    resolution: ChartResolution


class ChartData(AvanzaModel):
    """Price chart data response.

    Used for both stock charts and marketmaker charts.
    """

    ohlc: list[OHLCDataPoint]
    metadata: ChartMetadata
    from_date: str | None = Field(default=None, alias="from")  # 'from' is a Python keyword
    to: str | None = None
    marketMaker: list[dict] | None = None  # Only present in marketmaker charts
    previousClosingPrice: float | None = None  # Only present in some charts
