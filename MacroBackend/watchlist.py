import os
import sys
import time
import threading
from typing import Union
import pandas as pd
import numpy as np
import re
import base64
import gc

# Path helpers (used by defaults in the class)
wd = os.path.dirname(__file__)
parent = os.path.dirname(wd)
grampa = os.path.dirname(parent)
fdel = os.path.sep
sys.path.append(parent)

# Internal module imports
from MacroBackend import Utilities, Pull_Data, charting_plotly

from PyQt6 import QtWidgets
import pydantic
from pydantic import BaseModel, Field
import datetime
from typing import Optional, Any, Mapping, ClassVar

###### Standalone functions ##################

def drop_duplicate_columns(df):
    # Identify columns with a dot followed by a numeric character
    regex = re.compile(r'\.\d+')
    columns_to_drop = [str(col) for col in df.columns if regex.search(str(col))]
    
    # Drop the identified columns
    df = df.drop(columns=columns_to_drop)
    
    return df, columns_to_drop
    
def close_open_stores(target_path: str) -> None:
    """Find and close any open HDFStore objects pointing to target_path"""
    # Force garbage collection to ensure we catch everything
    unreached = gc.collect()
    print(f"Garbage collection: {unreached} objects unreachable.")

    for obj in gc.get_objects():
        if isinstance(obj, pd.HDFStore):
            if obj._path == target_path and obj.is_open:
                print(f"Closing open store: {obj._path}")
                obj.close()
                time.sleep(1)

def qt_load_file_dialog(dialog_title: str = "Choose a file", initial_dir: str = wd, 
                        file_types: str = "All Files (*);;Text Files (*.txt);;Excel Files (*.xlsx)"):
    app = QtWidgets.QApplication.instance()  # Check if an instance already exists
    if not app:  # If not, create a new instance
        app = QtWidgets.QApplication(sys.argv)

    file_path, _ = QtWidgets.QFileDialog.getOpenFileName(None, dialog_title, initial_dir, file_types, options=QtWidgets.QFileDialog.Option.DontUseNativeDialog)

    return file_path

def sanitize_hdf_key(key: str) -> str:
    """
    Sanitize a key to be valid for HDF5 storage by replacing invalid characters
    with underscores and ensuring it starts with a letter or underscore.
    """
    import re
    # Replace any non-alphanumeric characters (except underscores) with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', str(key))
    
    # Ensure it starts with a letter or underscore
    if sanitized and not sanitized[0].isalpha() and sanitized[0] != '_':
        sanitized = '_' + sanitized
    
    # Remove multiple consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    
    return sanitized

