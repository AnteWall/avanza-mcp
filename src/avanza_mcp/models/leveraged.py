"""Typed output models for leveraged-instrument screening."""

from typing import Literal

from .common import AvanzaModel

ProductType = Literal["certificate", "warrant"]
ScreenDirection = Literal["long", "short"]


class LeveragedUnderlying(AvanzaModel):
    """Compact underlying identity from the filter response."""

    order_book_id: str
    name: str | None = None
    instrument_type: str | None = None
    country_code: str | None = None


class LeveragedCandidate(AvanzaModel):
    """Compact discovery facts for one leveraged product."""

    product_type: ProductType
    order_book_id: str
    name: str
    direction: str
    issuer: str
    sub_type: str | None = None
    leverage: float | None = None
    stop_loss: float | None = None
    discovery_bid: float | None = None
    discovery_ask: float | None = None
    upstream_spread: float | None = None
    spread_percent_from_discovery_prices: float | None = None
    total_value_traded: float | None = None
    underlying: LeveragedUnderlying | None = None


class LeveragedFamilySummary(AvanzaModel):
    """Per-family collection status."""

    returned: int
    upstream_total: int | None = None
    truncated: bool
    error: Literal["upstream_unavailable"] | None = None


class LeveragedScreenResponse(AvanzaModel):
    """Bounded combined certificate/warrant discovery response."""

    underlying_order_book_id: str
    direction: ScreenDirection
    families: dict[ProductType, LeveragedFamilySummary]
    products: list[LeveragedCandidate]
    returned: int
    data_note: str
