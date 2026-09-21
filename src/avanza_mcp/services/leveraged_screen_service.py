"""Bounded server-side aggregation for leveraged instrument discovery."""

from __future__ import annotations

import asyncio
from typing import Any

from ..client.base import AvanzaClient
from ..client.exceptions import AvanzaError
from ..models.certificate import CertificateFilter, CertificateFilterRequest
from ..models.filter import SortBy
from ..models.leveraged import (
    LeveragedCandidate,
    LeveragedFamilySummary,
    LeveragedScreenResponse,
    LeveragedUnderlying,
    ProductType,
    ScreenDirection,
)
from ..models.warrant import WarrantFilter, WarrantFilterRequest
from .market_data_service import MarketDataService

_PAGE_SIZE = 100
_MAX_PER_TYPE = 200


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _discovery_spread_percent(bid: Any, ask: Any) -> float | None:
    """Calculate midpoint spread from discovery prices without implying executability."""
    bid_value = _number(bid)
    ask_value = _number(ask)
    if (
        bid_value is None
        or ask_value is None
        or bid_value <= 0
        or ask_value <= 0
        or ask_value < bid_value
    ):
        return None
    midpoint = (bid_value + ask_value) / 2
    return round((ask_value - bid_value) / midpoint * 100, 6)


def _normalize_underlying(value: Any) -> LeveragedUnderlying | None:
    if not isinstance(value, dict):
        return None
    data = {
        "order_book_id": value.get("orderbookId"),
        "name": value.get("name"),
        "instrument_type": value.get("instrumentType"),
        "country_code": value.get("countryCode"),
    }
    if not data["order_book_id"]:
        return None
    return LeveragedUnderlying.model_validate(
        {key: item for key, item in data.items() if item is not None}
    )


def _normalize_candidate(item: Any, product_type: ProductType) -> LeveragedCandidate:
    raw = item.model_dump(mode="json", by_alias=True, exclude_none=True)
    bid = _number(raw.get("buyPrice"))
    ask = _number(raw.get("sellPrice"))
    data = {
        "product_type": product_type,
        "order_book_id": raw["orderbookId"],
        "name": raw["name"],
        "direction": raw["direction"],
        "issuer": raw["issuer"],
        "sub_type": raw.get("subType"),
        "leverage": _number(raw.get("leverage")),
        "stop_loss": _number(raw.get("stopLoss")),
        "discovery_bid": bid,
        "discovery_ask": ask,
        "upstream_spread": _number(raw.get("spread")),
        "spread_percent_from_discovery_prices": _discovery_spread_percent(bid, ask),
        "total_value_traded": _number(raw.get("totalValueTraded")),
        "underlying": _normalize_underlying(raw.get("underlyingInstrument")),
    }
    return LeveragedCandidate.model_validate(
        {key: value for key, value in data.items() if value is not None}
    )


class LeveragedScreenService:
    """Aggregate bounded certificate/warrant screens inside one MCP tool call."""

    def __init__(self, client: AvanzaClient) -> None:
        self._market = MarketDataService(client)

    async def _collect_certificates(
        self, underlying_order_book_id: str, direction: ScreenDirection, max_results: int
    ) -> tuple[list[LeveragedCandidate], int | None]:
        products: list[LeveragedCandidate] = []
        offset = 0
        total: int | None = None
        while len(products) < max_results:
            limit = min(_PAGE_SIZE, max_results - len(products))
            response = await self._market.filter_certificates(
                CertificateFilterRequest(
                    filter=CertificateFilter(
                        directions=[direction],
                        underlyingInstruments=[underlying_order_book_id],
                    ),
                    offset=offset,
                    limit=limit,
                    sortBy=SortBy(field="name", order="asc"),
                )
            )
            page = response.certificates
            products.extend(_normalize_candidate(item, "certificate") for item in page)
            total = response.totalNumberOfOrderbooks
            offset += len(page)
            if not page or len(page) < limit or (total is not None and offset >= total):
                break
        return products, total

    async def _collect_warrants(
        self, underlying_order_book_id: str, direction: ScreenDirection, max_results: int
    ) -> tuple[list[LeveragedCandidate], int | None]:
        products: list[LeveragedCandidate] = []
        offset = 0
        total: int | None = None
        while len(products) < max_results:
            limit = min(_PAGE_SIZE, max_results - len(products))
            response = await self._market.filter_warrants(
                WarrantFilterRequest(
                    filter=WarrantFilter(
                        directions=[direction],
                        underlyingInstruments=[underlying_order_book_id],
                    ),
                    offset=offset,
                    limit=limit,
                    sortBy=SortBy(field="name", order="asc"),
                )
            )
            page = response.warrants
            products.extend(_normalize_candidate(item, "warrant") for item in page)
            total = response.totalNumberOfOrderbooks
            offset += len(page)
            if not page or len(page) < limit or (total is not None and offset >= total):
                break
        return products, total

    async def screen(
        self,
        underlying_order_book_id: str,
        direction: ScreenDirection,
        product_types: list[ProductType],
        max_per_type: int,
    ) -> LeveragedScreenResponse:
        if not product_types:
            raise ValueError("product_types must contain at least one product type")
        if len(set(product_types)) != len(product_types):
            raise ValueError("product_types must not contain duplicates")
        if not 1 <= max_per_type <= _MAX_PER_TYPE:
            raise ValueError(f"max_per_type must be between 1 and {_MAX_PER_TYPE}")

        collectors = {
            "certificate": self._collect_certificates,
            "warrant": self._collect_warrants,
        }
        results = await asyncio.gather(
            *[
                collectors[product_type](
                    underlying_order_book_id, direction, max_per_type
                )
                for product_type in product_types
            ],
            return_exceptions=True,
        )

        families: dict[ProductType, LeveragedFamilySummary] = {}
        products: list[LeveragedCandidate] = []
        for product_type, result in zip(product_types, results, strict=True):
            if isinstance(result, AvanzaError):
                families[product_type] = LeveragedFamilySummary(
                    returned=0,
                    truncated=False,
                    error="upstream_unavailable",
                )
                continue
            if isinstance(result, Exception):
                raise result

            family_products, total = result
            families[product_type] = LeveragedFamilySummary(
                returned=len(family_products),
                upstream_total=total,
                truncated=total is not None and len(family_products) < total,
            )
            products.extend(family_products)

        return LeveragedScreenResponse(
            underlying_order_book_id=underlying_order_book_id,
            direction=direction,
            families=families,
            products=products,
            returned=len(products),
            data_note=(
                "Discovery/filter snapshot only. Prices, spread and turnover may be stale "
                "or absent outside market hours and are not execution-verified."
            ),
        )
