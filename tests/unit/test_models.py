"""Unit tests for Pydantic models."""

import pytest
from datetime import date
from decimal import Decimal

from avanza_mcp.models.stock import (
    Quote,
    StockInfo,
    Listing,
    StockChart,
    OHLCDataPoint,
    OrderDepth,
    OrderLevel,
    OrderSide,
)
from avanza_mcp.models.fund import (
    FundInfo,
    FundPerformance,
    FundSustainability,
    ChartDataPoint,
)
from avanza_mcp.models.search import (
    SearchResponse,
    SearchHit,
    SearchPrice,
)


class TestStockModels:
    """Tests for stock-related models."""

    def test_quote_with_all_fields(self):
        """Test Quote model with all fields."""
        data = {
            "buy": 100.5,
            "sell": 101.0,
            "last": 100.75,
            "highest": 102.0,
            "lowest": 99.5,
            "change": 0.25,
            "changePercent": 0.25,
            "spread": 0.5,
            "totalValueTraded": 1000000.0,
            "totalVolumeTraded": 10000.0,
            "isRealTime": True,
        }
        quote = Quote.model_validate(data)
        assert quote.buy == 100.5
        assert quote.last == 100.75
        assert quote.isRealTime is True

    def test_quote_with_extra_fields(self):
        """Test Quote model handles extra fields gracefully."""
        data = {
            "buy": 100.5,
            "sell": 101.0,
            "unknownField": "should not fail",
            "anotherExtra": 123,
        }
        quote = Quote.model_validate(data)
        assert quote.buy == 100.5
        # Extra fields should be stored

    def test_quote_with_missing_optional_fields(self):
        """Test Quote model with missing optional fields."""
        data = {"buy": 100.5}
        quote = Quote.model_validate(data)
        assert quote.buy == 100.5
        assert quote.sell is None
        assert quote.last is None

    def test_listing_model(self):
        """Test Listing model."""
        data = {
            "shortName": "VOLV B",
            "tickerSymbol": "VOLV B",
            "currency": "SEK",
            "marketPlaceName": "Stockholm",
        }
        listing = Listing.model_validate(data)
        assert listing.shortName == "VOLV B"
        assert listing.currency == "SEK"

    def test_stock_info_complex(self):
        """Test StockInfo with nested objects."""
        data = {
            "orderbookId": "5479",
            "name": "Volvo B",
            "isin": "SE0000115446",
            "listing": {
                "shortName": "VOLV B",
                "currency": "SEK",
                "marketPlaceName": "Stockholm",
            },
            "quote": {
                "last": 250.5,
                "changePercent": 1.5,
            },
        }
        stock = StockInfo.model_validate(data)
        assert stock.orderbookId == "5479"
        assert stock.name == "Volvo B"
        assert stock.listing.shortName == "VOLV B"
        assert stock.quote.last == 250.5

    def test_ohlc_data_point(self):
        """Test OHLCDataPoint model."""
        data = {
            "timestamp": 1704067200000,
            "open": 100.0,
            "high": 105.0,
            "low": 99.0,
            "close": 103.0,
            "totalVolumeTraded": 50000,
        }
        point = OHLCDataPoint.model_validate(data)
        assert point.timestamp == 1704067200000
        assert point.open == 100.0
        assert point.high == 105.0

    def test_stock_chart(self):
        """Test StockChart model."""
        data = {
            "ohlc": [
                {
                    "timestamp": 1704067200000,
                    "open": 100.0,
                    "high": 105.0,
                    "low": 99.0,
                    "close": 103.0,
                    "totalVolumeTraded": 50000,
                }
            ],
            "from": 1704067200000,
            "to": 1704153600000,
            "previousClosingPrice": 99.5,
        }
        chart = StockChart.model_validate(data)
        assert len(chart.ohlc) == 1
        assert chart.from_ == 1704067200000  # Alias for 'from'
        assert chart.previousClosingPrice == 99.5

    def test_order_depth(self):
        """Test OrderDepth model."""
        data = {
            "receivedTime": 1704067200000,
            "levels": [
                {
                    "buySide": {"price": 100.0, "volume": 500, "priceString": "100.00"},
                    "sellSide": {"price": 100.5, "volume": 300, "priceString": "100.50"},
                }
            ],
        }
        depth = OrderDepth.model_validate(data)
        assert len(depth.levels) == 1
        assert depth.levels[0].buySide.price == 100.0
        assert depth.levels[0].sellSide.volume == 300


