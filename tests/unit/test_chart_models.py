"""Unit tests for chart models."""

import pytest

from avanza_mcp.models.chart import ChartData


@pytest.fixture
def chart_payload():
    return {
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
        "from": "2026-02-05",
        "to": "2026-02-05",
        "metadata": {
            "resolution": {
                "chartResolution": "minute",
                "availableResolutions": ["minute", "hour", "day"],
            }
        },
    }


class TestChartModels:
    """Test chart models."""

    def test_chart_data_marketmaker(self, chart_payload):
        """Test nested chart components and the marketMaker array."""
        chart_payload["marketMaker"] = []
        chart = ChartData.model_validate(chart_payload)
        assert len(chart.ohlc) == 1
        assert chart.marketMaker == []
        assert chart.to == "2026-02-05"
        point = chart.ohlc[0]
        assert point.timestamp == 1770280320000
        assert point.open == 1.4776
        assert point.totalVolumeTraded == 5098
        resolution = chart.metadata.resolution
        assert resolution.chartResolution == "minute"
        assert len(resolution.availableResolutions) == 3

    def test_chart_data_with_previous_close(self, chart_payload):
        """Test ChartData with previousClosingPrice."""
        chart_payload["ohlc"][0] = {
            "timestamp": 1770278400000,
            "open": 745.1,
            "close": 746.0,
            "low": 745.1,
            "high": 746.0,
            "totalVolumeTraded": 155,
        }
        chart_payload["metadata"]["resolution"]["availableResolutions"] = ["minute", "day"]
        chart_payload["previousClosingPrice"] = 749.2
        chart = ChartData.model_validate(chart_payload)
        assert chart.previousClosingPrice == 749.2
        assert len(chart.ohlc) == 1
        assert chart.ohlc[0].open == 745.1

    def test_chart_data_serialization(self, chart_payload):
        """Test chart data serializes correctly with alias for 'from'."""
        chart_payload["ohlc"][0].update(
            open=1.0, close=1.0, low=1.0, high=1.0, totalVolumeTraded=100
        )
        chart_payload["metadata"]["resolution"] = {
            "chartResolution": "day",
            "availableResolutions": ["day"],
        }
        chart_payload["from"] = "2026-02-01"
        chart = ChartData.model_validate(chart_payload)
        serialized = chart.model_dump(by_alias=True, exclude_none=True)
        assert serialized["from"] == "2026-02-01"
        assert serialized["to"] == "2026-02-05"
