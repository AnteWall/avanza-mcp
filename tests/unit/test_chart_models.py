"""Unit tests for chart models."""

from avanza_mcp.models.chart import (
    ChartData,
    ChartMetadata,
    ChartResolution,
    OHLCDataPoint,
)


class TestChartModels:
    """Test chart models."""

    def test_ohlc_data_point(self):
        """Test OHLCDataPoint model."""
        data = {
            "timestamp": 1770280320000,
            "open": 1.4776,
            "close": 1.4776,
            "low": 1.4776,
            "high": 1.4776,
            "totalVolumeTraded": 5098,
        }
        point = OHLCDataPoint.model_validate(data)
        assert point.timestamp == 1770280320000
        assert point.open == 1.4776
        assert point.totalVolumeTraded == 5098

    def test_chart_resolution(self):
        """Test ChartResolution model."""
        data = {
            "chartResolution": "minute",
            "availableResolutions": ["minute", "hour", "day"],
        }
        resolution = ChartResolution.model_validate(data)
        assert resolution.chartResolution == "minute"
        assert len(resolution.availableResolutions) == 3

    def test_chart_metadata(self):
        """Test ChartMetadata model."""
        data = {
            "resolution": {
                "chartResolution": "minute",
                "availableResolutions": ["minute", "hour"],
            }
        }
        metadata = ChartMetadata.model_validate(data)
        assert metadata.resolution.chartResolution == "minute"

    def test_chart_data_marketmaker(self):
        """Test ChartData with marketMaker array."""
        data = {
            "ohlc": [
                {
                    "timestamp": 1770280320000,
                    "open": 1.4776,
                    "close": 1.4776,
                    "low": 1.4776,
                    "high": 1.4776,
                    "totalVolumeTraded": 5098,
                }
            ],
            "marketMaker": [],
            "from": "2026-02-05",
            "to": "2026-02-05",
            "metadata": {
                "resolution": {
                    "chartResolution": "minute",
                    "availableResolutions": ["minute", "hour", "day"],
                }
            },
        }
        chart = ChartData.model_validate(data)
        assert len(chart.ohlc) == 1
        assert chart.marketMaker == []
        assert chart.to == "2026-02-05"

    def test_chart_data_with_previous_close(self):
        """Test ChartData with previousClosingPrice."""
        data = {
            "ohlc": [
                {
                    "timestamp": 1770278400000,
                    "open": 745.1,
                    "close": 746.0,
                    "low": 745.1,
                    "high": 746.0,
                    "totalVolumeTraded": 155,
                }
            ],
            "metadata": {
                "resolution": {
                    "chartResolution": "minute",
                    "availableResolutions": ["minute", "day"],
                }
            },
            "from": "2026-02-05",
            "to": "2026-02-05",
            "previousClosingPrice": 749.2,
        }
        chart = ChartData.model_validate(data)
        assert chart.previousClosingPrice == 749.2
        assert len(chart.ohlc) == 1
        assert chart.ohlc[0].open == 745.1

    def test_chart_data_serialization(self):
        """Test chart data serializes correctly with alias for 'from'."""
        data = {
            "ohlc": [
                {
                    "timestamp": 1770280320000,
                    "open": 1.0,
                    "close": 1.0,
                    "low": 1.0,
                    "high": 1.0,
                    "totalVolumeTraded": 100,
                }
            ],
            "metadata": {
                "resolution": {
                    "chartResolution": "day",
                    "availableResolutions": ["day"],
                }
            },
            "from": "2026-02-01",
            "to": "2026-02-05",
        }
        chart = ChartData.model_validate(data)
        serialized = chart.model_dump(by_alias=True, exclude_none=True)
        assert serialized["from"] == "2026-02-01"
        assert serialized["to"] == "2026-02-05"