class TestFundModels:
    """Tests for fund-related models."""

    def test_fund_performance(self):
        """Test FundPerformance model with aliases."""
        data = {
            "today": 0.5,
            "oneWeek": 1.2,
            "oneMonth": 2.5,
            "threeMonths": 5.0,
            "thisYear": 8.0,
            "oneYear": 12.0,
            "threeYears": 25.0,
            "fiveYears": 50.0,
        }
        perf = FundPerformance.model_validate(data)
        assert perf.one_week == Decimal("1.2")
        assert perf.three_years == Decimal("25.0")

    def test_fund_info_basic(self):
        """Test FundInfo model with basic fields."""
        data = {
            "name": "Test Fund",
            "isin": "SE0000000001",
            "nav": 150.5,
            "currency": "SEK",
            "risk": 4,
            "rating": 5,
        }
        fund = FundInfo.model_validate(data)
        assert fund.name == "Test Fund"
        assert fund.nav == Decimal("150.5")
        assert fund.risk == 4

    def test_fund_info_with_holdings(self):
        """Test FundInfo model with portfolio holdings."""
        data = {
            "name": "Test Fund",
            "currency": "SEK",
            "countryChartData": [
                {"name": "Sweden", "y": 45.0},
                {"name": "USA", "y": 30.0},
            ],
            "sectorChartData": [
                {"name": "Technology", "y": 25.0},
            ],
            "holdingChartData": [
                {"name": "Apple Inc", "y": 5.0},
            ],
        }
        fund = FundInfo.model_validate(data)
        assert len(fund.country_chart_data) == 2
        assert fund.country_chart_data[0].name == "Sweden"
        assert fund.country_chart_data[0].y == 45.0

    def test_chart_data_point(self):
        """Test ChartDataPoint model."""
        data = {"name": "Test", "y": 25.5}
        point = ChartDataPoint.model_validate(data)
        assert point.name == "Test"
        assert point.y == 25.5

    def test_fund_sustainability(self):
        """Test FundSustainability model."""
        data = {
            "lowCarbon": True,
            "esgScore": 7.5,
            "environmentalScore": 8.0,
            "socialScore": 7.0,
            "governanceScore": 7.5,
            "sustainabilityRating": 4,
            "productInvolvements": [],
        }
        sustainability = FundSustainability.model_validate(data)
        assert sustainability.lowCarbon is True
        assert sustainability.esgScore == 7.5
        assert sustainability.sustainabilityRating == 4


class TestSearchModels:
    """Tests for search-related models."""

    def test_search_price(self):
        """Test SearchPrice model."""
        data = {
            "last": "250.50",
            "currency": "SEK",
            "todayChangePercent": "1.5",
            "todayChangeDirection": 1,
        }
        price = SearchPrice.model_validate(data)
        assert price.last == "250.50"
        assert price.currency == "SEK"

    def test_search_hit(self):
        """Test SearchHit model."""
        data = {
            "type": "STOCK",
            "title": "Volvo B",
            "highlightedTitle": "<b>Volvo</b> B",
            "description": "Swedish automotive company",
            "highlightedDescription": "Swedish automotive company",
            "orderBookId": "5479",
            "urlSlugName": "volvo-b",
            "tradeable": True,
            "sellable": True,
            "buyable": True,
            "marketPlaceName": "Stockholm",
            "price": {"last": "250.50", "currency": "SEK"},
        }
        hit = SearchHit.model_validate(data)
        assert hit.type == "STOCK"
        assert hit.title == "Volvo B"
        assert hit.orderBookId == "5479"
        assert hit.price.last == "250.50"

    def test_search_response(self):
        """Test SearchResponse model."""
        data = {
            "totalNumberOfHits": 100,
            "hits": [
                {
                    "type": "STOCK",
                    "title": "Test Stock",
                    "highlightedTitle": "Test Stock",
                    "description": "A test stock",
                    "highlightedDescription": "A test stock",
                    "urlSlugName": "test-stock",
                    "tradeable": True,
                    "sellable": True,
                    "buyable": True,
                    "marketPlaceName": "Stockholm",
                }
            ],
            "searchQuery": "test",
            "searchFilter": {"types": []},
            "facets": {"types": [{"type": "STOCK", "count": 50}]},
            "pagination": {"size": 10, "from": 0},
        }
        response = SearchResponse.model_validate(data)
        assert response.totalNumberOfHits == 100
        assert len(response.hits) == 1
        assert response.searchQuery == "test"
        assert response.pagination.size == 10
        assert response.pagination.from_ == 0  # Alias for 'from'


class TestModelConfig:
    """Tests for model configuration."""

    def test_extra_fields_allowed(self):
        """Test that extra fields from API don't break models."""
        data = {
            "buy": 100.0,
            "unknownField1": "test",
            "unknownField2": 123,
            "nestedUnknown": {"a": 1},
        }
        quote = Quote.model_validate(data)
        assert quote.buy == 100.0

    def test_populate_by_name(self):
        """Test that both alias and field names work."""
        # Using alias
        data1 = {"oneWeek": 1.5}
        perf1 = FundPerformance.model_validate(data1)
        assert perf1.one_week == Decimal("1.5")

        # Using field name
        data2 = {"one_week": 2.0}
        perf2 = FundPerformance.model_validate(data2)
        assert perf2.one_week == Decimal("2.0")

    def test_whitespace_stripping(self):
        """Test that whitespace is stripped from strings."""
        data = {
            "shortName": "  VOLV B  ",
            "currency": " SEK ",
            "marketPlaceName": "Stockholm  ",
        }
        listing = Listing.model_validate(data)
        assert listing.shortName == "VOLV B"
        assert listing.currency == "SEK"
        assert listing.marketPlaceName == "Stockholm"
