import os
import sys
import time
import signal
from typing import Union
import pandas as pd
import numpy as np
import re
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
from typing import Optional, Any, Mapping

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
    'original_source': ['original_source', 'originalSource', 'Source'],
    'source': ['source', 'data_source', 'provider', 'Source', 'original_source'],
    'description': ['description', 'notes', 'longBusinessSummary', 'table_title', 'indicator'],
    'start_date': ['start_date', 'observation_start', 'start_time', 'first_date', 'Start date', 'Series Start'],
    'end_date': ['end_date', 'observation_end', 'end_time', 'last_date', 'End date', 'Series End'],
    'last_updated': ['last_updated', 'lastUpdate', 'regularMarketTime', 'updated', 'pub_date', 'ReleaseDate', 'NextReleaseDate'],
    'min_value': ['min_value', 'minimum', 'min'],
    'max_value': ['max_value', 'maximum', 'max'],
    'length': ['length', 'count', 'observations', 'No. Obs.', 'No. Obs'],
    'units_short': ['units_short', 'unit_short', 'symbol', 'seasonal_adjustment_short', 'frequency_short'],
    'title': ['title', 'name', 'longName', 'shortName', 'label', 'shortname', 'series', 'Datasetname', 'TableName', 'metric_full'],
    'id': ['id', 'symbol', 'Ticker', 'Series ID', 'series_id', 'metric_short', 'path'],
    # Additional specialized fields that don't have direct CommonMetadata equivalents but could be useful
    'exchange': ['exchange', 'Exchange', 'exchDisp', 'fullExchange']
}

