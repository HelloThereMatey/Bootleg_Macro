"""
Global M2 Data Handler Module
==============================
A modular and efficient system for downloading and managing M2 money supply data
and FX exchange rates for multiple countries.

Author: Refactored for efficiency
Date: February 2026
"""

import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path

# Setup paths
fdel = os.path.sep
wd = os.path.dirname(__file__)
grampa = os.path.dirname(wd)
grampa = os.path.dirname(grampa)
sys.path.append(grampa)

from MacroBackend import tvDatafeedz


## Standalone functions #################
def identify_outliers(series: pd.Series, method: str = 'iqr', threshold: float = 3.0, 
                     z_score_threshold: float = 3.0, iqr_multiplier: float = 1.5,
                     pct_change_threshold: float = None):
    """
    Identify outliers in a time series using various methods.
    
    Parameters:
    -----------
    series : pd.Series
        The time series data to analyze
    method : str
        Method to use: 'iqr' (Interquartile Range), 'zscore', 'pct_change', or 'magnitude'
    threshold : float
        General threshold for magnitude-based detection (e.g., detect values > 10^14)
    z_score_threshold : float
        Number of standard deviations for z-score method (default: 3.0)
    iqr_multiplier : float
        Multiplier for IQR method (default: 1.5)
    pct_change_threshold : float
        Percentage change threshold (e.g., 100 for 100% change)
    
    Returns:
    --------
    dict with keys:
        'outlier_indices': list of index positions
        'outlier_dates': list of dates
        'outlier_values': list of values
        'method_used': string describing method
    """
    
    # Ensure we're working with a Series
    if isinstance(series, pd.DataFrame):
        series = series.iloc[:, 0]
    
    # Drop any NaN values for calculation
    series_clean = series.dropna()
    
    outlier_info = {
        'outlier_indices': [],
        'outlier_dates': [],
        'outlier_values': [],
        'method_used': method
    }
    
    if method == 'iqr':
        # Interquartile Range method
        Q1 = series_clean.quantile(0.25)
        Q3 = series_clean.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - iqr_multiplier * IQR
        upper_bound = Q3 + iqr_multiplier * IQR
        
        outliers = (series < lower_bound) | (series > upper_bound)
        
    elif method == 'zscore':
        # Z-score method
        mean = series_clean.mean()
        std = series_clean.std()
        
        # Check for zero standard deviation
        if std == 0 or np.isnan(std):
            print(f"    ⚠ Warning: Standard deviation is {std}, cannot compute z-scores")
            outliers = pd.Series(False, index=series.index)
        else:
            z_scores = np.abs((series - mean) / std)
            outliers = z_scores > z_score_threshold
        
    elif method == 'pct_change':
        # Percentage change method
        if pct_change_threshold is None:
            raise ValueError("pct_change_threshold must be specified for 'pct_change' method")
        
        pct_changes = series.pct_change().abs() * 100
        outliers = pct_changes > pct_change_threshold
        
    elif method == 'magnitude':
        # Absolute magnitude threshold (useful for your Iraq case)
        outliers = series > threshold
        
    else:
        raise ValueError(f"Unknown method: {method}. Use 'iqr', 'zscore', 'pct_change', or 'magnitude'")
    
    # Extract outlier information
    outlier_mask = outliers.fillna(False)
    outlier_info['outlier_indices'] = list(series[outlier_mask].index)
    outlier_info['outlier_dates'] = [str(date) for date in series[outlier_mask].index]
    # Convert numpy array to Python list
    outlier_info['outlier_values'] = series[outlier_mask].values.tolist()
    
    # Print summary
    print(f"\nOutlier Detection Summary ({method} method):")
    print(f"Total data points: {len(series)}")
    print(f"Outliers found: {len(outlier_info['outlier_indices'])}")
    
    if len(outlier_info['outlier_indices']) > 0:
        print("\nOutlier details:")
        for date, value in zip(outlier_info['outlier_dates'], outlier_info['outlier_values']):
            # Handle both scalar values and potential list values
            if isinstance(value, (list, tuple)):
                value = value[0] if len(value) > 0 else 0.0
            print(f"  Date: {date}, Value: {float(value):.2e}")
    
    return outlier_info     

