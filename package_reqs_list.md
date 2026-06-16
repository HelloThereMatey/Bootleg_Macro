Package Dependency Lists
========================
Generated from pyproject.toml files — 2026-06-10

Dependency chain: bootleg-datafeed → bootleg-toolz → bootleg-gui
                                      → bootleg-indexes

---

1. bootleg-datafeed
   Description: Core data acquisition — pull financial/economic time series from 11+ sources
   Requires-python: >=3.11
   Dependencies:
     - pandas>=2.0
     - requests>=2.0
     - pydantic>=2.0
     - yfinance>=0.1
     - numpy>=1.0
     - readabs>=0.1
     - nasdaq-data-link>=0.1
   Optional:
     - tv: [] (tvDatafeedz is local MacroBackend module — install manually)
     - chrome: selenium
     - all: selenium

---

2. bootleg-toolz
   Description: Watchlist management, Plotly charting, and data utilities
   Requires-python: >=3.11
   Dependencies:
     - bootleg-datafeed>=0.1
     - pandas>=2.0
     - plotly>=5.0
     - openpyxl>=3.0
     - tables>=3.0
     - statsmodels>=0.14

---

3. bootleg-gui
   Description: PyQt6 desktop application for interactive watchlist building
   Requires-python: >=3.11
   Dependencies:
     - bootleg-toolz>=0.1
     - PyQt6>=6.0

---

4. bootleg-indexes
   Description: Custom index construction from multiple series (not yet implemented)
   Requires-python: >=3.11
   Dependencies:
     - bootleg-datafeed>=0.1
     - pandas>=2.0
     - numpy>=1.0