# Add the alias mapping as a class attribute
CommonMetadata.field_aliases = FIELD_ALIASES

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

    def load_watchlist(self, filepath: str = ""):
        """load_watchlist method. Loads a watchlist from an Excel file, with two sheets: 'watchlist' and 'all_metadata'.
        If no filepath is provided, a file dialog will open to allow the user to choose a file."""

        print("Loading watchlist from filepath: ", filepath)
        if len(filepath) == 0:
           filepath = qt_load_file_dialog(dialog_title="Choose a watchlist excel file.", initial_dir = self.watchlists_path, 
                                                   file_types = "Excel Files (*.xlsx)")
         
        if len(filepath) > 0:
            try:
                self['watchlist'] = pd.read_excel(filepath, index_col=0, sheet_name="watchlist")
                # FIX: Ensure metadata is loaded with object dtype to prevent datetime inference
                self['metadata'] = pd.read_excel(filepath, index_col=0, sheet_name="all_metadata", dtype=str)
                # Convert back to object dtype to handle mixed types properly
                self['metadata'] = self['metadata'].astype('object')
                self.name = filepath.split(fdel)[-1].split(".")[0]
                
                # ENHANCED DEBUG: Check the raw loaded data
                print(f"=== RAW DATA LOADED ===")
                print(f"Watchlist shape: {self['watchlist'].shape}")
                print(f"Watchlist columns: {self['watchlist'].columns.tolist()}")
                print(f"Source column type: {self['watchlist']['source'].dtype}")
                print(f"Source non-null count: {self['watchlist']['source'].notna().sum()}")
                print(f"Source null count: {self['watchlist']['source'].isna().sum()}")
                
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
        print(f"=== AFTER INDEX MANIPULATION ===")
        print(f"Watchlist shape: {self['watchlist'].shape}")
        print(f"Source non-null count: {self['watchlist']['source'].notna().sum()}")
        print(f"Source null count: {self['watchlist']['source'].isna().sum()}")

        current_index = self['watchlist'].index.tolist()
        meta_columns = self['metadata'].columns.tolist()
        print("Current watchlist index before any processing: ", current_index[:10])  # Show first 10
        print(f"Loaded watchlist shape: {self['watchlist'].shape}")

        # Check if corresponding .h5s file exists and restore original keys if needed
        if os.path.isfile(self.storepath):
            try:
                with pd.HDFStore(self.storepath, mode='r') as store:
                    # Load key mapping if it exists
                    if '/_key_mapping' in store.keys():
                        mapping_series = store['_key_mapping']
                        key_mapping = mapping_series.to_dict()
                        print(f"Loaded key mapping from HDF5 file with {len(key_mapping)} entries")
                        
                        # FIXED: Don't add duplicate rows - the original Excel watchlist is the source of truth
                        # The HDF5 key mapping should only be used for loading the dataset data, not modifying the watchlist
                        for idx in key_mapping.keys():  
                            original_key = key_mapping[idx]
                            # Only process metadata columns, not watchlist rows
                            if original_key in meta_columns and idx not in meta_columns:
                                pass
                            elif idx in meta_columns and original_key not in meta_columns:
                                self["metadata"][original_key] = self["metadata"][idx]
                                self["metadata"].drop(columns=[idx], axis=1, inplace=True)
                            elif idx in meta_columns and original_key in meta_columns:
                                # If both keys exist drop the duplicate
                                self["metadata"].drop(columns=[idx], axis=1, inplace=True)
                        
            except Exception as e:
                print(f"Could not load key mapping from HDF5 file: {e}")

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
        
        # ENHANCED DEBUG: Check after drop_data
        print(f"=== AFTER DROP_DATA ===")
        print(f"Watchlist shape: {self['watchlist'].shape}")
        print(f"Source non-null count: {self['watchlist']['source'].notna().sum()}")
        
        # FIXED: Only drop rows where "source" column has NaN values, not "title" column
        print(f"Shape before removing rows with NaN source: {self['watchlist'].shape}")
        print(f"Rows with NaN source values: {self['watchlist']['source'].isna().sum()}")
        
        # ENHANCED DEBUG: Show exactly which rows will be dropped
        rows_to_drop = self["watchlist"][self["watchlist"]["source"].isna()]
        if len(rows_to_drop) > 0:
            print("Rows that will be dropped due to NaN source:")
            print(rows_to_drop[['id', 'title', 'source']])
        
        # Only drop rows where source is NaN/null - keep rows where title is NaN but source is valid
        original_count = len(self["watchlist"])
        
        # ENHANCED: Let's see what the source column actually contains
        print("Source column unique values:")
        print(self["watchlist"]["source"].value_counts(dropna=False))
        
        # More specific filtering - check for actual NaN/None/empty values
        valid_source_mask = (
            self["watchlist"]["source"].notna() &  # Not NaN
            (self["watchlist"]["source"] != "") &   # Not empty string
            (self["watchlist"]["source"] != "nan") & # Not string "nan"
            (self["watchlist"]["source"] != "None")  # Not string "None"
        )
        
        self["watchlist"] = self["watchlist"][valid_source_mask]
        removed_count = original_count - len(self["watchlist"])
        
        print(f"Removed {removed_count} rows with missing source values")
        print(f"Final watchlist shape: {self['watchlist'].shape}")
        print(f"Remaining rows with NaN titles (which is OK): {self['watchlist']['title'].isna().sum()}")

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
        
        with pd.ExcelWriter(save_path) as writer:
            self['watchlist'].to_excel(writer, sheet_name='watchlist')
            metadata_for_excel.to_excel(writer, sheet_name='all_metadata')

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

    def timeout_handler(signum, frame):
        raise TimeoutError("Data pull timed out")

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
        meta = pd.DataFrame()  #Use empty df to put the common metadata in
        #print("Watchlist: \n", watchlist, "\n\nMetadata: \n", meta)

        #Then get the data....
        data = {}
        if id_list is None:
            # If no id_list is provided, use all ids in the watchlist
            ids = watchlist["id"].to_list() if len(watchlist["id"]) > len(watchlist.index) else watchlist.index.to_list()
            # can a column have a greater length than the index? Yes, if there are duplicate index values
        else:
            ids = id_list
      
        for i in ids:
            sauce = str(watchlist.loc[i, "source"]).strip()
            eyed = str(watchlist.loc[i, "id"]).strip()
            try:
                exchag = str(meta.loc["exchange", i]).strip()
            except:
                exchag = None
            print(f"Attempting data pull for series id: {eyed}, from source: {sauce},\n start_date: {start_date}), exchange_code: {exchag}")
            
            # Set up timeout for this data pull
            signal.signal(signal.SIGALRM, self.timeout_handler)
            signal.alarm(timeout)
            
            # Initialize variables for this iteration
            series_meta = None
            ds_data = None
            
            try:
                ds = Pull_Data.dataset()
                ds.get_data(sauce, eyed, start_date, exchange_code = exchag, timeout=timeout)
                data[watchlist.loc[i,"id"]] = ds.data
                series_meta = ds.SeriesInfo
                ds_data = ds.data

                print(f"Data pull successful for {watchlist.loc[i,'id']} from {watchlist.loc[i,'source']}.")
                signal.alarm(0)  # Cancel the alarm

            except TimeoutError:
                print(f"Timeout ({timeout}s) exceeded for {watchlist.loc[i,'id']} from {watchlist.loc[i,'source']}. Skipping...")
                data[watchlist.loc[i,"id"]] = pd.Series([f"Data pull timed out after {timeout} seconds.", "Timeout exceeded", 
                                                        f"Source: {sauce}"], name="Timeout_"+watchlist.loc[i,"id"], index = [0, 1, 2])
                signal.alarm(0)  # Cancel the alarm
                continue  # Skip metadata processing for failed pulls
        
            except Exception as e:
                print(f"Error pulling data for {watchlist.loc[i,'id']} from {watchlist.loc[i,'source']}. Exception: {e}")
                data[watchlist.loc[i,"id"]] = pd.Series(["Data pull failed for this series.", "Devo bro....",
                                                        "Error messsage: "+str(e)], name="Error_"+watchlist.loc[i,"id"], index = [0, 1, 2])
                signal.alarm(0)  # Cancel the alarm
                continue  # Skip metadata processing for failed pulls

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

                    # Concatenate the common metadata as columns (axis=1) ensuring proper orientation
                    common_series = common.to_series()
                    common_series.name = eyed  # Ensure proper column name
                    meta = pd.concat([meta, common_series], axis=1)
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
                    print("Your metadata series is a DataFrame, reducing to a Series.... Have a look at it first: \n", series)
                    if len(series.columns) == 1:
                        series = series.squeeze()
                    else:
                        print("Skipping this series, it is a DataFrame with more than one column, should be a series with metadata,", series.columns)
                        continue
            
                # Get the title from metadata, use series.name or key as fallback
                try:
                    metadata_title = self["metadata"].loc["title", key]
                    if pd.isna(metadata_title) or metadata_title == "" or metadata_title is None:
                        # Use series name if available, otherwise use the key
                        title = series.name if series.name is not None and series.name != "" else key
                        print(f"Title was NaN/empty for {key}, using fallback title: {title}")
                    else:
                        title = metadata_title
                except (KeyError, IndexError):
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

                start_date = series.index[0] if series is not None else np.nan
                end_date = series.index[-1] if series is not None else np.nan
                self["watchlist_datasets"][key] = series

                #Update the watchlist with improved metadata as well as the metadata DataFrame
                self["watchlist"].loc[key, "id"] = key
                
                # Fix Warning 1: Ensure title column is object dtype before assignment
                if "title" not in self["watchlist"].columns:
                    self["watchlist"]["title"] = ""
                self["watchlist"]["title"] = self["watchlist"]["title"].astype('object')
                self["watchlist"].loc[key, "title"] = str(title)  # Explicitly convert to string
                
                # Update metadata with the title if it was missing or NaN
                if key in self["metadata"].columns:
                    if pd.isna(self["metadata"].loc["title", key]) or self["metadata"].loc["title", key] == "":
                        self["metadata"].loc["title", key] = str(title)  # Explicitly convert to string
                        try:
                            # Ensure observation_start and observation_end rows exist
                            for row_name in ["observation_start", "observation_end"]:
                                if row_name not in self["metadata"].index:
                                    # Create a new row with object dtype and fill with empty strings
                                    new_row = pd.Series([''] * len(self["metadata"].columns), 
                                                      index=self["metadata"].columns, 
                                                      name=row_name, 
                                                      dtype=object)
                                    # Use pd.concat to add the new row
                                    new_row_df = new_row.to_frame().T
                                    self["metadata"] = pd.concat([self["metadata"], new_row_df], ignore_index=False)
                            
                            # Ensure the entire metadata DataFrame is object dtype
                            self["metadata"] = self["metadata"].astype('object')
                            
                            # Now safely assign the date values
                            if key in self["metadata"].columns and pd.notna(self["metadata"].loc["observation_start", key]):
                                self["metadata"].loc["observation_start", key] = str(start_date)
                                self["metadata"].loc["observation_end", key] = str(end_date)
                            else:
                                self["metadata"].loc["observation_start", key] = str(start_date)
                                self["metadata"].loc["observation_end", key] = str(end_date)
                        except Exception as e:
                            print(f"Error setting observation dates for {key}: {e}")

                # Also set the title in the watchlist 
                self["watchlist"].loc[key, "title"] = str(title)
                
                # FIX: Handle frequency metadata assignment with proper dtype management
                if key in self["metadata"].columns and "frequency" in self["metadata"].index and pd.notna(self["metadata"].loc["frequency", key]):
                    pass
                else:
                    try:
                        freq = Utilities.freqDetermination(series)
                        freq.DetermineSeries_Frequency()
                    
                        # Ensure frequency rows exist and are object dtype
                        if "frequency" not in self["metadata"].index:
                            # Initialize the metadata with proper object dtype if needed
                            if self["metadata"].empty:
                                self["metadata"] = pd.DataFrame(dtype=object)
                            
                            # Create a new row with object dtype and fill with empty strings
                            new_row = pd.Series([''] * len(self["metadata"].columns), 
                                                index=self["metadata"].columns, 
                                                name="frequency", 
                                                dtype=object)
                            # Use pd.concat to add the new row
                            new_row_df = new_row.to_frame().T
                            self["metadata"] = pd.concat([self["metadata"], new_row_df], ignore_index=False)
                        
                        if "frequency_short" not in self["metadata"].index:
                            # Create a new row with object dtype and fill with empty strings
                            new_row = pd.Series([''] * len(self["metadata"].columns), 
                                                index=self["metadata"].columns, 
                                                name="frequency_short", 
                                                dtype=object)
                            # Use pd.concat to add the new row
                            new_row_df = new_row.to_frame().T
                            self["metadata"] = pd.concat([self["metadata"], new_row_df], ignore_index=False)
                        
                        # Ensure the entire metadata DataFrame is object dtype
                        self["metadata"] = self["metadata"].astype('object')
                        
                        # Now safely assign the frequency values
                        self["metadata"].loc["frequency", key] = str(freq.frequency)
                        self["metadata"].loc["frequency_short", key] = str(freq.frequency[0])
                        
                    except Exception as e:
                        print("Error determining frequency for series: ", key, ". Exception: ", e)
                        
                        # Ensure frequency rows exist with object dtype before assigning fallback values
                        if "frequency" not in self["metadata"].index:
                            if self["metadata"].empty:
                                self["metadata"] = pd.DataFrame(dtype=object)
                            new_row = pd.Series([''] * len(self["metadata"].columns), 
                                                index=self["metadata"].columns, 
                                                name="frequency", 
                                                dtype=object)
                            new_row_df = new_row.to_frame().T
                            self["metadata"] = pd.concat([self["metadata"], new_row_df], ignore_index=False)
                        
                        if "frequency_short" not in self["metadata"].index:
                            new_row = pd.Series([''] * len(self["metadata"].columns), 
                                                index=self["metadata"].columns, 
                                                name="frequency_short", 
                                                dtype=object)
                            new_row_df = new_row.to_frame().T
                            self["metadata"] = pd.concat([self["metadata"], new_row_df], ignore_index=False)
                        
                        # Ensure the entire metadata DataFrame is object dtype
                        self["metadata"] = self["metadata"].astype('object')
                        
                        # Now safely assign fallback values as strings
                        self["metadata"].loc["frequency", key] = "Unknown"
                        self["metadata"].loc["frequency_short", key] = "U"
        else:
            print("Download datasets for the watchlist first using get_watchlist_data() or load_watchlist_data() methods.....")
            return

    def load_watchlist_data(self, ask_input: bool = False):
        """load_watchlist_data method.
        This function loads the watchlist data from a .h5s database file. The data is stored in the 'watchlist_datasets' dictionary.
        This can be run as an alternative to get_wtaclist_data, if the data has already been pulled and saved to a .h5s file."""

        print("Database filepath: ", self.storepath)
        if self.storepath is not None and os.path.isfile(self.storepath):
            with pd.HDFStore(self.storepath, mode='a') as data:
                #print("Database keys: ", data.keys())
                
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
                    self['watchlist_datasets'][original_key] = data[sanitized_key]
                
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
        
        print("Loaded database from .h5s file, keys: ", self["watchlist_datasets"].keys())

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
            #print("Final index/columns watchlist/metadata: ", self["watchlist"].index, self["metadata"].columns)

    def plot_watchlist(self, left: list, right: list, template: str = "plotly_white"):
        """
        Plot selected datasets in this watchlist on a dual-axis chart.

        Parameters:
        - left: list of ids (strings) to plot on the left axis (primary)
        - right: list of ids (strings) to plot on the right axis (secondary)
        """
        if not self.get("watchlist_datasets"):
            print("No datasets loaded. Use get_watchlist_data() or load_watchlist_data() first.")
            return None

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
                    title = self["watchlist"].loc[did, "title"]
                    if pd.isna(title) or title is None or title == "":
                        title = did
                except Exception:
                    title = did
                out[str(title)] = ser
            return out

        # De-duplicate ids if any appear in both lists (prefer right axis)
        left_ids = [i for i in (left or []) if i not in (right or [])]
        right_ids = right or []

        primary_data = build_series_map(left_ids)
        secondary_data = build_series_map(right_ids)

        if not primary_data and not secondary_data:
            print("Nothing to plot. Check the ids provided.")
            return None

        title = self.name if hasattr(self, "name") and self.name else "Watchlist Plot"
        fig = charting_plotly.dual_axis_basic_plot(primary_data, secondary_data=secondary_data, title=title, template=template)
        return fig
    

if __name__ == "__main__":
    # Example usage
    watchlist = Watchlist()
    watchlist.load_watchlist()
    print(watchlist["watchlist"])
