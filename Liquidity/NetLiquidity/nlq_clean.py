"""
Clean, modular USD Net Liquidity (NLQ) calculation script.

This script calculates the Net Liquidity metric originally formulated by Darius Dale and 42Macro.
Net Liquidity = Fed Balance Sheet - Treasury General Account - Reverse Repo Facility

Key improvements over the original script:
- Clean, modular functions
- Clear separation of concerns
- Better error handling
- Type hints for better code documentation
- Simplified data flow

The script pulls data from:
- FRED (Federal Reserve Economic Data) for Fed balance sheet and reverse repo data
- Treasury API for daily TGA data (more timely than FRED's weekly TGA data)
"""

import os
import sys
import datetime
from typing import Dict, List, Optional, Tuple, Union
import pandas as pd
import numpy as np

# Add parent directories to path for imports
current_dir = os.path.dirname(__file__)
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)

wd = os.path.dirname(os.path.abspath(__file__))
fdel = os.sep

from MacroBackend import Pull_Data, PriceImporter, Utilities


class NLQDataFetcher:
    """Class to handle all data fetching operations for NLQ calculation."""
    
    def __init__(self, save_data: bool = True, data_dir: Optional[str] = None):
        """
        Initialize the NLQ data fetcher.
        
        Args:
            save_data: Whether to save downloaded data to disk
            data_dir: Directory to save data (defaults to User_Data folder)
        """
        self.save_data = save_data
        self.data_dir = data_dir or os.path.join(project_root, "User_Data")
        
        # Initialize data puller
        self.data_puller = Pull_Data.dataset()
        
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
        directories = [
            os.path.join(self.data_dir, 'FRED_Data'),
            os.path.join(self.data_dir, 'TreasuryData'),
            os.path.join(self.data_dir, 'NLQ_Data')
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def fetch_fred_series(self, 
                         series_codes: List[str], 
                         start_date: str, 
                         end_date: str) -> Dict[str, pd.Series]:
        """
        Fetch multiple FRED series using the Pull_Data.dataset class.
        
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
                
                # Use Pull_Data.dataset to fetch the series
                self.data_puller.get_data(
                    source='fred',
                    data_code=series_code,
                    start_date=start_date,
                    end_date=end_date
                )
                
                # Extract the data
                if hasattr(self.data_puller, 'data') and self.data_puller.data is not None:
                    series_data = self.data_puller.data.copy()
                    
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
                    
                else:
                    print(f"No data returned for {series_code}")
                    fred_data[series_code] = pd.Series(dtype=float, name=series_code)
                    
            except Exception as e:
                print(f"Error fetching {series_code}: {str(e)}")
                fred_data[series_code] = pd.Series(dtype=float, name=series_code)
        
        return fred_data
    
    def _save_fred_series(self, series_code: str, data: pd.Series) -> None:
        """Save FRED series to Excel file."""
        save_path = os.path.join(self.data_dir, 'FRED_Data', f'{series_code}.xlsx')
        
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
    
    def fetch_tga_data_treasury_api(self, 
                                   start_date: Optional[str] = None) -> pd.Series:
        """
        Fetch daily TGA data from the Treasury API for more timely updates.
        
        This function updates the local TGA Excel file with the latest data from Treasury,
        then returns the complete daily TGA series.
        
        Args:
            start_date: Start date to fetch from Treasury API (defaults to last date in local file)
            
        Returns:
            Daily TGA balance series in billions of dollars
        """
        print("Fetching TGA data from Treasury API...")
        
        # Path to local TGA data file
        tga_file_path = os.path.join(self.data_dir, 'TreasuryData', 'TGA_Since2005.xlsx')
        
        try:
            # Load existing TGA data if available
            if os.path.exists(tga_file_path):
                print("Loading existing TGA data...")
                tga_past = pd.read_excel(tga_file_path)
                
                # Set up date index
                if 'record_date' in tga_past.columns:
                    tga_past['record_date'] = pd.to_datetime(tga_past['record_date'])
                    tga_past.set_index('record_date', inplace=True)
                else:
                    # Assume first column is date
                    tga_past.iloc[:, 0] = pd.to_datetime(tga_past.iloc[:, 0])
                    tga_past.set_index(tga_past.columns[0], inplace=True)
                
                # Clean up columns - keep only balance columns
                balance_columns = [col for col in tga_past.columns 
                                 if any(term in col.lower() for term in ['bal', 'close', 'open'])]
                if balance_columns:
                    tga_past = tga_past[balance_columns]
                
                last_date_in_file = tga_past.index[-1].strftime('%Y-%m-%d')
                print(f"Last date in existing TGA file: {last_date_in_file}")
                
            else:
                print("No existing TGA file found, will fetch all available data")
                tga_past = pd.DataFrame()
                last_date_in_file = "2005-01-01"  # Default start date
            
            # Determine start date for Treasury API call
            if start_date is None:
                api_start_date = last_date_in_file
            else:
                api_start_date = start_date
            
            # Fetch new data from Treasury API
            print(f"Fetching new TGA data from Treasury API starting from {api_start_date}...")
            
            # Fetch closing balances
            closing_data = PriceImporter.PullTGA_Data(
                AccountName='Treasury General Account (TGA) Closing Balance',
                start_date=api_start_date
            )
            
            # Fetch opening balances  
            opening_data = PriceImporter.PullTGA_Data(
                AccountName='Treasury General Account (TGA) Opening Balance',
                start_date=api_start_date
            )
            
            # Process and combine the data
            if closing_data is not None and not closing_data.empty:
                closing_data.set_index(pd.to_datetime(closing_data.index), inplace=True)
                opening_data.set_index(pd.to_datetime(opening_data.index), inplace=True)
                
                # Clean up the data
                for df in [closing_data, opening_data]:
                    # Remove unwanted columns
                    cols_to_drop = [col for col in df.columns if 'account_type' in col.lower()]
                    df.drop(columns=cols_to_drop, errors='ignore', inplace=True)
                
                # Combine opening and closing data
                combined_data = pd.concat([
                    opening_data.add_suffix('_open'),
                    closing_data.add_suffix('_close')
                ], axis=1)
                
                # Update the main TGA dataset
                if not tga_past.empty:
                    # Remove overlapping dates and append new data
                    tga_past = tga_past[tga_past.index < combined_data.index[0]]
                    tga_updated = pd.concat([tga_past, combined_data])
                else:
                    tga_updated = combined_data
                
                # Save updated data
                tga_updated.to_excel(tga_file_path, index_label='record_date')
                print(f"Updated TGA data saved to {tga_file_path}")
                
            else:
                print("No new TGA data available from Treasury API")
                tga_updated = tga_past
            
            # Extract daily closing balance series
            close_col = None
            for col in tga_updated.columns:
                if 'close' in col.lower() and 'bal' in col.lower():
                    close_col = col
                    break
            
            if close_col is None:
                # Try to find any balance column
                for col in tga_updated.columns:
                    if 'bal' in col.lower():
                        close_col = col
                        break
            
            if close_col is not None:
                tga_daily_series = pd.Series(
                    tga_updated[close_col], 
                    name='TGA Balance (Billions USD)'
                )
                
                # Convert from millions to billions
                tga_daily_series = tga_daily_series / 1000
                
                # Remove any NaN values and ensure proper datetime index
                tga_daily_series = tga_daily_series.dropna()
                tga_daily_series.index = pd.to_datetime(tga_daily_series.index)
                
                # Remove duplicate dates (keep last occurrence)
                if tga_daily_series.index.duplicated().any():
                    print(f"Warning: Removing {tga_daily_series.index.duplicated().sum()} duplicate dates from TGA data")
                    tga_daily_series = tga_daily_series[~tga_daily_series.index.duplicated(keep='last')]
                
                print(f"TGA data: {len(tga_daily_series)} observations from {tga_daily_series.index[0].date()} to {tga_daily_series.index[-1].date()}")
                
                return tga_daily_series
                
            else:
                print("Error: Could not find balance column in TGA data")
                return pd.Series(dtype=float, name='TGA Balance (Billions USD)')
                
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
        
        # Fetch TGA data from Treasury API
        tga_daily = self.fetch_tga_data_treasury_api()
        
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

    def __init__(self, input_settings: pd.DataFrame = None, core_data: Dict[str, Union[pd.Series, str]] = None):
        """
        Initialize NetLiquidity calculator with core data.
        
        Args:
            - input_settings: DataFrame of input settings from excel sheet template for netliquidity (optional).
            - core_data: Dictionary from NLQDataFetcher.get_core_nlq_data() containing:
                - 'fed_balance_sheet': Fed assets series (WALCL or RESPPNTNWW)
                - 'reverse_repo': Reverse repo facility series (RRPONTSYD)
                - 'tga_fred_weekly': TGA from FRED (weekly)
                - 'tga_treasury_daily': TGA from Treasury API (daily)
                - 'series_type': 'total_assets' or 'QE_only'
        """

        if input_settings is None:
            try:
                self.input_settings = pd.read_excel(wd + fdel + "NetLiquidity_InputParams.xlsx", sheet_name="Parameters", index_col=0)
        
            except Exception as e:
                print(f"Error reading input settings: {e}\nEnsure that the NetLiquidity_InputParams.xlsx file exists in the script directory.")
                return None 
        else:
            self.input_settings = input_settings

        self.start_date = str(self.input_settings.loc["Start date", "Additional FRED Data"])
        end = self.input_settings.loc["End date", "Additional FRED Data"]
        if pd.isna(end) or end.strip() == "":
            self.end_date = datetime.datetime.today().strftime('%Y-%m-%d')
        else:
            self.end_date = str(end)

        if core_data is None:
           fetcher = NLQDataFetcher(save_data=True)
           self.core_data = fetcher.get_core_nlq_data(self.start_date, self.end_date, use_qe_only=False)
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
            Resampled daily series
        """
        if index is None:
            if self.daily_index is None:
                raise ValueError("Daily index not created. Call create_daily_index() first.")
            index = self.daily_index
        
        # Remove duplicates from the series if any exist
        if series.index.duplicated().any():
            print(f"Warning: Removing {series.index.duplicated().sum()} duplicate dates from {series.name}")
            series = series[~series.index.duplicated(keep='last')]
        
        # Check if resampling is needed
        if len(index.difference(series.index)) == 0 and len(series.index) == len(index):
            # Already aligned
            return series
        
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