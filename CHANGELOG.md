# Changelog

All notable changes to this project will be documented in this file.

## [1.2.0] - 2026-02-05

### Added
- **Certificates Support** (3 tools)
  - `filter_certificates` - Search and filter certificates with pagination
  - `get_certificate_info` - Get detailed certificate information
  - `get_certificate_details` - Get extended certificate details

- **Warrants Support** (3 tools)
  - `filter_warrants` - Search and filter warrants (turbos, minis)
  - `get_warrant_info` - Get detailed warrant information
  - `get_warrant_details` - Get extended warrant details

- **ETFs Support** (3 tools)
  - `filter_etfs` - Search and filter exchange-traded funds
  - `get_etf_info` - Get detailed ETF information
  - `get_etf_details` - Get extended ETF details

- **Futures/Forwards Support** (4 tools)
  - `list_futures_forwards` - List available futures and forwards
  - `get_future_forward_filter_options` - Get available filter options
  - `get_future_forward_info` - Get contract information
  - `get_future_forward_details` - Get extended contract details

- **Additional Data Tools** (3 tools)
  - `get_number_of_owners` - Get owner count for any instrument
  - `get_short_selling` - Get short selling data for instruments
  - `get_marketmaker_chart` - Get OHLC price chart data for traded products (certificates, warrants, ETFs)

- **New Models**
  - `models/chart.py` - Chart data models (ChartData, OHLCDataPoint, ChartMetadata)
  - `models/filter.py` - Shared filter models (SortBy, UnderlyingInstrument)
  - `models/certificate.py` - Certificate models
  - `models/warrant.py` - Warrant models
  - `models/etf.py` - ETF models
  - `models/future_forward.py` - Future/Forward models
  - `models/instrument_data.py` - Additional instrument data models

- **16 New API Endpoints**
  - Certificate endpoints (filter, info, details)
  - Warrant endpoints (filter, info, details)
  - ETF endpoints (filter, info, details)
  - Futures/Forwards endpoints (matrix, filter-options, info, details)
  - Additional data endpoints (number_of_owners, short_selling)
  - Chart endpoint (marketmaker)

### Changed
- Tool count increased from 18 to 34 tools
- `MarketDataService` extended with 15 new methods
- **Test Structure Reorganized** - Split monolithic test files into domain-specific files following clean code practices:
  - Unit tests: 7 separate files by domain (filter, certificate, warrant, ETF, futures/forwards, instrument data, chart models)
  - Integration tests: 6 separate files by domain (certificates, warrants, ETFs, futures/forwards, instrument data, chart endpoints)

## [1.1.0] - Previous Release

(Previous changelog entries would go here)