################## Class Definition ##################
class Global_M2:
    """
    A class to handle downloading, processing, and storing Global M2 data
    for multiple countries.
    
    Attributes:
    -----------
    config_path : str
        Path to the Excel file containing country M2 and FX ticker information
    country_list : pd.DataFrame
        DataFrame with country information indexed by country name
    data_dict : dict
        Dictionary storing M2 and FX DataFrames for each country
    tv : tvDatafeedz.TvDatafeed
        TradingView data feed object for pulling data
    """
    
    def __init__(self, config_file='M2Info_Top50.xlsx', config_folder='UpdateM2Infos'):
        """
        Initialize the Global_M2 object.
        
        Parameters:
        -----------
        config_file : str
            Name of the Excel file containing country M2/FX information
        config_folder : str
            Folder name containing the config file
        """
        self.wd = Path(__file__).parent
        self.config_path = self.wd / config_folder / config_file
        self.country_list = None
        self.data_dict = {}
        self.tv = None
        self.failed_downloads = []
        
        # Aggregate definitions
        self.aggregates = {
            'Top50': None,
            'Top33': None,
            'Long28': None,
            'Long27': None,
            'Top8': None
        }
        self.aggregate_series = {}
        
        # Load the country list configuration
        self._load_country_list()
        
    def _load_country_list(self):
        """
        Load the country list from Excel file.
        The file should have countries as index and columns for:
        - M2_Symbol
        - M2_exchange
        - FX_Symbol
        - FX_Exchange
        - M2_currency_code
        """
        try:
            self.country_list = pd.read_excel(self.config_path, index_col=0)
            print(f"Successfully loaded country list with {len(self.country_list)} countries")
            print(f"Countries: {list(self.country_list.index)}")
        except FileNotFoundError:
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        except Exception as e:
            raise Exception(f"Error loading country list: {str(e)}")
    
    def download_data(self, n_bars=500, countries=None):
        """
        Download M2 and FX data for specified countries.
        
        Parameters:
        -----------
        n_bars : int
            Number of monthly bars to download (default: 500)
        countries : list or None
            List of specific countries to download. If None, downloads all countries.
            
        Returns:
        --------
        dict
            Dictionary with country names as keys and DataFrames as values
        """
        # Initialize TradingView datafeed
        self.tv = tvDatafeedz.TvDatafeed()
        
        # Determine which countries to process
        if countries is None:
            countries_to_process = self.country_list.index.tolist()
        else:
            countries_to_process = countries
        
        print(f"\nStarting download for {len(countries_to_process)} countries...")
        print("=" * 70)
        
        # Reset data_dict and failed_downloads
        self.data_dict = {}
        self.failed_downloads = []
        
        for i, country in enumerate(countries_to_process):
            print(f"\n[{i+1}/{len(countries_to_process)}] Processing: {country}")
            
            try:
                # Get country configuration
                country_info = self.country_list.loc[country]
                
                m2_symbol = country_info['M2_Symbol']
                m2_exchange = country_info['M2_exchange']
                fx_symbol = country_info['FX_Symbol']
                fx_exchange = country_info['FX_Exchange']
                currency_code = country_info['M2_currency_code']
                
                print(f"  M2: {m2_symbol} @ {m2_exchange}")
                print(f"  FX: {fx_symbol} @ {fx_exchange}")
                print(f"  Currency: {currency_code}")
                
                # Download M2 data
                m2_data = self._download_m2_data(m2_symbol, m2_exchange, n_bars)
                
                if m2_data is None:
                    self.failed_downloads.append(f"{country}_M2")
                    continue
                
                # Download FX data (skip if USD)
                if currency_code == 'USD':
                    print(f"  Skipping FX download (already in USD)")
                    fx_data = None
                else:
                    fx_data = self._download_fx_data(fx_symbol, fx_exchange, n_bars, country)
                
                # Process and combine data
                combined_df = self._process_country_data(
                    country, m2_data, fx_data, currency_code, fx_symbol
                )
                
                if combined_df is not None:
                    self.data_dict[country] = combined_df
                    print(f"  ✓ Successfully processed {country}")
                    print(f"  Data range: {combined_df.index[0]} to {combined_df.index[-1]}")
                    print(f"  Rows: {len(combined_df)}")
                    
            except Exception as e:
                print(f"  ✗ Error processing {country}: {str(e)}")
                self.failed_downloads.append(country)
                continue
        
        # Summary
        print("\n" + "=" * 70)
        print(f"\nDownload Summary:")
        print(f"  Successfully downloaded: {len(self.data_dict)} countries")
        print(f"  Failed downloads: {len(self.failed_downloads)}")
        
        if self.failed_downloads:
            print(f"\n  Failed: {self.failed_downloads}")
        
        return self.data_dict
    
    def _download_m2_data(self, symbol, exchange, n_bars):
        """Download M2 data from TradingView."""
        try:
            m2_data = self.tv.multi_attempt_pull(
                symbol=symbol,
                exchange=exchange,
                interval=tvDatafeedz.Interval.in_monthly,
                n_bars=n_bars
            )
            return m2_data
        except Exception as e:
            print(f"    ✗ Failed to download M2 data: {str(e)}")
            return None
    
    def _download_fx_data(self, symbol, exchange, n_bars, country):
        """Download FX data from TradingView."""
        try:
            fx_data = self.tv.multi_attempt_pull(
                symbol=symbol,
                exchange=exchange,
                interval=tvDatafeedz.Interval.in_monthly,
                n_bars=n_bars
            )
            return fx_data
        except Exception as e:
            print(f"    ✗ Failed to download FX data: {str(e)}")
            self.failed_downloads.append(f"{country}_FX")
            return None
    
    def _process_country_data(self, country, m2_data, fx_data, currency_code, fx_symbol):
        """
        Process and combine M2 and FX data for a country.
        
        Parameters:
        -----------
        country : str
            Country name
        m2_data : pd.DataFrame
            M2 data from TradingView
        fx_data : pd.DataFrame or None
            FX data from TradingView (None if USD)
        currency_code : str
            Currency code (e.g., 'EUR', 'JPY', 'USD')
        fx_symbol : str
            FX symbol (e.g., 'EURUSD', 'USDJPY')
            
        Returns:
        --------
        pd.DataFrame
            Combined DataFrame with M2 in local currency and USD
        """
        # Convert M2 data index to datetime
        m2_df = pd.DataFrame(m2_data)
        m2_df.index = pd.DatetimeIndex(m2_df.index).to_period('M').to_timestamp()
        
        # Extract M2 close prices
        m2_close = m2_df['close'].copy()
        m2_close.name = f'{country}_M2_{currency_code}'
        
        # Handle FX data
        if currency_code == 'USD':
            # No conversion needed
            fx_close = pd.Series(1.0, index=m2_close.index, name=f'{country}_FX_USD')
            m2_usd = m2_close.copy()
            m2_usd.name = f'{country}_M2_USD'
        else:
            # Process FX data
            if fx_data is None:
                print(f"    ⚠ Missing FX data, cannot convert to USD")
                return None
            
            fx_df = pd.DataFrame(fx_data)
            fx_df.index = pd.DatetimeIndex(fx_df.index).to_period('M').to_timestamp()
            
            # Resample FX to monthly mean (in case of higher frequency data)
            fx_monthly = fx_df['close'].resample('MS').mean()
            
            # Align FX data with M2 data
            fx_close = fx_monthly.reindex(m2_close.index)
            fx_close = fx_close.fillna(method='ffill')  # Forward fill missing values
            fx_close.name = f'{country}_FX_Rate'
            
            # Determine if we need to invert the FX rate
            # Convention: we want rate that converts local currency to USD
            if fx_symbol.startswith('USD'):
                # Format: USDXXX (e.g., USDJPY) - already gives USD per local currency
                # To convert to local currency per USD, we invert
                fx_conversion = 1 / fx_close
            elif fx_symbol.endswith('USD'):
                # Format: XXXUSD (e.g., EURUSD) - gives USD per local currency
                # This is what we want
                fx_conversion = fx_close
            else:
                print(f"    ⚠ Unexpected FX symbol format: {fx_symbol}")
                fx_conversion = fx_close
            
            # Calculate M2 in USD
            m2_usd = m2_close * fx_conversion
            m2_usd.name = f'{country}_M2_USD'
        
        # Combine into single DataFrame
        result_df = pd.concat([m2_close, fx_close, m2_usd], axis=1)
        result_df = result_df.sort_index()
        
        return result_df
    
    def save_to_hdf5(self, filename='global_m2_data.hd5', path=None):
        """
        Save the data dictionary to an HDF5 file.
        
        Parameters:
        -----------
        filename : str
            Name of the HDF5 file
        path : str or None
            Directory path to save the file. If None, saves in working directory.
            
        Returns:
        --------
        str
            Full path to the saved file
        """
        if not self.data_dict:
            print("No data to save. Run download_data() first.")
            return None
        
        # Determine save path
        if path is None:
            save_path = self.wd / filename
        else:
            save_path = Path(path) / filename
        
        print(f"\nSaving data to HDF5 file: {save_path}")
        
        try:
            # Save each country's DataFrame to the HDF5 file
            with pd.HDFStore(save_path, mode='w') as store:
                for country, df in self.data_dict.items():
                    # Clean country name for use as HDF key (replace spaces/special chars)
                    key = country.replace(' ', '_').replace('-', '_')
                    store.put(key, df, format='table')
                    print(f"  Saved: {country} -> /{key}")
                
                # Also save metadata
                metadata = pd.DataFrame({
                    'country': list(self.data_dict.keys()),
                    'rows': [len(df) for df in self.data_dict.values()],
                    'start_date': [df.index[0] for df in self.data_dict.values()],
                    'end_date': [df.index[-1] for df in self.data_dict.values()],
                })
                store.put('metadata', metadata, format='table')
                print(f"  Saved: metadata")
            
            print(f"\n✓ Successfully saved {len(self.data_dict)} countries to {save_path}")
            return str(save_path)
            
        except Exception as e:
            print(f"✗ Error saving to HDF5: {str(e)}")
            return None
    
    def load_from_hdf5(self, filename='global_m2_data.hd5', path=None):
        """
        Load data from an HDF5 file.
        
        Parameters:
        -----------
        filename : str
            Name of the HDF5 file
        path : str or None
            Directory path to load from. If None, loads from working directory.
            
        Returns:
        --------
        dict
            Dictionary with country DataFrames
        """
        # Determine load path
        if path is None:
            load_path = self.wd / filename
        else:
            load_path = Path(path) / filename
        
        if not load_path.exists():
            print(f"File not found: {load_path}")
            return None
        
        print(f"\nLoading data from HDF5 file: {load_path}")
        
        try:
            self.data_dict = {}
            
            # Open store once and get all keys
            with pd.HDFStore(load_path, mode='r') as store:
                keys = [key for key in store.keys() if key != '/metadata']
                
                # Load all DataFrames at once
                for key in keys:
                    country = key.lstrip('/').replace('_', ' ')
                    df = pd.read_hdf(load_path, key=key)
                    
                    # Rebuild the DataFrame with a fresh DatetimeIndex
                    # This avoids pandas/numpy compatibility issues
                    new_index = pd.DatetimeIndex(df.index.values)
                    df_new = pd.DataFrame(df.values, index=new_index, columns=df.columns)
                    
                    self.data_dict[country] = df_new
                    print(f"  Loaded: {country}")
            
            print(f"\n✓ Successfully loaded {len(self.data_dict)} countries")
            return self.data_dict
            
        except Exception as e:
            print(f"✗ Error loading from HDF5: {str(e)}")
            return None
    
    def get_country_data(self, country):
        """
        Get data for a specific country.
        
        Parameters:
        -----------
        country : str
            Country name
            
        Returns:
        --------
        pd.DataFrame or None
            DataFrame for the specified country
        """
        return self.data_dict.get(country, None)
    
    def load_aggregate_definitions(self, config_folder='UpdateM2Infos'):
        """
        Load country lists for each aggregate from Excel files.
        
        Parameters:
        -----------
        config_folder : str
            Folder containing the aggregate definition files
            
        Returns:
        --------
        dict
            Dictionary with aggregate names and their country lists
        """
        aggregate_files = {
            'Top50': 'M2Info_Top50.xlsx',
            'Top33': 'M2Info_Top33.xlsx',
            'Long28': 'M2Info_Long28.xlsx',
            'Long27': 'M2Info_Long27.xlsx',
            'Top8': 'M2Info_Top8.xlsx'
        }
        
        print(f"\nLoading aggregate definitions from {config_folder}...")
        
        for agg_name, filename in aggregate_files.items():
            file_path = self.wd / config_folder / filename
            try:
                df = pd.read_excel(file_path, index_col=0)
                self.aggregates[agg_name] = list(df.index)
                print(f"  {agg_name}: {len(self.aggregates[agg_name])} countries")
            except FileNotFoundError:
                print(f"  ⚠ Warning: {filename} not found, skipping {agg_name}")
                self.aggregates[agg_name] = []
            except Exception as e:
                print(f"  ✗ Error loading {agg_name}: {str(e)}")
                self.aggregates[agg_name] = []
        
        print(f"✓ Loaded {len([a for a in self.aggregates.values() if a])} aggregate definitions")
        return self.aggregates
    
    def create_aggregate(self, countries, name='Custom', use_ffill=True):
        """
        Create an aggregated Global M2 series from a list of countries.
        
        Parameters:
        -----------
        countries : list
            List of country names to include in aggregate
        name : str
            Name for this aggregate
        use_ffill : bool
            Whether to forward-fill missing values at end of series
            
        Returns:
        --------
        tuple
            (aggregate_series, aggregate_series_ffill) if use_ffill=True
            aggregate_series if use_ffill=False
        """
        if not self.data_dict:
            print("No data loaded. Run download_data() or load_from_hdf5() first.")
            return None
        
        # Find countries that are available in data_dict
        available_countries = [c for c in countries if c in self.data_dict]
        missing_countries = [c for c in countries if c not in self.data_dict]
        
        if missing_countries:
            print(f"\n⚠ Warning: {len(missing_countries)} countries not in data: {missing_countries}")
        
        if not available_countries:
            print("✗ No countries available for aggregation")
            return None
        
        print(f"\nCreating '{name}' aggregate from {len(available_countries)} countries...")
        
        # Collect all M2_USD series
        country_series = {}
        date_ranges = []
        
        for country in available_countries:
            df = self.data_dict[country]
            m2_usd_col = df.columns[-1]  # Last column is M2_USD
            series = df[m2_usd_col].copy()
            
            # Ensure it's a Series
            if isinstance(series, pd.DataFrame):
                series = series.iloc[:, 0]
            
            country_series[country] = series
            date_ranges.append((series.index[0], series.index[-1]))
        
        # Find the common date range (intersection)
        earliest_start = max([dr[0] for dr in date_ranges])
        latest_end = min([dr[1] for dr in date_ranges])
        
        print(f"  Date range: {earliest_start} to {latest_end}")
        
        # Create a common index
        # Get all unique dates from all series
        all_dates = set()
        for series in country_series.values():
            all_dates.update(series.index)
        
        # Sort and create DatetimeIndex
        common_index = pd.DatetimeIndex(sorted(all_dates))
        common_index = common_index[(common_index >= earliest_start) & (common_index <= latest_end)]
        
        # Create the aggregate series
        aggregate = pd.Series(0.0, index=common_index, name=f'{name}_M2_USD')
        
        # Sum up each country's contribution
        for country, series in country_series.items():
            # Reindex to common index
            series_aligned = series.reindex(common_index)
            # Add to aggregate (NaN values don't contribute)
            aggregate = aggregate.add(series_aligned, fill_value=0)
        
        print(f"  ✓ Aggregate created: {len(aggregate)} data points")
        print(f"  Total M2 (latest): ${aggregate.iloc[-1]:.2e}")
        
        if use_ffill:
            # Create forward-filled version for handling missing recent data
            aggregate_ffill = pd.Series(0.0, index=common_index, name=f'{name}_M2_USD_ffill')
            
            for country, series in country_series.items():
                # Reindex and forward fill
                series_aligned = series.reindex(common_index)
                series_filled = series_aligned.fillna(method='ffill')
                # Add to aggregate
                aggregate_ffill = aggregate_ffill.add(series_filled, fill_value=0)
            
            print(f"  Total M2 (ffill, latest): ${aggregate_ffill.iloc[-1]:.2e}")
            
            return aggregate, aggregate_ffill
        else:
            return aggregate
    
    def create_all_aggregates(self, use_ffill=True):
        """
        Create all predefined aggregate series.
        
        Parameters:
        -----------
        use_ffill : bool
            Whether to create forward-filled versions
            
        Returns:
        --------
        dict
            Dictionary with aggregate names and their series
        """
        if not self.aggregates or not any(self.aggregates.values()):
            print("No aggregate definitions loaded. Run load_aggregate_definitions() first.")
            return None
        
        print(f"\n{'='*70}")
        print("Creating Global M2 Aggregates")
        print(f"{'='*70}")
        
        self.aggregate_series = {}
        
        for agg_name, countries in self.aggregates.items():
            if not countries:
                print(f"\n⚠ Skipping {agg_name}: no countries defined")
                continue
            
            result = self.create_aggregate(countries, name=agg_name, use_ffill=use_ffill)
            
            if result:
                if use_ffill:
                    self.aggregate_series[agg_name] = result[0]
                    self.aggregate_series[f'{agg_name}_ffill'] = result[1]
                else:
                    self.aggregate_series[agg_name] = result
        
        print(f"\n{'='*70}")
        print(f"✓ Created {len([k for k in self.aggregate_series.keys() if not k.endswith('_ffill')])} aggregates")
        print(f"{'='*70}\n")
        
        return self.aggregate_series
    
    def save_aggregates(self, path=None, format='both'):
        """
        Save aggregate series to files.
        
        Parameters:
        -----------
        path : str or None
            Directory to save files. If None, saves to working directory.
        format : str
            'hdf5', 'excel', or 'both'
            
        Returns:
        --------
        list
            List of saved file paths
        """
        if not self.aggregate_series:
            print("No aggregates to save. Run create_all_aggregates() first.")
            return None
        
        # Determine save path
        if path is None:
            save_dir = self.wd
        else:
            save_dir = Path(path)
        
        saved_files = []
        
        # Save to Excel
        if format in ['excel', 'both']:
            print(f"\nSaving aggregates to Excel...")
            for agg_name, series in self.aggregate_series.items():
                if not agg_name.endswith('_ffill'):
                    file_path = save_dir / f'{agg_name}_M2_USD.xlsx'
                    series.to_excel(file_path)
                    print(f"  Saved: {file_path.name}")
                    saved_files.append(str(file_path))
                    
                    # Also save ffill version if it exists
                    ffill_name = f'{agg_name}_ffill'
                    if ffill_name in self.aggregate_series:
                        file_path_ffill = save_dir / f'{agg_name}_M2_USD_ffill.xlsx'
                        self.aggregate_series[ffill_name].to_excel(file_path_ffill)
                        print(f"  Saved: {file_path_ffill.name}")
                        saved_files.append(str(file_path_ffill))
        
        # Save to HDF5
        if format in ['hdf5', 'both']:
            print(f"\nSaving aggregates to HDF5...")
            hdf_path = save_dir / 'global_m2_aggregates.h5'
            
            with pd.HDFStore(hdf_path, mode='w') as store:
                for agg_name, series in self.aggregate_series.items():
                    key = agg_name.replace(' ', '_').replace('-', '_')
                    store.put(key, series, format='table')
                    print(f"  Saved: /{key}")
            
            saved_files.append(str(hdf_path))
            print(f"✓ Saved to {hdf_path}")
        
        return saved_files
    
    def clean_outliers(self, method='iqr', threshold=3.0, z_score_threshold=3.0, 
                       iqr_multiplier=1.5, pct_change_threshold=None, 
                       interpolation_method='linear', countries=None):
        """
        Identify and correct outliers in the M2 data by replacing them with interpolated values.
        
        Parameters:
        -----------
        method : str
            Outlier detection method: 'iqr', 'zscore', 'pct_change', or 'magnitude'
        threshold : float
            Threshold for magnitude-based detection
        z_score_threshold : float
            Number of standard deviations for z-score method
        iqr_multiplier : float
            Multiplier for IQR method
        pct_change_threshold : float
            Percentage change threshold for pct_change method
        interpolation_method : str
            Pandas interpolation method ('linear', 'polynomial', 'spline', etc.)
        countries : list or None
            List of specific countries to clean. If None, cleans all countries.
            
        Returns:
        --------
        dict
            Dictionary with outlier information for each country
        """
        if not self.data_dict:
            print("No data loaded. Run download_data() or load_from_hdf5() first.")
            return None
        
        # Determine which countries to process
        if countries is None:
            countries_to_process = list(self.data_dict.keys())
        else:
            countries_to_process = countries
        
        outlier_report = {}
        
        print(f"\n{'='*70}")
        print(f"Cleaning Outliers - Method: {method}")
        print(f"{'='*70}")
        
        for country in countries_to_process:
            if country not in self.data_dict:
                print(f"\n  ⚠ {country} not found in data")
                continue
            
            print(f"\n  Processing: {country}")
            df = self.data_dict[country]
            
            # Focus on the M2_USD column (the last column)
            m2_usd_col = df.columns[-1]
            m2_series = df[m2_usd_col].copy()
            
            # Ensure we have a Series, not a DataFrame
            if isinstance(m2_series, pd.DataFrame):
                m2_series = m2_series.iloc[:, 0]
            
            # Convert to Series if needed and ensure proper dtype
            m2_series = pd.Series(m2_series.values, index=m2_series.index, name=m2_usd_col)
            
            # Identify outliers
            outlier_info = identify_outliers(
                m2_series,
                method=method,
                threshold=threshold,
                z_score_threshold=z_score_threshold,
                iqr_multiplier=iqr_multiplier,
                pct_change_threshold=pct_change_threshold
            )
            
            # Store outlier info
            outlier_report[country] = outlier_info
            
            # If outliers found, replace with NaN and interpolate
            if len(outlier_info['outlier_indices']) > 0:
                print(f"    → Replacing {len(outlier_info['outlier_indices'])} outliers with interpolated values")
                
                # Create a copy of the series
                cleaned_series = m2_series.copy()
                
                # Set outliers to NaN
                for idx in outlier_info['outlier_indices']:
                    cleaned_series.loc[idx] = np.nan
                
                # Interpolate missing values
                cleaned_series = cleaned_series.interpolate(method=interpolation_method)
                
                # If there are still NaNs at the beginning or end, use forward/backward fill
                cleaned_series = cleaned_series.fillna(method='bfill').fillna(method='ffill')
                
                # Update the DataFrame
                self.data_dict[country][m2_usd_col] = cleaned_series
                
                # Also update the M2 in local currency if needed
                if df.columns[0] != m2_usd_col:  # If not USD country
                    # Recalculate M2 local from M2 USD and FX rate
                    fx_rate = df[df.columns[1]]  # FX rate column
                    self.data_dict[country][df.columns[0]] = cleaned_series / fx_rate
                
                print(f"    ✓ Outliers cleaned and interpolated")
            else:
                print(f"    ✓ No outliers detected")
        
        print(f"\n{'='*70}")
        print(f"Outlier Cleaning Complete")
        print(f"{'='*70}\n")
        
        return outlier_report
    
    def summary(self):
        """Print a summary of the loaded data."""
        if not self.data_dict:
            print("No data loaded.")
            return
        
        print("\n" + "=" * 70)
        print("Global M2 Data Summary")
        print("=" * 70)
        print(f"Total countries: {len(self.data_dict)}")
        print("\nCountry details:")
        
        for country, df in self.data_dict.items():
            print(f"\n  {country}:")
            print(f"    Columns: {list(df.columns)}")
            print(f"    Date range: {df.index[0]} to {df.index[-1]}")
            print(f"    Rows: {len(df)}")
            # Use .iloc[-1, -1] to get the scalar value directly
            latest_m2_usd = df.iloc[-1, -1]
            print(f"    Latest M2 (USD): {latest_m2_usd:.2e}")


# Example usage
if __name__ == "__main__":
    # Initialize the Global M2 handler
    gm2 = Global_M2()
    print(gm2.country_list)
    # Download data for all countries (or specify a subset)
    # gm2.download_data(countries=['United States', 'China', 'Japan'])
    gm2.download_data()
    
    # Save to HDF5
    #gm2.save_to_hdf5()
    #gm2.load_from_hdf5()
    outlier_report = gm2.clean_outliers(method='zscore', z_score_threshold=4.0)

    # Print outlier report  
    print("\nOutlier Report Summary:")
    print(outlier_report)

    for country, report in outlier_report.items():
        if len(report['outlier_dates']) > 0:
            print(f"\nOutliers for {country}:\n{report['outlier_dates']}: {report['outlier_values']}")
    gm2.save_to_hdf5()

    # Print summary
    #gm2.summary()
