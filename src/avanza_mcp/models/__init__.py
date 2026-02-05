"""Pydantic models for Avanza API responses."""

from .certificate import (
    CertificateDetails,
    CertificateFilter,
    CertificateFilterRequest,
    CertificateFilterResponse,
    CertificateInfo,
    CertificateListItem,
)
from .chart import ChartData, ChartMetadata, ChartResolution, OHLCDataPoint
from .common import Direction, InstrumentType, SubType, TimePeriod
from .etf import (
    ETFDetails,
    ETFFilter,
    ETFFilterRequest,
    ETFFilterResponse,
    ETFInfo,
    ETFListItem,
)
from .filter import FilterResponse, PaginationRequest, SortBy, UnderlyingInstrument
from .fund import (
    FundChart,
    FundChartPeriod,
    FundDescription,
    FundInfo,
    FundPerformance,
    FundSustainability,
)
from .future_forward import (
    FutureForwardDetails,
    FutureForwardInfo,
    FutureForwardMatrixFilter,
    FutureForwardMatrixRequest,
    FutureForwardMatrixResponse,
)
from .instrument_data import NumberOfOwners, ShortSellingData
from .search import SearchHit, SearchResponse
from .stock import (
    BrokerTradeSummary,
    MarketplaceInfo,
    OrderDepth,
    Quote,
    StockChart,
    StockInfo,
    Trade,
)
from .warrant import (
    WarrantDetails,
    WarrantFilter,
    WarrantFilterRequest,
    WarrantFilterResponse,
    WarrantInfo,
    WarrantListItem,
)

__all__ = [
    # Certificate models
    "CertificateInfo",
    "CertificateDetails",
    "CertificateListItem",
    "CertificateFilter",
    "CertificateFilterRequest",
    "CertificateFilterResponse",
    # Chart models
    "ChartData",
    "OHLCDataPoint",
    "ChartMetadata",
    "ChartResolution",
    # Common
    "InstrumentType",
    "TimePeriod",
    "Direction",
    "SubType",
    # ETF models
    "ETFInfo",
    "ETFDetails",
    "ETFListItem",
    "ETFFilter",
    "ETFFilterRequest",
    "ETFFilterResponse",
    # Filter models
    "SortBy",
    "PaginationRequest",
    "UnderlyingInstrument",
    "FilterResponse",
    # Fund models
    "FundInfo",
    "FundPerformance",
    "FundSustainability",
    "FundChart",
    "FundChartPeriod",
    "FundDescription",
    # Future/Forward models
    "FutureForwardInfo",
    "FutureForwardDetails",
    "FutureForwardMatrixFilter",
    "FutureForwardMatrixRequest",
    "FutureForwardMatrixResponse",
    # Instrument data
    "NumberOfOwners",
    "ShortSellingData",
    # Search models
    "SearchResponse",
    "SearchHit",
    # Stock models
    "StockInfo",
    "Quote",
    "StockChart",
    "MarketplaceInfo",
    "BrokerTradeSummary",
    "Trade",
    "OrderDepth",
    # Warrant models
    "WarrantInfo",
    "WarrantDetails",
    "WarrantListItem",
    "WarrantFilter",
    "WarrantFilterRequest",
    "WarrantFilterResponse",
]