def strip_timezone_from_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Strip timezone information from all datetime columns in a DataFrame to make it Excel-compatible.
    """
    df_copy = df.copy()
    
    for col in df_copy.columns:
        # Check each column for datetime objects
        for idx in df_copy.index:
            val = df_copy.loc[idx, col]
            if isinstance(val, pd.Timestamp) and val.tz is not None:
                # Convert timezone-aware timestamp to timezone-naive
                df_copy.loc[idx, col] = val.tz_convert('UTC').tz_localize(None)
            elif hasattr(val, 'tzinfo') and val.tzinfo is not None:
                # Handle other datetime objects with timezone info
                if hasattr(val, 'astimezone'):
                    # Convert to UTC then remove timezone
                    df_copy.loc[idx, col] = val.astimezone(datetime.timezone.utc).replace(tzinfo=None)
                else:
                    # Fallback: just remove timezone info
                    df_copy.loc[idx, col] = val.replace(tzinfo=None)
    
    return df_copy

############ Pydantic Common Metadata Model ################

# Comprehensive frequency mapping dictionary
FREQUENCY_MAPPING = {
    # Daily frequencies
    'D': ['daily', 'day', 'days', 'd', '1d', '24h', '1day'],
    
    # Weekly frequencies  
    'W': ['weekly', 'week', 'weeks', 'w', '1w', '7d', '1week', 'wk'],
    
    # Monthly frequencies
    'M': ['monthly', 'month', 'months', 'm', '1m', '1month', 'mo'],
    'MS': ['month start', 'monthly start', 'ms', 'month_start'],
    
    # Quarterly frequencies
    'Q': ['quarterly', 'quarter', 'quarters', 'q', '1q', '3m', '1quarter'],
    'QS': ['quarter start', 'quarterly start', 'qs', 'quarter_start'],
    
    # Annual frequencies
    'A': ['annual', 'annually', 'year', 'yearly', 'years', 'a', 'y', '1y', '1year', '12m'],
    'AS': ['annual start', 'year start', 'as', 'yas', 'annual_start'],
    
    # Business frequencies
    'B': ['business', 'business day', 'business days', 'b', 'bd', 'bday'],
    'BM': ['business month', 'business monthly', 'bm', 'business_month'],
    'BQ': ['business quarter', 'business quarterly', 'bq', 'business_quarter'],
    'BA': ['business annual', 'business year', 'ba', 'business_annual'],
    
    # Higher frequency
    'H': ['hourly', 'hour', 'hours', 'h', '1h', '1hour', 'hr'],
    'T': ['minute', 'minutes', 'min', 't', '1min', '1minute'],
    'S': ['second', 'seconds', 'sec', 's', '1sec', '1second'],
}

def map_frequency_to_pandas(freq_string: str, mapping: dict = FREQUENCY_MAPPING) -> str:
    """
    Map a frequency string to a pandas frequency code.
    
    Parameters:
    - freq_string: The frequency string to map
    - mapping: The frequency mapping dictionary
    
    Returns:
    - str: Pandas frequency code or original string if no match
    """
    if freq_string is None or freq_string == '' or freq_string == 'Unknown':
        return None
        
    freq_lower = str(freq_string).lower().strip()
    
    # Direct match first
    for pandas_freq, aliases in mapping.items():
        if freq_lower in [alias.lower() for alias in aliases]:
            return pandas_freq
    
    # Handle special cases and partial matches
    if 'quarter' in freq_lower or freq_lower == 'q':
        return 'Q'
    elif 'month' in freq_lower and 'start' in freq_lower:
        return 'MS'
    elif 'month' in freq_lower:
        return 'M'
    elif 'day' in freq_lower or freq_lower in ['d', '1d']:
        return 'D'
    elif 'year' in freq_lower or 'annual' in freq_lower:
        return 'A'
    elif 'week' in freq_lower:
        return 'W'
    elif 'hour' in freq_lower or freq_lower.endswith('h'):
        return 'H'
    
    # If no match found, return original
    return freq_string

class CommonMetadata(BaseModel):
    """
    Standardized metadata model for any dataset in a Watchlist.

    Multiple alias names are supported for each field to handle various source formats.
    """
    # Canonical core identifiers
    id: str
    title: Optional[str] = None

    # Fields with multiple possible source names
    units: Optional[str] = None  # Consolidated units field
    series_type: Optional[str] = None
    data_type: Optional[str] = None
    frequency: Optional[str] = None
    frequency_short: Optional[str] = None
    original_source: Optional[str] = None
    source: Optional[str] = None
    description: Optional[str] = None

    # Temporal coverage
    start_date: Optional[datetime.date] = None
    end_date: Optional[datetime.date] = None
    last_updated: Optional[datetime.datetime] = None

    # Derived numeric characteristics
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    length: Optional[int] = None
    units_short: Optional[str] = None

    # Add frequency mapping as class attribute with proper ClassVar annotation
    frequency_mapping: ClassVar[dict] = FREQUENCY_MAPPING
    field_aliases: ClassVar[dict] = {}  # Will be set after class definition

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        arbitrary_types_allowed = True

# Define alias mappings as a class variable (outside the class)
FIELD_ALIASES = {
    'units': ['Unit', 'units', 'unit', 'currency', 'measure', 'units_short'],  # Consolidated units field
    'series_type': ['Series Type', 'series_type', 'type', 'quoteType', 'typeDisp', 'Data Type'],
    'data_type': ['Data Type', 'data_type', 'datatype', 'type', 'typeDisp'],
    'frequency': ['frequency', 'freq', 'periodicity', 'Freq.', 'Data frequency', 'resolution', 'Frequency'],
    'frequency_short': ['frequency_short', 'freq_short'],
    'original_source': ['original_source', 'originalSource', 'Source'],
    'source': ['source', 'data_source', 'provider', 'Source', 'original_source'],
    'description': ['description', 'notes', 'longBusinessSummary', 'table_title', 'indicator'],
    'start_date': ['start_date', 'observation_start', 'start_time', 'first_date', 'Start date', 'Series Start'],
    'end_date': ['end_date', 'observation_end', 'end_time', 'last_date', 'End date', 'Series End'],
    'last_updated': ['last_updated', 'lastUpdate', 'regularMarketTime', 'updated', 'pub_date', 'ReleaseDate', 'NextReleaseDate'],
    'min_value': ['min_value', 'minimum', 'min'],
    'max_value': ['max_value', 'maximum', 'max'],
    'length': ['length', 'count', 'observations', 'No. Obs.', 'No. Obs'],
    'units_short': ['units_short', 'unit_short', 'symbol', 'seasonal_adjustment_short'],
    'title': ['title', 'name', 'longName', 'shortName', 'label', 'shortname', 'series', 'Datasetname', 'TableName', 'metric_full'],
    'id': ['id', 'symbol', 'Ticker', 'Series ID', 'series_id', 'metric_short', 'path'],
    # Additional specialized fields that don't have direct CommonMetadata equivalents but could be useful
    'exchange': ['exchange', 'Exchange', 'exchDisp', 'fullExchange']
}

# Add the alias mapping as a class attribute
CommonMetadata.field_aliases = FIELD_ALIASES

# Add canonical metadata index after FIELD_ALIASES is defined
METADATA_INDEX = list(FIELD_ALIASES.keys())

# Update the class methods
@classmethod
def _resolve_field_value(cls, raw_meta: dict, field_name: str):
    """
    Resolve a field value using multiple possible alias names.
    Returns the first matching value found, or None if no match.
    """
    aliases = cls.field_aliases.get(field_name, [field_name])
    
    for alias in aliases:
        if alias in raw_meta and raw_meta[alias] is not None:
            value = raw_meta[alias]
            # Skip empty strings and 'nan' strings
            if isinstance(value, str) and (value == '' or value.lower() == 'nan'):
                continue
            return value
    return None

@classmethod
def from_series(cls, data: Union[pd.Series, pd.DataFrame], meta: Union[Mapping[str, Any], pd.Series, None] = None,
                source: str = None, id : str = None):
    """
    Build a CommonMetadata object from a pandas Series/DataFrame plus a raw metadata mapping.
    Attempts to infer min/max/length & start/end dates if not supplied.
    Uses multiple alias resolution for flexible field mapping.
    """
    if isinstance(data, pd.DataFrame):
        if data.shape[1] == 1:
            data_ser = data.iloc[:, 0]
        else:
            # Choose first numeric column fallback
            num_cols = [c for c in data.columns if pd.api.types.is_numeric_dtype(data[c])]
            data_ser = data[num_cols[0]] if num_cols else data.iloc[:, 0]
    else:
        data_ser = data

    raw_meta = {}
    if meta is not None:
        if isinstance(meta, pd.Series):
            raw_meta = meta.dropna().to_dict()
        else:
            raw_meta = {k: v for k, v in meta.items() if v is not None}

    # Build resolved metadata using alias resolution
    resolved_meta = {}
    
    # Handle required fields with fallbacks
    resolved_meta["id"] = cls._resolve_field_value(raw_meta, 'id') or str(getattr(data_ser, "name", "unknown_id"))
    resolved_meta["title"] = cls._resolve_field_value(raw_meta, 'title') or str(getattr(data_ser, "name", resolved_meta["id"]))

    # Resolve all other fields using aliases
    for field_name in cls.field_aliases.keys():
        if field_name not in ['id', 'title']:  # Already handled above
            value = cls._resolve_field_value(raw_meta, field_name)
            if value is not None:
                resolved_meta[field_name] = value

    # Infer start / end dates if not found
    if data_ser.index.__class__.__name__ == "DatetimeIndex":
        if "start_date" not in resolved_meta:
            resolved_meta["start_date"] = data_ser.index.min().date()
        if "end_date" not in resolved_meta:
            resolved_meta["end_date"] = data_ser.index.max().date()

    # Infer numeric stats if not found
    if pd.api.types.is_numeric_dtype(data_ser):
        if "min_value" not in resolved_meta:
            resolved_meta["min_value"] = float(data_ser.min())
        if "max_value" not in resolved_meta:
            resolved_meta["max_value"] = float(data_ser.max())
    if "length" not in resolved_meta:
        resolved_meta["length"] = int(len(data_ser))

    # Handle datetime parsing for fields that should be datetime objects
    datetime_fields = ['start_date', 'end_date', 'last_updated']
    for field in datetime_fields:
        if field in resolved_meta and resolved_meta[field] is not None:
            value = resolved_meta[field]
            
            # Skip if already a proper date/datetime object
            if isinstance(value, (datetime.date, datetime.datetime)):
                continue
                
            # Try to parse string values
            if isinstance(value, str):
                try:
                    # Handle timezone-aware datetime strings (like from FRED)
                    if 'T' in value or '-' in value[-6:]:  # ISO format or timezone offset
                        parsed_dt = pd.to_datetime(value)
                        if field == 'last_updated':
                            resolved_meta[field] = parsed_dt.to_pydatetime()
                        else:  # start_date, end_date should be date objects
                            resolved_meta[field] = parsed_dt.date()
                    else:
                        # Simple date string
                        parsed_dt = pd.to_datetime(value)
                        if field == 'last_updated':
                            resolved_meta[field] = parsed_dt.to_pydatetime()
                        else:
                            resolved_meta[field] = parsed_dt.date()
                except Exception as e:
                    print(f"Warning: Could not parse {field} value '{value}': {e}")
                    # Remove invalid datetime value
                    del resolved_meta[field]
    
    # Handle frequency_short mapping
    if 'frequency' in resolved_meta and resolved_meta['frequency'] is not None:
        if 'frequency_short' not in resolved_meta or resolved_meta['frequency_short'] is None:
            # Map frequency to pandas frequency code for frequency_short field
            pandas_freq = map_frequency_to_pandas(resolved_meta['frequency'])
            if pandas_freq:
                resolved_meta['frequency_short'] = pandas_freq
    
    if source is not None:
        # If source is provided, add it to the metadata
        resolved_meta["source"] = source
    if id is not None:
        # If id is provided, add it to the metadata
        resolved_meta["id"] = id
        
    # Return validated model
    return cls(**resolved_meta)

def to_display_dict(self) -> dict:
    """
    Export a dict with both canonical and common alias forms.
    """
    data = self.model_dump()
    
    # Add common aliases for backward compatibility
    alias_mappings = {
        'Unit': self.units,  # Changed from self.unit to self.units
        'Series Type': self.series_type,
        'Data Type': self.data_type,
        'observation_start': self.start_date,
        'observation_end': self.end_date
    }
    
    for alias, value in alias_mappings.items():
        if value is not None:
            data[alias] = value
            
    return data

def to_series(self) -> pd.Series:
    """
    Export the metadata to a pandas Series.
    """
    return pd.Series(self.model_dump())

# Bind the methods to the class
CommonMetadata._resolve_field_value = _resolve_field_value
CommonMetadata.from_series = from_series
CommonMetadata.to_display_dict = to_display_dict
CommonMetadata.to_series = to_series

############ Watchlist object defiition ####################    
class Watchlist(dict):
    """
    **Watchlist class.*
    A class for watchlists of time-series data, price history data for equities, commodities, macroeconomic series, etc.
    Stores a list of assets/tickers/macrodata codes to be watched, with metadata for each asset/ticker/macrodata code.
    The data for each asset/ticker/macrodata code can come from a wide range of sources. 
    This class is a dictionary of pandas DataFrames, with the following pre-set
    keys: 
    - 'watchlist': pd.DataFrame - created on init, contains the list of assets/tickers/macrodata codes to be watched, with columns 'id' and 'source'.
    tickers/data codes are the index of this DataFrame.
    - 'metadata': pd.DataFrame - created on init, contains metadata for each asset/ticker/macrodata code. The data codes are the column names of this
    dataframe and the index contains different metadata categories such as "source", "observation_start", "observation_end", "frequency", "units".
    - 'watchlist_datasets': dict - contains pandas Series and/or DataFrame objects, with the keys being the asset/ticker/macrodata codes. This is not
    created until the method "get_watchlist_data" is called, which pulls data from the source listed for each asset/ticker/macrodata code in the watchlist.
    
    *** __init__ Parameters :***
    - watchlist_data: pd.DataFrame, default None - a DataFrame containing the list of assets/tickers/macrodata codes to be watched, with columns 'id' and 'source'.
    - metadata_data: pd.DataFrame, default None - a DataFrame containing metadata for each asset/ticker/macrodata code. The data codes are the column names of this
    dataframe and the index contains different metadata categories such as "source", "observation_start", "observation_end", "frequency", "units".
    - watchlist_name: str, default "base_watchlist" - the name of the watchlist.
    - watchlists_path: str, default parent+fdel+"User_Data"+fdel+"Watchlists" - the path to the folder where watchlists are saved, relative to this file.
    
    The Watchlist  object can be initialized with watchlist and metadata data, that you may have gotten from the search_symbol_gui or created manually
    or you can just init a blank watchlist and add data to it later, using the GUI or manually.

    *** Methods: ***
    - load_watchlist: loads a watchlist from an Excel file, with two sheets: 'watchlist' and 'all_metadata'.
    - append_current_watchlist: appends new data to the current watchlist.
    - save_watchlist: saves the watchlist data to an Excel file.
    - get_watchlist_data: pulls data from the source listed for each asset/ticker/macrodata code in the watchlist.
    - update_metadata: updates the metadata with the new data.
    - load_watchlist_data: loads the watchlist data from a .h5s database file.
    - insert_data: inserts data into the watchlist_datasets dictionary.
    - drop_data: drops data from the watchlist_datasets dictionary.
    """
    def __init__(self, watchlist_data=None, metadata_data=None, watchlist_name: str = "base_watchlist", watchlists_path: str = parent+fdel+"User_Data"+fdel+"Watchlists"):
        super().__init__()
        # Initialize watchlist and metadata as pandas DataFrames
        self.name = watchlist_name
        self.watchlists_path = watchlists_path
        self['watchlist'] = pd.DataFrame(watchlist_data) if watchlist_data is not None else pd.DataFrame()
        self['metadata'] = pd.DataFrame(metadata_data) if metadata_data is not None else pd.DataFrame()
        self['watchlist_datasets'] = {}
        self['full_metadata'] = {}
        self.storepath = None

        self.source_labels = {
            'bea': 'BEA', 'tv': "Trading View", "rba_series": "RBA",
            'abs_series': 'ABS', "quandl": "NASDAQ", 
            'fred': 'FRED', 'glassnode': "Glassnode", 'coingecko': "Coin Gecko",
            'yfinance': 'Yahoo Finance'}

    def load_watchlist(self, filepath: str = ""):
        """load_watchlist method. Loads a watchlist from an Excel file, with two sheets: 'watchlist' and 'all_metadata'.
        If no filepath is provided, a file dialog will open to allow the user to choose a file."""

        print("Loading watchlist from filepath: ", filepath)
        if len(filepath) == 0:
           filepath = qt_load_file_dialog(dialog_title="Choose a watchlist excel file.", initial_dir = self.watchlists_path, 
                                                   file_types = "Excel Files (*.xlsx)")
         
        if len(filepath) > 0:
            try:
                self['metadata'] = pd.read_excel(filepath, index_col=0, sheet_name="all_metadata")
                # Normalize metadata index to canonical CommonMetadata fields
                self['metadata'] = self['metadata'].reindex(METADATA_INDEX)
                print("The metadata before processing: ", self['metadata'])
                
                # # Ensure all columns are object dtype for consistency
                # self['metadata'] = self['metadata'].astype('object')
                # # Replace empty strings and 'nan' strings with np.nan for proper NaN handling
                # self['metadata'] = self['metadata'].replace('', np.nan).replace('nan', np.nan)
                
                # Load watchlist data
                self['watchlist'] = pd.read_excel(filepath, index_col=0, sheet_name="watchlist")
                
                # Handle full_metadata if it exists
                try:
                    self["full_metadata"] = pd.read_excel(filepath, index_col=0, sheet_name="full_metadata", dtype=str).to_dict()
                except:
                    self["full_metadata"] = {}
                
                self.name = filepath.split(fdel)[-1].split(".")[0]
                
            except Exception as e:
                print("Error loading watchlist data from file, '.xlsx file may have had the wrong format for a watchlist,\
                        you want two sheets named 'watchlist' and 'all_metadata' with tables that can form dataframes in each. Exception:", e)
                return None
        
        self.storepath = os.path.splitext(filepath)[0] + ".h5s"
        self.storepath  = self.watchlists_path + fdel + self.name + fdel + self.name + ".h5s"
        
        # ENHANCED DEBUG: Check before index manipulation
        print(f"=== BEFORE INDEX MANIPULATION ===")
        print(f"Index unique count: {len(self['watchlist'].index.unique())}")
        print(f"ID column unique count: {len(self['watchlist']['id'].unique())}")
        print(f"Sample of index: {self['watchlist'].index[:5].tolist()}")
        print(f"Sample of id column: {self['watchlist']['id'][:5].tolist()}")
        
        # Set index as the id column. Put ids in the id column and they'll be added.
        if len(self["watchlist"].index.unique()) < len(self["watchlist"]["id"].unique()):
            print("CASE 1: Setting index to id column")
            # New values must have been copied into the id column  not the index, duplicate for index
            self["watchlist"].set_index("id", inplace=True, drop=False)
            self["watchlist"].index.rename("index", inplace=True)
        elif len(self["watchlist"].index.unique()) == len(self["watchlist"]["id"].unique()):
            print("CASE 2: Renaming existing index")
            # If the index is already set to the id column, just rename it
            self["watchlist"].index.rename("index", inplace=True)
        else:
            print("CASE 3: Copying index to id column")
            self["watchlist"]["id"] = self["watchlist"].index.copy()

        # ENHANCED DEBUG: Check after index manipulation
        #drop any duplicates present
        self.drop_data(drop_duplicates=True)

        current_index = self['watchlist'].index.tolist()
        meta_columns = self['metadata'].columns.tolist()
        print("Current watchlist index before any processing: ", current_index[:10])  # Show first 10
        print(f"Loaded watchlist shape: {self['watchlist'].shape}")

        # ENHANCED DEBUG: Check after HDF5 processing
        print(f"=== AFTER HDF5 PROCESSING ===")
        print(f"Watchlist shape: {self['watchlist'].shape}")
        print(f"Source non-null count: {self['watchlist']['source'].notna().sum()}")

        try:
            self.load_watchlist_data()
        except Exception as e:
            print("Watchlist and metadata were loaded but error encountered in loading the watchlist datasets from hdfStore file, error: ", e)

        # ENHANCED DEBUG: Check before drop_data
        print(f"=== BEFORE DROP_DATA ===")
        print(f"Watchlist shape: {self['watchlist'].shape}")
        print(f"Source non-null count: {self['watchlist']['source'].notna().sum()}")

        #Drop dem dupes dog
        self.drop_data(drop_duplicates=True)

    def append_current_watchlist(self, watchlist_data: pd.DataFrame, metadata_data: pd.DataFrame):
        """append_current_watchlist method.
        Mostly for use with the GUI, this method appends new data to the current watchlist."""


        # Append new data to the current watchlist
        self['watchlist'] = pd.concat([self['watchlist'], watchlist_data], axis=0)
        self['metadata'] = pd.concat([self['metadata'], metadata_data], axis=1)

    def save_watchlist(self, path: str = parent+fdel+"User_Data"+fdel+"Watchlists"):
        """save_watchlist method.

        This function saves the watchlist data to an Excel file with two sheets 'watchlist' and 'metadata'. 
        It also saves your data series if you have pulled the data first using the get_watchlist_data method.
        """

        # Example method to save watchlist data to an Excel file
        saveName = os.path.basename(self.name)  # Get just the name part, not the full path
        saveName = saveName.replace(" ", "_")   # Replace spaces with underscores in the name only
        save_directory = os.path.join(path, saveName)
        save_path = os.path.join(save_directory, saveName + ".xlsx")
        
        print("Saving watchlist data to Excel file... save name: ", saveName, " to path: ", path, "watchlist name: ", self.name, 
              "save path: ", save_path, "save directory: ", save_directory)
        
        if not os.path.exists(save_directory):
            os.makedirs(save_directory, exist_ok=True)
            
        # Strip timezone information from metadata before saving to Excel
        metadata_for_excel = strip_timezone_from_df(self['metadata'])
        
        # Create DataFrame from full_metadata dict of Series
        if self["full_metadata"]:
            full_meta_df = pd.DataFrame(self["full_metadata"])
            full_meta_for_excel = strip_timezone_from_df(full_meta_df)
        else:
            full_meta_for_excel = pd.DataFrame()
        
        with pd.ExcelWriter(save_path) as writer:
            self['watchlist'].to_excel(writer, sheet_name='watchlist')
            metadata_for_excel.to_excel(writer, sheet_name='all_metadata')
            if not full_meta_for_excel.empty:
                full_meta_for_excel.to_excel(writer, sheet_name='full_metadata')

        if self['watchlist_datasets']:
            self.storepath = os.path.join(save_directory, saveName + ".h5s")
            close_open_stores(self.storepath)  #Close any open hdf5 stores pointing to this path

            try:    
                watchstore = pd.HDFStore(self.storepath, mode='a')
                
                # Create a mapping of original keys to sanitized keys
                key_mapping = {}
            
                for key in self["watchlist_datasets"].keys():
                    series = self["watchlist_datasets"][key]
                    if isinstance(series, pd.DataFrame):
                        if len(series.columns) == 1:
                            series = series.squeeze()
                            self["watchlist_datasets"][key] = series
                    
                    # Sanitize the key for HDF5 storage
                    sanitized_key = sanitize_hdf_key(key)
                    key_mapping[sanitized_key] = key
                    
                    # Store with sanitized key
                    watchstore[sanitized_key] = series if series is not None else pd.Series(dtype='object')
                
                # Save the key mapping for later retrieval
                if key_mapping:
                    mapping_series = pd.Series(key_mapping, name='original_keys')
                    watchstore['_key_mapping'] = mapping_series
                    
                watchstore.close()
                print("Saved watchlist datasets to .h5s database... save name: ", saveName)

            except Exception as e:
                print("Error saving watchlist data to file. Exception: ", e)
                watchstore.close()

        return saveName, save_path
    
    class TimeoutError(Exception):
        pass

    def get_watchlist_data(self, start_date: str = "1600-01-01", id_list: list = None, timeout: int = 60):
        """
        get_watchlist_data method.

        This function takes a Watchlist object and returns a dictionary of pandas Series and/or dataframe objects.
        Data will be pulled from the source listed for each asset/ticker/macrodata code in the watchlist.
        The max time-length for each asset will be pulled. Geting higher frequency data from trading view may require 
        doing it manually with the tvDatafeedz module.

        Parameters:

        - Watchlist: search_symbol_gui.Watchlist object
        - start_date: str, default "1900-01-01"
        - id_list: list, default None - a list of asset/ticker/macrodata codes to pull data for. If None, all assets in the watchlist will be pulled.
        - timeout: int, default 60 - timeout in seconds for each individual data pull
        """

        watchlist = pd.DataFrame(self["watchlist"])#; meta = pd.DataFrame(self["metadata"])
        # FIX: Start with a copy of existing metadata to preserve all columns
        meta = self["metadata"].copy() if not self["metadata"].empty else pd.DataFrame()
        #print("Watchlist: \n", watchlist, "\n\nMetadata: \n", meta)

        #Then get the data....
        data = {}
        # Build candidate ids from watchlist when id_list is not supplied
        if id_list is None:
            if "id" in watchlist.columns:
                ids = watchlist["id"].tolist()
            else:
                ids = watchlist.index.to_list()
        else:
            # Use provided id_list (may contain index keys or values from the 'id' column)
            ids = list(id_list)

        # Normalize requested ids to actual watchlist index entries:
        resolved_ids = []
        missing_ids = []
        for req in ids:
            # If it already matches an index entry, keep it
            if req in watchlist.index:
                resolved_ids.append(req)
                continue

            # If it matches a value in the 'id' column, map to the corresponding index (take first match)
            if "id" in watchlist.columns:
                matches = watchlist.index[watchlist["id"].astype(str) == str(req)].tolist()
                if matches:
                    # If multiple rows match, we keep them all to preserve data
                    resolved_ids.extend(matches)
                    continue

            # Not found: warn and skip
            missing_ids.append(req)

        if missing_ids:
            print(f"Warning: the following requested ids were not found in watchlist index or 'id' column and will be skipped: {missing_ids}")

        # Final list to iterate
        ids_to_process = resolved_ids

        for i in ids_to_process:
            # Accessing watchlist row is now safe because i was resolved from the index
            try:
                sauce = str(watchlist.loc[i, "source"]).strip()
            except KeyError:
                print(f"Warning: index '{i}' not found in watchlist. Skipping.")
                continue

            eyed = str(watchlist.loc[i, "id"]).strip()
            try:
                exchag = str(meta.loc["exchange", i]).strip()
            except Exception:
                exchag = None
            print(f"Attempting data pull for series id: {eyed}, from source: {sauce},\n start_date: {start_date}), exchange_code: {exchag}")
            
            # Initialize variables for this iteration
            series_meta = None
            ds_data = None
            
            # Windows-compatible timeout using threading
            def pull_data_with_timeout():
                nonlocal series_meta, ds_data
                try:
                    ds = Pull_Data.dataset()
                    ds.get_data(sauce, eyed, start_date, exchange_code=exchag, timeout=timeout)
                    ds_data = ds.data
                    series_meta = ds.SeriesInfo
                    return True
                except Exception as e:
                    print(f"Error in data pull thread for {eyed}: {e}")
                    return False
            
            # Create and start thread
            thread = threading.Thread(target=pull_data_with_timeout)
            thread.daemon = True
            thread.start()
            thread.join(timeout=timeout)
            
            if thread.is_alive():
                print(f"Timeout ({timeout}s) exceeded for {eyed} from {sauce}. Skipping...")
                data[str(i)] = pd.Series([f"Data pull timed out after {timeout} seconds.", "Timeout exceeded", 
                                        f"Source: {sauce}"], name=f"Timeout_{eyed}", index=[0, 1, 2])
                continue  # Skip metadata processing for failed pulls
            
            if ds_data is None:
                print(f"Data pull failed for {eyed} from {sauce}.")
                data[str(i)] = pd.Series(["Data pull failed for this series.", "Devo bro....", 
                                        "Check the error messages above"], name=f"Error_{eyed}", index=[0, 1, 2])
                continue  # Skip metadata processing for failed pulls
            
            # Data pull was successful
            data[str(i)] = ds_data
            print(f"Data pull successful for {eyed} from {sauce}.")

            # Process metadata only if data pull was successful
            if series_meta is not None and ds_data is not None:
                try:
                    # FIX: Ensure series_meta is properly oriented as a column
                    if isinstance(series_meta, pd.DataFrame):
                        # If it's a DataFrame, squeeze to Series and ensure it's named correctly
                        series_meta = series_meta.squeeze()
                    
                    if isinstance(series_meta, pd.Series):
                        # Ensure the Series has the correct name (the series ID)
                        series_meta.name = eyed
                        print(f"Processing metadata for {eyed}, series_meta type: {type(series_meta)}")
                        print(f"Raw metadata sample: {series_meta.head()}")
                    else:
                        print(f"Warning: series_meta for {eyed} is not a Series or DataFrame: {type(series_meta)}")
                        # Create minimal metadata if series_meta is not usable
                        series_meta = pd.Series({
                            'id': eyed,
                            'source': sauce,
                            'title': eyed
                        }, name=eyed)

                    #Create common metadata for metadata concatenation
                    print(f"Creating CommonMetadata for {eyed}...")
                    print(f"Data type: {type(ds_data)}, Metadata type: {type(series_meta)}")

                    common = CommonMetadata.from_series(ds_data, series_meta, source = sauce)
                    print(f"CommonMetadata created successfully for {eyed}")
                    print("Common metadata for concatenation: \n", common.to_series())

                    # FIX: Update or add the common metadata column instead of always concatenating
                    common_series = common.to_series()
                    common_series.name = eyed  # Ensure proper column name

                    # Ensure common_series only contains canonical metadata rows before concatenation
                    common_series = common_series.reindex(METADATA_INDEX)

                    if eyed in meta.columns:
                        # Update existing column
                        meta[eyed] = common_series
                    else:
                        # Add new column
                        meta = pd.concat([meta, common_series.to_frame()], axis=1)
                    self["full_metadata"][eyed] = series_meta
                    
                    print(f"Successfully processed metadata for {eyed}")

                except Exception as e:
                    print(f"Error processing metadata for {eyed}. Exception: {e}")
                    print(f"Series_meta content: {series_meta}")
                    print(f"DS_data type: {type(ds_data)}")
                    
                    # Create fallback metadata to prevent complete failure
                    try:
                        fallback_meta = pd.Series({
                            'id': eyed,
                            'title': eyed,
                            'source': sauce,
                            'frequency': 'Unknown',
                            'units': 'Unknown'
                        }, name=eyed)
                        meta = pd.concat([meta, fallback_meta], axis=1)
                        print(f"Created fallback metadata for {eyed}")
                    except Exception as fallback_error:
                        print(f"Even fallback metadata failed for {eyed}: {fallback_error}")
                    continue

        # Check if 'watchlist_datasets' key already exists
        if "watchlist_datasets" in self:
            # Append new data to the existing dictionary
            self["watchlist_datasets"].update(data)
        else:
            # Create the dictionary if it doesn't exist
            self["watchlist_datasets"] = data

        # Before assigning back to self['metadata'], ensure canonical index (drops stray rows)
        meta = meta.reindex(METADATA_INDEX)
        self["metadata"] = meta  # Update the metadata DataFrame with the new data
        print(f"Final metadata shape: {meta.shape}")
        print(f"Final metadata columns: {meta.columns.tolist()}")
        
        self.update_metadata()
        self.save_watchlist()

    def update_metadata(self):
        
        #Drop any duplicates in the metadata
        self.drop_data(drop_duplicates=True)
        # Update the metadata with the new data
        if self["watchlist_datasets"]:
            print("Running watchlist update_metadata method.....")
            for key in self["watchlist_datasets"].keys():
                series = self["watchlist_datasets"][key]
                #first reduce dataframes to series if the df has only a single column
                if isinstance(series, pd.DataFrame):
                    print("Your series is a DataFrame, reducing to a Series.... Have a look at it first: \n", series)
                    if len(series.columns) == 1:
                        series = series.squeeze()
                    else:
                        print(f"Skipping this one {key}, it is a DataFrame with more than one columns,", series.columns)
                        continue
            
                # Get the title from metadata, use series.name or key as fallback
                try:
                    metadata_title = self["full_metadata"][key].loc["title"]
                    if pd.isna(metadata_title) or metadata_title == "" or metadata_title is None:
                        # Use series name if available, otherwise use the key
                        title = series.name if series.name is not None and series.name != "" else key
                        print(f"Title was NaN/empty for {key}, using fallback title: {title}")
                    else:
                        title = metadata_title
                except:
                    # Title not found in metadata, use series name or key as fallback
                    title = series.name if series is not None and series.name != "" else key
                    #print(f"Title not found in metadata for {key}, using fallback title: {title}")
                
                # Rename the series to have the proper title
                try:
                    if series is not None and series.name != title:
                        series.rename(title, inplace=True)
                        print(f"Renamed series {key} to: {title}")
                except Exception as err:
                    print("Failed to rename series, ", series.name, " to title: ", title, ", error: ", err)

                # start_date = series.index[0] if series is not None else np.nan
                # end_date = series.index[-1] if series is not None else np.nan
                self["watchlist_datasets"][key] = series

                #Update the watchlist with improved metadata as well as the metadata DataFrame
                self["watchlist"].loc[key, "id"] = key
                
                # Fix Warning 1: Ensure title column is object dtype before assignment
                if "title" not in self["watchlist"].columns:
                    self["watchlist"]["title"] = ""
                self["watchlist"]["title"] = self["watchlist"]["title"].astype('object')
                self["watchlist"].loc[key, "title"] = str(title)  # Explicitly convert to string
                
        else:
            print("Download datasets for the watchlist first using get_watchlist_data() or load_watchlist_data() methods.....")
            return

    def load_watchlist_data(self, ask_input: bool = False):
        """load_watchlist_data method.
        This function loads the watchlist data from a .h5s database file. The data is stored in the 'watchlist_datasets' dictionary.
        Or just drop a given data_name from the watchlist_datasets dictionary, watchlist and metadata dataframes."""
        
        print("Database filepath: ", self.storepath)
        if self.storepath is not None and os.path.isfile(self.storepath):
            with pd.HDFStore(self.storepath, mode='a') as data:
                # Load key mapping if it exists
                key_mapping = {}
                if '_key_mapping' in data.keys():
                    mapping_series = data['_key_mapping']
                    key_mapping = mapping_series.to_dict()
                
                # Load data with original keys restored
                self['watchlist_datasets'] = {}
                for sanitized_key in data.keys():
                    if sanitized_key.startswith('/_key_mapping'):
                        continue  # Skip the mapping key
                    
                    clean_key = sanitized_key.lstrip('/')
                    original_key = key_mapping.get(clean_key, clean_key)
                    series = data[sanitized_key]
                    
                    # FIX: Attempt to convert index to DatetimeIndex if it's not already
                    if not isinstance(series.index, pd.DatetimeIndex):
                        try:
                            # Try to infer datetime from the index (handles int64 timestamps, strings, etc.)
                            series.index = pd.to_datetime(series.index, errors='coerce')
                            print(f"Converted index to DatetimeIndex for series: {original_key}")
                        except Exception as e:
                            print(f"Could not convert index to DatetimeIndex for series: {original_key}. Error: {e}")
                            # Leave as-is; update_metadata will handle the fallback
                    
                    self['watchlist_datasets'][original_key] = series
                
                data.close()
            self.update_metadata()
        else:
            print("No .h5s database found for this watchlist. Get and save data first....")
            if ask_input:
                if input("Do you want to attempt pulling the data for the watchlist now? y/n?") == "y":
                    self.get_watchlist_data()
                    self.save_watchlist()
                    self.update_metadata()
                else:
                    return
            return
        
        print("Loaded database from .h5s file, keys: ", list(self["watchlist_datasets"].keys()))

    def insert_data(self, data: Union[pd.DataFrame, pd.Series], metadata: pd.Series):
        """ INSERT DATA METHOD.
        Add a dataset into your watchlist database. Must be pandas series or dataframe. 
        Some metadata must be supplied.

        **Parameters:**
        - data: pd.DataFrame or pd.Series: Your dataset.
        - metadata: pd.Series - This must have index values "id", "title" & "source"at a minimum.
            - "title": str - this is the title/name for your dataset, can be the same as id.
            - "id": str - this is the all important datacode/ticker/id for the dataset from the source. 
            - "source": str - this is the name of the data source. It can be one of the sources used by Pull_Data module 
            or it can be "SavedData"to load the series from the User_Data/SavedData folder. An arbitrary source name can also be used 
            and if it does not match any of the upported sources the dataset will never be updated when the get_watchlist_data method is run. 
        """
        for key in ["id", "title", "source"]:
            if key not in metadata.index.to_list():
                print(f'You need to have {key} in your metadata series for this to work, pulling out.')
                return

        self["watchlist_datasets"][metadata["id"]] = data
        self["watchlist"].loc[metadata["id"], "id"] = metadata["id"]
        self["watchlist"].loc[metadata["id"], "title"] = metadata["title"]
        self["watchlist"].loc[metadata["id"], "source"] = metadata["source"]

        ## Drop if already exiting in the dataset
        if metadata["id"] in self["metadata"].columns:
            self["metadata"].drop(metadata["id"], axis=1, inplace=True)
            
        self["metadata"] = pd.concat([self["metadata"], metadata], axis = 1)
        # Ensure metadata index conforms to CommonMetadata model
        self["metadata"] = self["metadata"].reindex(METADATA_INDEX)
        print("Dataset ", metadata['title'], f"inserted into your {self.name} watchlist.")

    def add_series_from_SavedData(self, seriesName: str):
        """Add a data series that is found in the User_Data/SavedData folder to your watchlist.

        **Parameters:**
        - seriesName: str - This must match the name of an .xlsx file that is found in your SavedData folder. These files are generated
        by the Pull_Data module when the data is pulled and saved. These have tw sheets with names 'Closing_Price' and 'SeriesInfo'that
        contain your data and metadata.
        """
        rel_datapath = parent+fdel+"User_Data"+fdel+"SavedData"
        
        try:
            series = pd.read_excel(rel_datapath+fdel+seriesName+".xlsx", sheet_name="Closing_Price", index_col=0, parse_dates=True).squeeze()
            series_meta = pd.read_excel(rel_datapath+fdel+seriesName+".xlsx", sheet_name="SeriesInfo",index_col=0).squeeze().rename(seriesName)
            series_meta.loc["title"] = series.name
            series_meta.loc["id"] = seriesName
            series_meta.loc["source"] = "SavedData"
            series_meta.loc["notes"] = series_meta.loc["title"]+", aggregate index by the Macro Bootlegger."
            self.insert_data(series, series_meta)
        except Exception as e:
            print("Could not find the data or something else went wrong, check you seriesName, error message: ", e)
            return

    def drop_data(self, data_name: str = None, drop_duplicates: bool = False):
        """drop_data method.
        Eliminate duplicates from the watchlist and metadata dataframes, and drop data from the watchlist_datasets dictionary.
        Or just drop a given data_name from the watchlist_datasets dictionary, watchlist and metadata dataframes."""
        
        if data_name is not None:
            if data_name in self["watchlist_datasets"].keys():
                self["watchlist_datasets"].pop(data_name)
            if data_name in self["metadata"].columns:
                self["metadata"].drop(data_name, axis=1, inplace=True)
            if data_name in self["watchlist"].index:
                self["watchlist"].drop(data_name, axis=0, inplace=True)
        
        if drop_duplicates:
            watch = pd.DataFrame(self["watchlist"])
            #print("Checking for duplicates in watchlist... Original index/columns watchlist/metadata: ", watch.index, self["metadata"].columns)
            offenders = list(watch[watch.index.duplicated()].index)
            print("Duplicate indexes found in watchlist & will be dropped: ", offenders)
            meta , dropped = drop_duplicate_columns(self["metadata"]); self["metadata"] = meta
            print("Duplicate columns found in metadata & will be dropped: ", dropped)
            # Drop duplicate columns
            self["metadata"] = self["metadata"].loc[:, ~self["metadata"].columns.duplicated(keep='first')]
          
            self["watchlist"].drop_duplicates(inplace=True)
            tickers_to_remove = []
            for ticker in self["watchlist_datasets"].keys():
                if ticker not in self["watchlist"]["id"].to_list():
                    tickers_to_remove.append(ticker)
            
            for ticker in tickers_to_remove:
                self["watchlist_datasets"].pop(ticker)

    def rename_series(self, renamer_dict: dict):
        """
        Batch rename series titles using a dict {id: new_name}.
        Minimal logic: set watchlist.title and metadata['title'] entries; exceptions per-item are ignored.
        """
        if "title" not in self["watchlist"].columns:
            self["watchlist"]["title"] = ""
            self["watchlist"]["title"] = self["watchlist"]["title"].astype('object')

        for sid, newn in (renamer_dict or {}).items():
            try:
                self["watchlist"].loc[sid, "title"] = str(newn)
                # ensure metadata has the column and a 'title' row
                if sid not in self["metadata"].columns:
                    self["metadata"][sid] = np.nan
                if "title" not in self["metadata"].index:
                    self["metadata"].loc["title"] = np.nan
                self["metadata"].loc["title", sid] = str(newn)
            except Exception:
                print(f"Could not rename series {sid} to {newn}, check if the id exists in the watchlist.")
                # ignore errors for individual items and continue
                continue

        # Normalize metadata index to canonical CommonMetadata fields after batch rename
        self["metadata"] = self["metadata"].reindex(METADATA_INDEX)

    def plot_watchlist(self, left: list, right: list, template: str = "seaborn", plot_title: str = None,
                       left_axis_title: str = None, right_axis_title: str = None, other_series: dict = None, x_start_date: str = None,
                       margin: dict = None, figsize: tuple = (12,6), dpi: int = 110, width: int = None, height: int = None, source_str: str = None,
                       align_zeros: bool = False, plotly_kwargs: dict = None,
                       # logo options: path to image file (PNG/JPG). If provided, will inset bottom-right.
                       logo_path: str = None, logo_size: float = 0.12, logo_opacity: float = 1.0, logo_x_offset: int = 8, logo_y_offset: int = 6):
        """
        Plot selected datasets in this watchlist on a dual-axis chart.

        Parameters:
        - left: list of ids (strings) to plot on the left axis (primary)
        - right: list of ids (strings) to plot on the right axis (secondary)
        - template: str, default "plotly_white" - Plotly template to use
        - plot_title: str, default None - Title for the plot (renamed from 'title' to avoid shadowing)
        - left_axis_title: str, default None - Title for the left axis
        - right_axis_title: str, default None - Title for the right axis
        - other_series: dict, default None - Additional series to plot. Format: {"left": pd.Series or [pd.Series, ...], "right": pd.Series or [pd.Series, ...]}
        - x_start_date: str, default None - Start date for the x-axis (e.g., "2020-01-01")
        - margin: dict, default None - Margin configuration, e.g., {"t": 50, "b": 50, "l": 50, "r": 50}
        - figsize: tuple (width_in_inches, height_in_inches). Converted to pixels by dpi.
        - dpi: int, dots-per-inch used to convert figsize into pixels (default 96).
        - width, height: ints in pixels. If provided these override figsize conversion.
        - source_str: str, default None - Override source string for annotation
        - align_zeros: bool, default False - Align zero positions of left and right y-axes
        - plotly_kwargs: dict, optional - Arbitrary keyword args passed to fig.update_layout (e.g. {'width':1200, 'height':700, 'margin': {...}, 'legend': {...}})
        - logo_path: str, default None - Path to a logo image file (PNG/JPG) to inset in the bottom-right corner
        - logo_size: float, default 0.12 - Relative size of the logo (0 < logo_size <= 1)
        - logo_opacity: float, default 1.0 - Opacity of the logo (0.0 to 1.0)
        - logo_x_offset: int, default 8 - Horizontal offset in pixels from the right edge
        - logo_y_offset: int, default 6 - Vertical offset in pixels from the bottom edge
        """

        if not self.get("watchlist_datasets"):
            print("No datasets loaded. Use get_watchlist_data() or load_watchlist_data() first.")
            return None

        full_list = left + right
        charted = self['watchlist'].loc[full_list]
        sources = charted["source"].unique()
        # Build a string of source labels for all unique sources in the chart
        if source_str is None:
            source_str = ", ".join([self.source_labels.get(s, str(s)) for s in sources])
        # Helper to build dict[title] -> Series from a list of ids
        def build_series_map(ids: list) -> dict:
            out = {}
            for did in ids or []:
                if did not in self["watchlist_datasets"]:
                    print(f"Warning: '{did}' not in watchlist_datasets. Skipping.")
                    continue
                ser = self["watchlist_datasets"][did]
                # Reduce DataFrame to Series where possible
                if isinstance(ser, pd.DataFrame):
                    if ser.shape[1] == 1:
                        ser = ser.squeeze()
                    else:
                        first_col = ser.columns[0]
                        print(f"Info: '{did}' is a DataFrame with multiple columns. Using first column: {first_col}")
                        ser = ser[first_col]
                if not isinstance(ser, (pd.Series, pd.Index)):
                    print(f"Warning: '{did}' is not a pandas Series. Skipping.")
                    continue
                # Title from watchlist, fallback to id
                try:
                    series_title = self["watchlist"].loc[did, "title"]
                    if pd.isna(series_title) or series_title is None or series_title == "":
                        series_title = did
                except Exception:
                    series_title = did
                out[str(series_title)] = ser
            return out

        # De-duplicate ids if any appear in both lists (prefer right axis)
        left_ids = [i for i in (left or []) if i not in (right or [])]
        right_ids = right or []

        primary_data = build_series_map(left_ids)
        secondary_data = build_series_map(right_ids)

        # Enhanced other_series handling to support lists of series
        if other_series:
            for axis, series_data in other_series.items():
                if axis.lower() not in ["left", "right"]:
                    print(f"Warning: Invalid axis '{axis}' in other_series. Use 'left' or 'right'.")
                    continue
                
                # Determine target data dict
                target_data = primary_data if axis.lower() == "left" else secondary_data
                
                # Handle both single series and lists of series
                series_list = series_data if isinstance(series_data, list) else [series_data]
                
                for i, series in enumerate(series_list):
                    if not isinstance(series, (pd.Series, pd.Index)):
                        print(f"Warning: Item {i} in other_series['{axis}'] is not a pandas Series. Skipping.")
                        continue
                    
                    # Determine series title/legend name
                    if hasattr(series, 'name') and series.name is not None and series.name != "":
                        series_title = str(series.name)
                    else:
                        # Create a fallback name based on axis and position
                        axis_name = "Left" if axis.lower() == "left" else "Right"
                        series_title = f"Other {axis_name} Series {len(target_data) + 1}"
                    
                    # Ensure unique title if there are duplicates
                    original_title = series_title
                    counter = 1
                    while series_title in target_data:
                        series_title = f"{original_title} ({counter})"
                        counter += 1
                    
                    target_data[series_title] = series

        if not primary_data and not secondary_data:
            print("Nothing to plot. Check the ids provided.")
            return None

        if plot_title is None:
            plot_title = self.name if hasattr(self, "name") and self.name else "Watchlist Plot"

        if left_axis_title is None:
            if left_ids and not pd.isna(self["metadata"].loc["units", left_ids[0]]):
                left_axis_title = self["metadata"].loc["units", left_ids[0]]
            else:
                left_axis_title = "Primary Axis"
        if right_axis_title is None:
            if right_ids and not pd.isna(self["metadata"].loc["units", right_ids[0]]):
                right_axis_title = self["metadata"].loc["units", right_ids[0]]
            else:
                right_axis_title = "Secondary Axis"

        # FIX: Slice series from x_start_date if provided
        if x_start_date:
            try:
                start_dt = pd.to_datetime(x_start_date)
                # Slice primary_data series
                for title, series in primary_data.items():
                    if isinstance(series.index, pd.DatetimeIndex):
                        primary_data[title] = series.loc[start_dt:]
                # Slice secondary_data series
                for title, series in secondary_data.items():
                    if isinstance(series.index, pd.DatetimeIndex):
                        secondary_data[title] = series.loc[start_dt:]
                print(f"Sliced all series to start from: {x_start_date}")
            except Exception as e:
                print(f"Warning: Could not parse x_start_date '{x_start_date}' for slicing: {e}")

        # Set default margins if not provided
        if margin is None:
            margin = {"t": 60, "b": 40, "l": 70, "r": 10}  # Reduced bottom margin

        fig = charting_plotly.dual_axis_basic_plot(primary_data, secondary_data=secondary_data, title=plot_title, template=template,
                                                    primary_yaxis_title=left_axis_title, secondary_yaxis_title=right_axis_title)
        
        # Add zero alignment if requested
        if align_zeros and primary_data and secondary_data:
            # Calculate data ranges for both axes
            left_values = []
            right_values = []
            
            for series in primary_data.values():
                left_values.extend(series.dropna().values)
            for series in secondary_data.values():
                right_values.extend(series.dropna().values)
            
            if left_values and right_values:
                left_min, left_max = min(left_values), max(left_values)
                right_min, right_max = min(right_values), max(right_values)
                
                # Skip alignment if either axis doesn't cross zero
                if (left_min >= 0 or left_max <= 0) and (right_min >= 0 or right_max <= 0):
                    print("Zero alignment skipped: neither axis crosses zero")
                elif left_min >= 0 or left_max <= 0:
                    print("Zero alignment skipped: left axis doesn't cross zero")
                elif right_min >= 0 or right_max <= 0:
                    print("Zero alignment skipped: right axis doesn't cross zero")
                else:
                    # Both axes cross zero - proceed with alignment
                    # Calculate the proportion of negative vs positive range for each axis
                    left_negative_range = abs(left_min)
                    left_positive_range = left_max
                    
                    right_negative_range = abs(right_min)
                    right_positive_range = right_max
                    
                    # Calculate zero position as fraction from bottom (0=bottom, 1=top)
                    left_zero_position = left_negative_range / (left_negative_range + left_positive_range)
                    right_zero_position = right_negative_range / (right_negative_range + right_positive_range)
                    
                    print(f"Left zero position: {left_zero_position:.3f}, Right zero position: {right_zero_position:.3f}")
                    
                    # Align by adjusting ranges to match the larger zero fraction
                    if abs(left_zero_position - right_zero_position) > 0.01:  # Only adjust if difference is meaningful
                        target_zero_position = max(left_zero_position, right_zero_position)
                        
                        if left_zero_position < target_zero_position:
                            # Expand left axis negative range to match target zero position
                            # target_zero_position = new_negative_range / (new_negative_range + left_positive_range)
                            # Solving for new_negative_range:
                            new_left_negative = (target_zero_position * left_positive_range) / (1 - target_zero_position)
                            new_left_min = -new_left_negative
                            fig.update_layout(yaxis=dict(range=[new_left_min, left_max]))
                            print(f"Adjusted left axis range: [{new_left_min:.2f}, {left_max:.2f}]")
                            print(f"New left zero position: {new_left_negative / (new_left_negative + left_positive_range):.3f}")
                        
                        if right_zero_position < target_zero_position:
                            # Expand right axis negative range to match target zero position
                            new_right_negative = (target_zero_position * right_positive_range) / (1 - target_zero_position)
                            new_right_min = -new_right_negative
                            fig.update_layout(yaxis2=dict(range=[new_right_min, right_max]))
                            print(f"Adjusted right axis range: [{new_right_min:.2f}, {right_max:.2f}]")
                            print(f"New right zero position: {new_right_negative / (new_right_negative + right_positive_range):.3f}")
                    else:
                        print("Zero positions are already well-aligned")

        # Compute layout width/height (pixels) with precedence:
        # 1) explicit width/height args (pixels)
        # 2) figsize (inches) converted by dpi
        layout_kwargs = {}
        if width is not None:
            try:
                layout_kwargs['width'] = int(width)
            except Exception:
                pass
        if height is not None:
            try:
                layout_kwargs['height'] = int(height)
            except Exception:
                pass

        if ('width' not in layout_kwargs or 'height' not in layout_kwargs) and figsize is not None:
            try:
                w_in, h_in = figsize
                # Only set those not already provided explicitly
                if 'width' not in layout_kwargs:
                    layout_kwargs['width'] = int(w_in * dpi)
                if 'height' not in layout_kwargs:
                    layout_kwargs['height'] = int(h_in * dpi)
            except Exception:
                # invalid figsize tuple -> ignore
                pass

        # Default layout dict (margin + legend); user can override via plotly_kwargs
        default_layout = dict(margin=margin,
                              legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5))
        # Merge computed width/height into default layout
        default_layout.update(layout_kwargs)

        # Add zero line styling if align_zeros is True
        if align_zeros:
            default_layout.update({
                'yaxis': {**default_layout.get('yaxis', {}), 'zeroline': True, 'zerolinecolor': 'gray', 'zerolinewidth': 1},
                'yaxis2': {**default_layout.get('yaxis2', {}), 'zeroline': True, 'zerolinecolor': 'gray', 'zerolinewidth': 1}
            })

        # If user passed plotly_kwargs, merge them so user values override defaults
        if isinstance(plotly_kwargs, dict):
            merged_layout = {**default_layout, **plotly_kwargs}
        else:
            merged_layout = default_layout

        # Apply merged layout to figure
        fig.update_layout(**merged_layout)
        
        # Add annotation for data source
        fig.add_annotation(
            text="Source: " + source_str,  # Your custom text
            xref="paper", yref="paper",  # Relative to the entire figure
            x=0.0, y=-0.12,  # Bottom left position (adjust if needed)
            font=dict(size=14, color="black"),  # Small font, black color
            showarrow=False, 
            align="left",  # Left-align text
            bgcolor="white",  # White background for visibility
            bordercolor="black",  # Black border
            borderwidth=1
        )

        # Add optional inset logo if provided. Default behaviour: interpret logo_x_offset/logo_y_offset
        # as pixel offsets from the figure origin (bottom-left, i.e. paper (0,0)) and anchor the image's
        # bottom-left corner there. This places the image in the margin when offsets are small or
        # inside the plot if offsets push it into the plot area. If layout width/height can't be
        # determined, falls back to paper fractions.
        if logo_path:
            try:
                # read and base64-encode the image so plotly can embed it
                with open(logo_path, 'rb') as _f:
                    raw = _f.read()
                b64 = base64.b64encode(raw).decode('ascii')
                src = f"data:image/png;base64,{b64}"

                # determine layout width/height (pixels) to convert pixel offsets
                layout_w = merged_layout.get('width') if isinstance(merged_layout, dict) else None
                layout_h = merged_layout.get('height') if isinstance(merged_layout, dict) else None
                try:
                    # fallback to fig.layout values if not found in merged_layout
                    if not layout_w and getattr(fig.layout, 'width', None):
                        layout_w = fig.layout.width
                    if not layout_h and getattr(fig.layout, 'height', None):
                        layout_h = fig.layout.height
                except Exception:
                    pass

                # Compute image size in pixels and preserve aspect ratio when possible
                img_px_w = None
                img_px_h = None
                if layout_w:
                    try:
                        img_px_w = float(logo_size) * float(layout_w)
                    except Exception:
                        img_px_w = None

                # Try to obtain image aspect using Pillow if available
                img_aspect = None
                try:
                    from PIL import Image as _PILImage
                    with _PILImage.open(logo_path) as _im:
                        iw, ih = _im.size
                        img_aspect = float(ih) / float(iw) if iw and ih else None
                except Exception:
                    img_aspect = None

                if img_px_w is not None and img_aspect is not None:
                    img_px_h = img_px_w * img_aspect
                elif img_px_w is not None:
                    # fallback to square if aspect unknown
                    img_px_h = img_px_w

                # Convert pixel sizes to paper fraction sizes (sizex, sizey)
                if layout_w and layout_h and img_px_w is not None and img_px_h is not None:
                    sizex = img_px_w / float(layout_w)
                    sizey = img_px_h / float(layout_h)
                else:
                    # fallback to using logo_size for both dimensions (fractional)
                    sizex = float(logo_size)
                    sizey = float(logo_size)

                # Compute desired position: pixel offsets from bottom-left of figure
                if layout_w and layout_h:
                    x_pos = float(logo_x_offset) / float(layout_w)
                    y_pos = float(logo_y_offset) / float(layout_h)
                else:
                    # fallback: interpret offsets as paper fractions if layout unknown
                    x_pos = float(logo_x_offset)
                    y_pos = float(logo_y_offset)

                # clamp to reasonable range (allow small negative y to place in margin)
                x_pos = max(-1.0, min(1.0, x_pos))
                y_pos = max(-1.0, min(1.0, y_pos))

                fig.add_layout_image(dict(
                    source=src,
                    xref="paper", yref="paper",
                    x=x_pos, y=y_pos,
                    xanchor="left", yanchor="bottom",
                    sizex=sizex, sizey=sizey,
                    sizing="contain",
                    opacity=float(logo_opacity),
                    layer="above"
                ))
            except Exception as e:
                print(f"Warning: could not add logo from '{logo_path}': {e}")

        return fig
    

if __name__ == "__main__":
    # Example usage
    watchlist = Watchlist()
    watchlist.load_watchlist()
    watchlist.get_watchlist_data(id_list = ["A85232558J", "A85232568L"])
    watchlist.save_watchlist()
