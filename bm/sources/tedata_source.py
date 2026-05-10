"""
Trading Economics (tedata) source for bm.

Scrapes time-series data from Trading Economics charts using Selenium.
No API key required — uses the tedata package's Selenium-based scraping.

Note: Downloads typically take 15-30s per series due to page load + data extraction.
Allow sufficient timeout when calling pull_tedata().
"""

from __future__ import annotations

import enum
import logging
import time
from typing import Optional

import pandas as pd

from ..auxiliary import FrequencyConverter, convert_to_standard_series, calculate_metadata_stats
from ..models import SeriesMetadata, StandardSeries


logger = logging.getLogger(__name__)


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
    """Check if a browser is installed and accessible."""
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
    """Construct a full Trading Economics URL from a series ID/path."""
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
    timeout: int = 60,
) -> StandardSeries:
    """Pull data from Trading Economics via Selenium scraping.

    Args:
        url: Trading Economics chart URL (full URL or path portion)
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)
        browser: Browser preference ('firefox', 'chrome', or 'auto') — default 'auto'
        timeout: Seconds to wait for page load + data extraction (default: 60).
                 Typical downloads take 15-30s; set higher for slow connections.

    Returns:
        StandardSeries with data and metadata

    Raises:
        BrowserNotFoundError: If neither browser is available
        TimeoutError: If page does not load within timeout seconds
        ValueError: If no data returned from the chart
    """
    import tedata as ted

    browser_pref = BrowserPreference(browser) if isinstance(browser, str) else browser
    available_browser = _check_browser_available(browser_pref)
    logger.info(f"pull_tedata: browser={available_browser}, timeout={timeout}s")

    full_url = get_tedata_url(url)
    logger.info(f"pull_tedata: fetching {full_url}")

    t0 = time.time()

    # Retry up to 3 attempts with different driver strategies
    errors = []
    for attempt in range(1, 4):
        use_existing = (attempt == 1)
        try:
            logger.info(f"pull_tedata: attempt {attempt}/3 (use_existing_driver={use_existing})...")
            t_attempt = time.time()

            scraped = ted.scrape_chart(
                url=full_url,
                method="highcharts_api",
                use_existing_driver=use_existing,
            )

            elapsed = time.time() - t_attempt
            logger.info(f"  scrape completed in {elapsed:.1f}s")

            # Validate returned data — tedata returns None on timeout without raising
            if scraped is None:
                raise ValueError("tedata returned None (page load timeout)")

            # Check for data attributes being present
            if not hasattr(scraped, 'metadata') or scraped.metadata is None:
                raise ValueError(f"tedata returned invalid scraped object (metadata=None)")

            meta = scraped.metadata or {}
            if meta.get('error') or not hasattr(scraped, 'series') or scraped.series is None:
                raise ValueError(
                    f"tedata scrape returned empty data: "
                    f"series={getattr(scraped, 'series', None)}, "
                    f"metadata={meta}"
                )

            logger.info(f"  scrape data valid: title='{meta.get('title', '?')}', "
                        f"series_points={len(scraped.series) if scraped.series is not None else 0}")
            break

        except Exception as e:
            err_str = str(e)
            elapsed_total = time.time() - t0
            logger.warning(f"  attempt {attempt} failed after {elapsed_total:.1f}s: {err_str}")
            errors.append(f"attempt {attempt}: {err_str}")

            # Retry on transient errors (stale driver, timeout, network)
            transient = any(
                kw in err_str.lower()
                for kw in ["stale", "webdriver", "timeout", "timed out", "connection", "network"]
            )
            if not transient:
                raise ValueError(
                    f"pull_tedata failed for {full_url} after {elapsed_total:.1f}s: {err_str}"
                ) from e

            logger.info("  -> retrying with fresh driver...")
            continue
    else:
        total_time = time.time() - t0
        raise TimeoutError(
            f"pull_tedata timed out after {total_time:.1f}s for {full_url}. "
            f"Errors: {'; '.join(errors)}"
        )

    total_elapsed = time.time() - t0
    logger.info(f"pull_tedata: succeeded in {total_elapsed:.1f}s")

    # Get the series and metadata
    series = scraped.series
    te_meta = scraped.metadata

    if series is None or len(series) == 0:
        raise ValueError(f"No data returned from Trading Economics for URL: {full_url}")

    # Convert to standard series
    series = convert_to_standard_series(series)
    series.name = te_meta.get('ID', url.split('/')[-1])

    # Filter by date range
    if start_date:
        series = series[series.index >= pd.Timestamp(start_date)]
    if end_date:
        series = series[series.index <= pd.Timestamp(end_date)]

    # Map frequency
    te_freq = te_meta.get('frequency', None)
    std_freq = FrequencyConverter.standardize(te_freq) if te_freq else 'D'

    original_source = te_meta.get('original_source', 'Trading Economics')

    metadata = SeriesMetadata(
        id=te_meta.get('ID', series.name),
        title=te_meta.get('title', series.name),
        source='tedata',
        original_source=original_source,
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
    timeout: int = 60,
) -> pd.DataFrame:
    """Search Trading Economics and return results.

    Args:
        query: Search query string
        browser: Browser preference ('firefox', 'chrome', or 'auto') — default 'auto'
        timeout: Seconds to wait for search results (default: 60)

    Returns:
        DataFrame with columns: country, metric, url
    """
    import tedata as ted

    browser_pref = BrowserPreference(browser) if isinstance(browser, str) else browser
    available_browser = _check_browser_available(browser_pref)
    logger.info(f"search_tedata: browser={available_browser}, timeout={timeout}s, query='{query}'")

    t0 = time.time()
    errors = []

    for attempt in range(1, 4):
        use_existing = (attempt == 1)
        try:
            logger.info(f"search_tedata: attempt {attempt}/3 (use_existing_driver={use_existing})...")
            search = ted.search_TE(use_existing_driver=use_existing)
            search.search_trading_economics(query)
            result_table = search.result_table
            elapsed = time.time() - t0
            logger.info(f"search_tedata: completed in {elapsed:.1f}s, {len(result_table) if result_table is not None else 0} results")
            if result_table is not None and len(result_table) > 0:
                return result_table
            return pd.DataFrame(columns=['country', 'metric', 'url'])
        except Exception as e:
            err_str = str(e)
            elapsed_total = time.time() - t0
            logger.warning(f"  search attempt {attempt} failed after {elapsed_total:.1f}s: {err_str}")
            errors.append(f"attempt {attempt}: {err_str}")

            transient = any(
                kw in err_str.lower()
                for kw in ["stale", "webdriver", "timeout", "timed out", "connection", "network"]
            )
            if not transient:
                logger.error(f"search_tedata non-transient error: {err_str}")
                return pd.DataFrame(columns=['country', 'metric', 'url'])
            continue

    total_time = time.time() - t0
    logger.warning(f"search_tedata timed out after {total_time:.1f}s. Errors: {'; '.join(errors)}")
    return pd.DataFrame(columns=['country', 'metric', 'url'])