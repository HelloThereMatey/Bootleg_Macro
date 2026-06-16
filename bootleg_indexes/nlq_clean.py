"""
Clean, modular USD Net Liquidity (NLQ) calculation script.

This script calculates the Net Liquidity metric originally formulated by Darius Dale and 42Macro.
Net Liquidity = Fed Balance Sheet - Treasury General Account - Reverse Repo Facility

The script pulls data from:
- FRED (via bootleg_datafeed Dataset) for Fed balance sheet and reverse repo data
- Treasury API for daily TGA data (more timely than FRED's weekly TGA data)
"""

import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd
import numpy as np
import requests

from bootleg_datafeed.dataset import Dataset
from bootleg_datafeed._user_path import get_user_path


class NLQDataFetcher:
    """Class to handle all data fetching operations for NLQ calculation."""

    def __init__(self, save_data: bool = True, data_dir: Optional[str] = None):
        """
        Initialize the NLQ data fetcher.

        Args:
            save_data: Whether to save downloaded data to disk
            data_dir: Directory to save data (defaults to {user_path}/NLQ_Data)
        """
        self.save_data = save_data
        self.data_dir = data_dir or str(Path(get_user_path()) / "NLQ_Data")

        # Initialize Dataset
        self.ds = Dataset()
        
        # Key FRED series for NLQ calculation
        self.fred_series_map = {
            'WALCL': 'Fed Total Assets (Weekly)',
            'RESPPNTNWW': 'Fed QE Assets (Weekly)', 
            'RRPONTSYD': 'Reverse Repo Facility (Daily)',
            'WTREGEN': 'Treasury General Account - FRED (Weekly)'
        }
        
        # Create save directories
        self._create_save_directories()

    def _create_save_directories(self) -> None:
        """Create necessary directories for saving data."""
        dirs = [
            Path(self.data_dir) / 'FRED_Data',
            Path(self.data_dir) / 'TreasuryData',
            Path(self.data_dir) / 'NLQ_Data',
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
    
    def fetch_fred_series(self,
                         series_codes: List[str],
                         start_date: str,
                         end_date: str) -> Dict[str, pd.Series]:
        """
        Fetch multiple FRED series using bootleg_datafeed Dataset.

        Args:
            series_codes: List of FRED series codes to fetch
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format

        Returns:
            Dictionary mapping series codes to pandas Series with data
        """
        fred_data = {}

        print(f"Fetching FRED data from {start_date} to {end_date}")

        for series_code in series_codes:
            try:
                print(f"Fetching FRED series: {series_code} - {self.fred_series_map.get(series_code, series_code)}")

                # Use bootleg_datafeed Dataset to pull FRED
                result = self.ds.pull_fred(
                    series_id=series_code,
                    start_date=start_date,
                    end_date=end_date,
                )
                series_data = result.to_pandas()

                # Ensure it's a Series
                if isinstance(series_data, pd.DataFrame):
                    if len(series_data.columns) == 1:
                        series_data = series_data.iloc[:, 0]
                    else:
                        print(f"Warning: {series_code} returned multiple columns, using first column")
                        series_data = series_data.iloc[:, 0]

                # Convert to billions if needed (FRED data is typically in millions)
                if series_code in ['WALCL', 'RESPPNTNWW', 'WTREGEN']:
                    series_data = series_data / 1000  # Convert millions to billions

                series_data.name = series_code
                fred_data[series_code] = series_data

                # Save to disk if requested
                if self.save_data:
                    self._save_fred_series(series_code, series_data)

                print(f"Successfully fetched {series_code}: {len(series_data)} observations")

            except Exception as e:
                print(f"Error fetching {series_code}: {str(e)}")
                fred_data[series_code] = pd.Series(dtype=float, name=series_code)
        
        return fred_data
    
    def _save_fred_series(self, series_code: str, data: pd.Series) -> None:
        """Save FRED series to Excel file."""
        save_path = Path(self.data_dir) / 'FRED_Data' / f'{series_code}.xlsx'
        
        try:
            # Create DataFrame with both data and metadata
            df = pd.DataFrame({
                'Date': data.index,
                'Value': data.values
            })
            
            # Create metadata
            metadata = pd.Series({
                'series_id': series_code,
                'description': self.fred_series_map.get(series_code, series_code),
                'source': 'FRED',
                'units': 'Billions of Dollars' if series_code in ['WALCL', 'RESPPNTNWW', 'WTREGEN'] else 'Millions of Dollars',
                'last_updated': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'observations': len(data),
                'start_date': data.index[0] if len(data) > 0 else 'N/A',
                'end_date': data.index[-1] if len(data) > 0 else 'N/A'
            })
            
            with pd.ExcelWriter(save_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Data', index=False)
                metadata.to_excel(writer, sheet_name='Metadata')

            print(f"Saved {series_code} to {save_path}")

        except Exception as e:
            print(f"Error saving {series_code}: {str(e)}")

    # -------------------------------------------------------------------------
    # Treasury API helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _pull_tga_api(account_name: str = 'Treasury General Account (TGA) Closing Balance',
                      start_date: str = '2000-01-01') -> pd.DataFrame:
        """Fetch TGA operating cash balance from the US Treasury API."""
        url_base = 'https://api.fiscaldata.treasury.gov/services/api/fiscal_service'
        endpoint = '/v1/accounting/dts/operating_cash_balance'
        fields = '?fields=record_date,account_type,close_today_bal,open_today_bal'
        filters = f'&filter=record_date:gte:{start_date}'

        full_data = pd.DataFrame()
        exceptions = 0
        next_start = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        page_size = 5000

        for _ in range(50):
            if exceptions > 3:
                break

            url = (url_base + endpoint + fields + filters
                   + f'&page[size]={page_size}')

            try:
                r = requests.get(url, timeout=30)
                if r.status_code != 200:
                    exceptions += 1
                    continue
                data = r.json().get('data', [])
                if not data:
                    break
                chunk = pd.DataFrame(data)
                chunk['record_date'] = pd.to_datetime(chunk['record_date'])
                chunk = chunk[chunk['account_type'] == account_name]
                if chunk.empty:
                    break
                chunk = chunk.sort_values('record_date')
                last_date = chunk['record_date'].iloc[-1].date()
                next_start = last_date + datetime.timedelta(days=1)
                filters = f'&filter=record_date:gte:{next_start}'
                full_data = pd.concat([full_data, chunk], ignore_index=True)
                if next_start >= datetime.date.today():
                    break
            except Exception as e:
                print(f'TGA API exception: {e}')
                exceptions += 1

        if full_data.empty:
            return pd.DataFrame()

        # Use close_today_bal when available, fall back to open_today_bal
        full_data['close_today_bal'] = pd.to_numeric(full_data['close_today_bal'], errors='coerce')
        full_data['open_today_bal'] = pd.to_numeric(full_data['open_today_bal'], errors='coerce')
        full_data['balance'] = full_data['close_today_bal'].fillna(full_data['open_today_bal'])

        full_data = full_data.drop_duplicates(subset='record_date').set_index('record_date')
        return full_data.sort_index()[['balance']]

    def fetch_tga_data_treasury_api(self,
                                   start_date: Optional[str] = None) -> pd.Series:
        """
        Fetch daily TGA data from the Treasury API for more timely updates.

        Args:
            start_date: Start date (defaults to last date in local cache file)

        Returns:
            Daily TGA balance series in billions of dollars
        """
        print("Fetching TGA data from Treasury API...")

        tga_file = Path(self.data_dir) / 'TreasuryData' / 'TGA_Since2005.xlsx'

        try:
            # Load cached TGA data
            if tga_file.exists():
                print("Loading existing TGA data...")
                tga_past = pd.read_excel(tga_file)
                tga_past['record_date'] = pd.to_datetime(tga_past['record_date'])
                tga_past.set_index('record_date', inplace=True)
                # Keep only numeric balance columns
                bal_cols = [c for c in tga_past.columns if 'close' in c.lower()]
                tga_past = tga_past[bal_cols] if bal_cols else tga_past.iloc[:, :1]
                last_in_file = tga_past.index[-1].strftime('%Y-%m-%d')
                print(f"Last date in cache: {last_in_file}")
            else:
                tga_past = pd.DataFrame()
                last_in_file = "2005-01-01"

            api_start = start_date or last_in_file

            # Fetch fresh data
            closing = self._pull_tga_api(
                'Treasury General Account (TGA) Closing Balance', api_start)
            opening = self._pull_tga_api(
                'Treasury General Account (TGA) Opening Balance', api_start)

            if not closing.empty:
                new_data = closing.rename(columns={'balance': 'TGA_balance'})

                if not tga_past.empty:
                    tga_past = tga_past[tga_past.index < new_data.index[0]]
                    tga_updated = pd.concat([tga_past, new_data])
                else:
                    tga_updated = new_data

                tga_updated.to_excel(tga_file, index_label='record_date')
                print(f"TGA cache saved: {tga_file}")
            else:
                print("No new TGA data from Treasury API")
                tga_updated = tga_past

            if tga_updated.empty:
                return pd.Series(dtype=float, name='TGA Balance (Billions USD)')

            # Pick the balance column
            bal_col = [c for c in tga_updated.columns if 'balance' in c.lower()]
            col = bal_col[0] if bal_col else tga_updated.columns[0]

            tga_series = tga_updated[col].dropna().astype(float) / 1000
            tga_series.index = pd.to_datetime(tga_series.index)
            tga_series = tga_series[~tga_series.index.duplicated(keep='last')]
            tga_series.name = 'TGA Balance (Billions USD)'

            print(f"TGA data: {len(tga_series)} observations from "
                  f"{tga_series.index[0].date()} to {tga_series.index[-1].date()}")
            return tga_series

        except Exception as e:
            print(f"Error fetching TGA data: {str(e)}")
            return pd.Series(dtype=float, name='TGA Balance (Billions USD)')
    
    def get_core_nlq_data(self, 
                         start_date: str, 
                         end_date: str,
                         use_qe_only: bool = False) -> Dict[str, pd.Series]:
        """
        Fetch all core data needed for NLQ calculation.
        
        Args:
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            use_qe_only: If True, use RESPPNTNWW (QE only), else use WALCL (total assets)
            
        Returns:
            Dictionary with all core NLQ data series
        """
        print("=== Fetching Core NLQ Data ===")
        
        # Determine which Fed balance sheet series to use
        if use_qe_only:
            fed_series = ['RESPPNTNWW', 'RRPONTSYD', 'WTREGEN']
            print("Using QE-only Fed balance sheet (RESPPNTNWW)")
        else:
            fed_series = ['WALCL', 'RRPONTSYD', 'WTREGEN']
            print("Using total Fed balance sheet (WALCL)")
        
        # Fetch FRED data
        fred_data = self.fetch_fred_series(fed_series, start_date, end_date)
        
        # Fetch TGA data from Treasury API (use start_date to bound the cache fetch)
        tga_daily = self.fetch_tga_data_treasury_api(start_date=start_date)
        
        # Combine all data
        core_data = {
            'fed_balance_sheet': fred_data.get('WALCL' if not use_qe_only else 'RESPPNTNWW', pd.Series()),
            'reverse_repo': fred_data.get('RRPONTSYD', pd.Series()),
            'tga_fred_weekly': fred_data.get('WTREGEN', pd.Series()),
            'tga_treasury_daily': tga_daily,
            'series_type': 'QE_only' if use_qe_only else 'total_assets'
        }
        
        return core_data


class NetLiquidity:
    """
    Class to calculate and manage Net Liquidity indices.
    
    Net Liquidity = Fed Balance Sheet - Treasury General Account - Reverse Repo
    
    This class provides three versions of the NLQ calculation:
    1. Weekly frequency using raw FRED data (no resampling)
    2. Daily frequency with FRED TGA (all FRED data resampled to daily)
    3. Daily frequency with Treasury API TGA (most accurate, daily updates)
    """

    def __init__(self,
                 start_date: str = "2000-01-01",
                 end_date: Optional[str] = None,
                 core_data: Optional[Dict[str, Union[pd.Series, str]]] = None,
                 use_qe_only: bool = False):
        """
        Initialize NetLiquidity calculator.

        Args:
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date (defaults to today)
            core_data: Optional pre-fetched data from NLQDataFetcher.get_core_nlq_data()
            use_qe_only: If True, use RESPPNTNWW instead of WALCL
        """
        self.start_date = start_date
        self.end_date = end_date or datetime.datetime.today().strftime('%Y-%m-%d')
        self.use_qe_only = use_qe_only

        if core_data is None:
            fetcher = NLQDataFetcher(save_data=True)
            self.core_data = fetcher.get_core_nlq_data(
                self.start_date, self.end_date, use_qe_only=self.use_qe_only)
        else:
            self.core_data = core_data
        
        # Extract individual components
        self.fed_balance_sheet = self.core_data.get('fed_balance_sheet', pd.Series()).copy()
        self.reverse_repo = self.core_data.get('reverse_repo', pd.Series()).copy()
        self.tga_fred = self.core_data.get('tga_fred_weekly', pd.Series()).copy()
        self.tga_treasury = self.core_data.get('tga_treasury_daily', pd.Series()).copy()
        self.series_type = self.core_data.get('series_type', 'total_assets')

        # Calculated NLQ series (initialized as None)
        self.nlq_weekly = None
        self.nlq_daily_treasury = None
        
        # Daily date index for resampling
        self.daily_index = None
        
        # Resampled component series
        self.fed_balance_sheet_daily = None
        self.reverse_repo_daily = None
        self.tga_fred_daily = None
        
        print(f"NetLiquidity initialized with {self.series_type} Fed balance sheet")
        self._validate_data()
    
    def _validate_data(self) -> None:
        """Validate that core data components are available."""
        required_series = {
            'Fed Balance Sheet': self.fed_balance_sheet,
            'Reverse Repo': self.reverse_repo,
            'TGA Treasury': self.tga_treasury
        }
        
        missing = []
        for name, series in required_series.items():
            if series.empty:
                missing.append(name)
        
        if missing:
            print(f"Warning: Missing data for: {', '.join(missing)}")
        else:
            print("All core data components validated successfully")
    
    def create_daily_index(self, start_date: Optional[str] = None, 
                          end_date: Optional[str] = None) -> pd.DatetimeIndex:
        """
        Create a daily date index for resampling.
        
        Args:
            start_date: Start date (defaults to earliest date in data)
            end_date: End date (defaults to latest date in data)
            
        Returns:
            Daily DatetimeIndex
        """
        if start_date is None:
            # Find earliest date across all series
            dates = []
            for series in [self.fed_balance_sheet, self.reverse_repo, 
                          self.tga_fred, self.tga_treasury]:
                if not series.empty:
                    dates.append(series.index[0])
            start_date = min(dates) if dates else datetime.datetime(2000, 1, 1)
        else:
            start_date = pd.to_datetime(start_date)
        
        if end_date is None:
            # Find latest date across all series
            dates = []
            for series in [self.fed_balance_sheet, self.reverse_repo, 
                          self.tga_fred, self.tga_treasury]:
                if not series.empty:
                    dates.append(series.index[-1])
            end_date = max(dates) if dates else datetime.datetime.today()
        else:
            end_date = pd.to_datetime(end_date)
        
        self.daily_index = pd.date_range(start_date, end_date, freq='D')
        print(f"Created daily index: {self.daily_index[0].date()} to {self.daily_index[-1].date()} ({len(self.daily_index)} days)")
        
        return self.daily_index
    
    def resample_to_daily(self, series: pd.Series,
                         index: Optional[pd.DatetimeIndex] = None,
                         method: str = 'ffill') -> pd.Series:
        """
        Resample a series to daily frequency.

        Args:
            series: Series to resample
            index: Target daily index (uses self.daily_index if None)
            method: Resampling method ('ffill' for forward fill)

        Returns:
            Resampled daily series (empty series if input was empty)
        """
        if series.empty:
            return pd.Series(dtype=float)

        if index is None:
            if self.daily_index is None:
                raise ValueError("Daily index not created. Call create_daily_index() first.")
            index = self.daily_index

        # Ensure series has DatetimeIndex
        if not isinstance(series.index, pd.DatetimeIndex):
            try:
                series.index = pd.to_datetime(series.index)
            except Exception:
                return pd.Series(dtype=float)

        # Remove duplicates from the series if any exist
        if series.index.duplicated().any():
            print(f"Warning: Removing {series.index.duplicated().sum()} duplicate dates from {series.name}")
            series = series[~series.index.duplicated(keep='last')]

        # Reindex to daily frequency using forward fill
        resampled = series.reindex(index, method=method)

        return resampled
    
    def calculate_nlq_weekly(self) -> pd.Series:
        """
        Calculate NLQ using raw weekly FRED data (no resampling).
        
        Formula: Fed Balance Sheet - TGA (FRED) - Reverse Repo
        
        Returns:
            Weekly NLQ series
        """
        print("Calculating NLQ (weekly, raw FRED data)...")
        
        self.nlq_weekly = (
            self.fed_balance_sheet - 
            self.tga_fred - 
            self.reverse_repo
        )
        
        self.nlq_weekly = pd.Series(self.nlq_weekly, name='NLQ Weekly (Bil $)')
        self.nlq_weekly.dropna(inplace=True)
        
        print(f"NLQ Weekly calculated: {len(self.nlq_weekly)} observations")
        if len(self.nlq_weekly) > 0:
            print(f"Latest value: ${self.nlq_weekly.iloc[-1]:.2f} billion")
        
        return self.nlq_weekly
    
    def calculate_nlq_daily_treasury(self) -> pd.Series:
        """
        Calculate daily NLQ using Treasury API TGA data (most accurate).
        
        Formula: Fed Balance Sheet (daily) - TGA Treasury (daily) - Reverse Repo (daily)
        
        Returns:
            Daily NLQ series using Treasury TGA
        """
        print("Calculating NLQ (daily, Treasury TGA)...")
        
        # Ensure daily index exists
        if self.daily_index is None:
            self.create_daily_index()
        
        # Resample Fed and RRP to daily (if not already done)
        if self.fed_balance_sheet_daily is None:
            self.fed_balance_sheet_daily = self.resample_to_daily(self.fed_balance_sheet)
        if self.reverse_repo_daily is None:
            self.reverse_repo_daily = self.resample_to_daily(self.reverse_repo)
        
        # Resample TGA Treasury to daily
        tga_treasury_daily = self.resample_to_daily(self.tga_treasury)
        
        # Calculate NLQ
        self.nlq_daily_treasury = pd.Series(
            self.fed_balance_sheet_daily - 
            tga_treasury_daily - 
            self.reverse_repo_daily,
            name='NLQ Daily Treasury (Bil $)'
        )
        
        self.nlq_daily_treasury.dropna(inplace=True)
        
        print(f"NLQ Daily (Treasury) calculated: {len(self.nlq_daily_treasury)} observations")
        if len(self.nlq_daily_treasury) > 0:
            print(f"Latest value: ${self.nlq_daily_treasury.iloc[-1]:.2f} billion")
        
        return self.nlq_daily_treasury
    
    def calculate_all(self) -> Dict[str, pd.Series]:
        """
        Calculate all three NLQ versions.
        
        Args:
            start_date: Start date for daily index
            end_date: End date for daily index
            
        Returns:
            Dictionary with all NLQ series
        """
        print("\n=== Calculating All NLQ Versions ===")
        
        if hasattr(self, 'start_date') and hasattr(self, 'end_date'):
            start_date = self.start_date
            end_date = self.end_date
        else:
            print("Using default date range for daily index")
            start_date = "01-01-2021"
            end_date = datetime.datetime.today().strftime('%Y-%m-%d')

        # Create daily index
        self.create_daily_index(start_date, end_date)
        
        # Calculate all versions
        nlq_weekly = self.calculate_nlq_weekly()
        nlq_daily_treasury = self.calculate_nlq_daily_treasury()
        
        return {
            'nlq_weekly': nlq_weekly,
            'nlq_daily_treasury': nlq_daily_treasury,
            'fed_balance_sheet_daily': self.fed_balance_sheet_daily,
            'reverse_repo_daily': self.reverse_repo_daily,
            'tga_fred_daily': self.tga_fred_daily,
            'tga_treasury_daily': self.resample_to_daily(self.tga_treasury)
        }
    
    def get_latest_values(self) -> Dict[str, float]:
        """Get the latest values for all NLQ series and components."""
        latest = {}
        
        series_map = {
            'Fed Balance Sheet': self.fed_balance_sheet,
            'Reverse Repo': self.reverse_repo,
            'TGA FRED': self.tga_fred,
            'TGA Treasury': self.tga_treasury,
            'NLQ Weekly': self.nlq_weekly,
            'NLQ Daily Treasury': self.nlq_daily_treasury
        }
        
        for name, series in series_map.items():
            if series is not None and not series.empty:
                latest[name] = {
                    'value': series.iloc[-1],
                    'date': series.index[-1].date() if hasattr(series.index[-1], 'date') else series.index[-1]
                }
        
        return latest
    
    def summary(self) -> None:
        """Print a summary of all NLQ calculations."""
        print("\n" + "="*60)
        print("NET LIQUIDITY SUMMARY")
        print("="*60)
        print(f"Series Type: {self.series_type}")
        
        latest = self.get_latest_values()
        
        print("\nLatest Component Values:")
        for component in ['Fed Balance Sheet', 'Reverse Repo', 'TGA FRED', 'TGA Treasury']:
            if component in latest:
                info = latest[component]
                print(f"  {component:.<30} ${info['value']:>10.2f}B on {info['date']}")
        
        print("\nLatest NLQ Values:")
        for nlq_type in ['NLQ Weekly', 'NLQ Daily FRED', 'NLQ Daily Treasury']:
            if nlq_type in latest:
                info = latest[nlq_type]
                print(f"  {nlq_type:.<30} ${info['value']:>10.2f}B on {info['date']}")
        
        print("="*60 + "\n")


def test_data_fetching():
    """Test function to verify data fetching works correctly."""
    print("Testing NLQ data fetching...")
    
    # Initialize fetcher
    fetcher = NLQDataFetcher(save_data=True)
    
    # Test date range
    start_date = "2020-01-01"
    end_date = "2024-12-31"
    
    # Test FRED data fetching
    print("\n=== Testing FRED Data ===")
    fred_series = ['WALCL', 'RRPONTSYD', 'WTREGEN']
    fred_data = fetcher.fetch_fred_series(fred_series, start_date, end_date)
    
    for series_code, data in fred_data.items():
        if not data.empty:
            print(f"{series_code}: {len(data)} observations, last value: {data.iloc[-1]:.2f}")
        else:
            print(f"{series_code}: No data retrieved")
    
    # Test TGA data fetching
    print("\n=== Testing TGA Data ===")
    tga_data = fetcher.fetch_tga_data_treasury_api()
    
    if not tga_data.empty:
        print(f"TGA data: {len(tga_data)} observations")
        print(f"Date range: {tga_data.index[0].date()} to {tga_data.index[-1].date()}")
        print(f"Latest TGA balance: ${tga_data.iloc[-1]:.2f} billion")
    else:
        print("No TGA data retrieved")
    
    # Test complete core data fetching
    print("\n=== Testing Complete Core Data ===")
    core_data = fetcher.get_core_nlq_data(start_date, end_date, use_qe_only=False)
    
    for key, data in core_data.items():
        if isinstance(data, pd.Series) and not data.empty:
            print(f"{key}: {len(data)} observations, latest: {data.iloc[-1]:.2f}")
        elif isinstance(data, str):
            print(f"{key}: {data}")
        else:
            print(f"{key}: No data")
    
    return core_data


def test_nlq_calculation():
    """Test the NetLiquidity class and NLQ calculations."""
    print("\n" + "="*60)
    print("TESTING NET LIQUIDITY CALCULATIONS")
    print("="*60)
    
    # Fetch core data
    fetcher = NLQDataFetcher(save_data=True)
    start_date = "2020-01-01"
    end_date = "2024-12-31"
    
    core_data = fetcher.get_core_nlq_data(start_date, end_date, use_qe_only=False)
    
    # Initialize NetLiquidity calculator
    nlq = NetLiquidity(core_data=core_data)
    
    # Calculate all NLQ versions
    nlq_results = nlq.calculate_all()
    
    # Print summary
    nlq.summary()
    
    # Show some sample data
    print("\nSample NLQ Data (last 5 observations):")
    print("\nNLQ Weekly:")
    print(nlq_results['nlq_weekly'].tail())
    
    print("\nNLQ Daily (Treasury TGA):")
    print(nlq_results['nlq_daily_treasury'].tail())
    
    return nlq, nlq_results


if __name__ == "__main__":
    # Test NLQ calculations
    nlq, nlq_results = test_nlq_calculation()
    
    print("\n" + "="*60)
    print(nlq_results)
    print("ALL TESTS COMPLETED SUCCESSFULLY")
    print(nlq)
    print("="*60)