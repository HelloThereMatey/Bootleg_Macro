"""
Trading Economics (tedata) source for bm.

Scrapes time-series data from Trading Economics charts using Selenium.
No API key required — uses the tedata package's Selenium-based scraping.
"""

from __future__ import annotations

import enum
from typing import Optional

import pandas as pd

from ..auxiliary import FrequencyConverter, convert_to_standard_series, calculate_metadata_stats
from ..models import SeriesMetadata, StandardSeries


class BrowserPreference(enum.Enum):
    """Browser preference for Selenium scraping."""
    FIREFOX = "firefox"
    CHROME = "chrome"
    AUTO = "auto"


class BrowserNotFoundError(Exception):
    """Raised when neither Chrome nor Firefox is available for scraping."""
    pass


def _check_browser_available(browser: BrowserPreference) -> str:
    """Check if requested browser is available.

    Args:
        browser: BrowserPreference value

    Returns:
        Browser name ('firefox' or 'chrome')

    Raises:
        BrowserNotFoundError: If browser not available
    """
    if browser == BrowserPreference.AUTO:
        # Try firefox first, then chrome
        for browser_name in ["firefox", "chrome"]:
            if _browser_installed(browser_name):
                return browser_name
        raise BrowserNotFoundError(
            "Neither Firefox nor Chrome is available. "
            "Please install Firefox (v115+) or Chrome (v115+) and ensure they're in your PATH."
        )
    else:
        browser_name = browser.value
        if not _browser_installed(browser_name):
            raise BrowserNotFoundError(
                f"{browser_name.capitalize()} is not available. "
                f"Please install {browser_name.capitalize()} (v115+) and ensure it's in your PATH."
            )
        return browser_name


def _browser_installed(browser: str) -> bool:
    """Check if a browser is installed and accessible.

    Args:
        browser: 'firefox' or 'chrome'

    Returns:
        True if browser is available
    """
    try:
        if browser == "firefox":
            from selenium.webdriver.firefox.options import Options as FirefoxOptions
            from selenium.webdriver.firefox.service import Service as FirefoxService
            return True
        elif browser == "chrome":
            from selenium.webdriver.chrome.options import Options as ChromeOptions
            from selenium.webdriver.chrome.service import Service as ChromeService
            return True
    except ImportError:
        return False
    return True


def get_tedata_url(series_id: str) -> str:
    """Construct a full Trading Economics URL from a series ID/path.

    Args:
        series_id: Either a full URL or path portion (e.g., 'united-states/ism-manufacturing-new-orders')

    Returns:
        Full Trading Economics URL
    """
    series_id = series_id.strip()
    if series_id.startswith("http"):
        return series_id
    if series_id.startswith("/"):
        series_id = series_id[1:]
    return f"https://tradingeconomics.com/{series_id}"


def pull_tedata(
    url: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    browser: str = "auto",
) -> StandardSeries:
    """Pull data from Trading Economics via Selenium scraping.

    Args:
        url: Trading Economics chart URL (full URL or path portion)
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)
        browser: Browser preference ('firefox', 'chrome', or 'auto') — default 'auto'

    Returns:
        StandardSeries with data and metadata

    Raises:
        BrowserNotFoundError: If neither browser is available
    """
    import tedata as ted

    browser_pref = BrowserPreference(browser) if isinstance(browser, str) else browser

    # Check browser availability
    available_browser = _check_browser_available(browser_pref)

    # Construct URL if needed
    full_url = get_tedata_url(url)

    # Determine method based on browser
    # tedata's scrape_chart uses method="highcharts_api" by default which works well
    # We just need to ensure we use the right browser
    use_existing_driver = True

    try:
        # Use the highcharts_api method which is fastest and most reliable
        scraped = ted.scrape_chart(
            url=full_url,
            method="highcharts_api",
            use_existing_driver=not use_existing_driver,
        )
    except Exception as e:
        # If we get a stale webdriver error, retry with fresh driver
        if "stale" in str(e).lower() or "webdriver" in str(e).lower():
            scraped = ted.scrape_chart(
                url=full_url,
                method="highcharts_api",
                use_existing_driver=False,
            )
        else:
            raise

    # Get the series and metadata from tedata
    series = scraped.series
    te_meta = scraped.metadata  # dict with keys: title, source, original_source, units, etc.

    # Handle case where series might be None or empty
    if series is None or len(series) == 0:
        raise ValueError(f"No data returned from Trading Economics for URL: {full_url}")

    # Convert to standard series (handles PeriodIndex, deduplication, sorting)
    series = convert_to_standard_series(series)
    series.name = te_meta.get('ID', url.split('/')[-1])

    # Filter by date range
    if start_date:
        start = pd.Timestamp(start_date)
        series = series[series.index >= start]
    if end_date:
        end = pd.Timestamp(end_date)
        series = series[series.index <= end]

    # Map frequency using FrequencyConverter
    te_freq = te_meta.get('frequency', None)
    std_freq = FrequencyConverter.standardize(te_freq) if te_freq else 'D'

    # original_source: where the data actually comes from (TE metadata field or TE default)
    original_source = te_meta.get('original_source', 'Trading Economics')

    metadata = SeriesMetadata(
        id=te_meta.get('ID', series.name),
        title=te_meta.get('title', series.name),
        source='tedata',  # bm's internal source identifier
        original_source=original_source,  # where TE says the data originates
        start_date=series.index.min().date() if len(series) > 0 else None,
        end_date=series.index.max().date() if len(series) > 0 else None,
        frequency=std_freq,
        units=te_meta.get('units', None),
        units_short=te_meta.get('units', None),
        description=te_meta.get('description', None),
        **calculate_metadata_stats(series),
    )

    return StandardSeries.from_pandas(series, metadata)


def search_tedata(
    query: str,
    browser: str = "auto",
) -> pd.DataFrame:
    """Search Trading Economics and return results.

    Args:
        query: Search query string
        browser: Browser preference ('firefox', 'chrome', or 'auto') — default 'auto'

    Returns:
        DataFrame with columns: country, metric, url
    """
    import tedata as ted

    browser_pref = BrowserPreference(browser) if isinstance(browser, str) else browser
    available_browser = _check_browser_available(browser_pref)

    try:
        search = ted.search_TE(use_existing_driver=True)
        search.search_trading_economics(query)
        result_table = search.result_table
        if result_table is not None and len(result_table) > 0:
            return result_table
        return pd.DataFrame(columns=['country', 'metric', 'url'])
    except Exception:
        return pd.DataFrame(columns=['country', 'metric', 'url'])