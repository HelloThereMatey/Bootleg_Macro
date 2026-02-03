<<<<<<< HEAD
"""
ABS and RBA Data Retrieval Module

This module provides functions for downloading and processing time series data from:
1. Australian Bureau of Statistics (ABS) - using Python readabs package or R fallback
2. Reserve Bank of Australia (RBA) - using R readrba package

Functions:
----------
ABS Data (Python - Preferred):
    get_abs_series_python(series_id, catalog_num, verbose) -> (pd.Series, pd.Series)
        Download ABS data using Python readabs package
        
ABS Data (R - Legacy):
    get_abs_series_from_excel(excel_file_path, series_id, verbose) -> (pd.Series, pd.Series)
        Extract ABS series from Excel file
    abs_download_with_r(series_id, save_path, r_script_path) -> str
        Download ABS data using R script (returns Excel file path)

RBA Data (R only):
    browse_rba_tables(searchterm) -> pd.DataFrame
        Search RBA tables by keyword
    browse_rba_series(searchterm) -> pd.DataFrame
        Search RBA series by keyword
    get_rba_series(series_id, save_path) -> pd.DataFrame
        Download RBA series data

Helper Functions:
    find_header_end(index) -> int
        Find where header ends in ABS Excel files
"""

import os
import shutil
import pandas as pd
import subprocess
import json
from typing import Tuple, Optional


def find_header_end(index) -> int:
    """
    Find the row where actual data begins in ABS Excel files.
    
    Parameters:
    -----------
    index : pd.Index
        Index from the Excel file
        
    Returns:
    --------
    int : Row number where data starts (first valid datetime)
    """
    for i, val in enumerate(index):
        if pd.to_datetime(val, errors='coerce') is not pd.NaT:
            return i
    return 9  # Fallback


# ============================================================================
# ABS FUNCTIONS - PYTHON READABS (PREFERRED)
# ============================================================================

def get_abs_series_python(
    series_id: str, 
    catalog_num: Optional[str] = None, 
    verbose: bool = False
) -> Tuple[pd.Series, pd.Series]:
    """
    Download ABS series using Python readabs package.
    
    This is the preferred method as it avoids R dependency issues.
    
    Parameters:
    -----------
    series_id : str
        ABS series ID (e.g., "A84423050A")
    catalog_num : str
        ABS catalog number (e.g., "6202.0" for Labour Force)
    verbose : bool
        Print debug information
        
    Returns:
    --------
    Tuple[pd.Series, pd.Series]
        (data_series, metadata_series)
        
    Raises:
    -------
    ValueError : If series not found or catalog_num not provided
    ImportError : If readabs_py module not available
    """
    try:
        from . import readabs_py
    except ImportError:
        raise ImportError(
            "readabs_py module not found. Ensure readabs_py.py exists in the same directory."
        )
    
    if not series_id:
        raise ValueError("series_id must be provided")
    
    if verbose:
        print(f"[Python] Getting ABS series {series_id} from catalog {catalog_num}")
    
    data_series, metadata_series = readabs_py.get_series_by_id(
        series_id=series_id,
        catalog_num=catalog_num,
        verbose=verbose,
        cache_only=False
    )
    
    if data_series is None:
        raise ValueError(f"Could not retrieve series {series_id} from catalog {catalog_num}")
    
    if verbose:
        print(f"[Python] Successfully retrieved {series_id}, shape: {data_series.shape}")
    
    return data_series, metadata_series


# ============================================================================
# ABS FUNCTIONS - R FALLBACK (LEGACY)
# ============================================================================

def abs_download_with_r(
    series_id: str,
    save_path: Optional[str] = None,
    r_script_path: Optional[str] = None
) -> tuple[pd.Series, pd.Series]:
    """
    Download ABS series using R script (legacy method).
    
    Parameters:
    -----------
    series_id : str
        ABS series ID
    save_path : str, optional
        Directory to save Excel file. Defaults to User_Data/ABS/LastPull
    r_script_path : str, optional
        Path to R script. Defaults to abs_get_series.r in this directory
        
    Returns:
    --------
    str : Full path to downloaded Excel file
    
    Raises:
    -------
    ValueError : If series_id not provided or R script errors
    FileNotFoundError : If R script not found
    """
    if not series_id:
        raise ValueError("series_id must be provided")
    
    # Set default paths
    if save_path is None:
        module_dir = os.path.dirname(__file__)
        project_root = os.path.dirname(os.path.dirname(module_dir))
        save_path = os.path.join(project_root, "User_Data", "ABS", "LastPull")
    
    if r_script_path is None:
        r_script_path = os.path.join(os.path.dirname(__file__), 'abs_get_series.r')
    
    if not os.path.isfile(r_script_path):
        raise FileNotFoundError(f"R script not found: {r_script_path}")
    
    # Run R script
    input_string = f"{series_id},{save_path}"
    process = subprocess.run(
        ['Rscript', r_script_path, input_string],
        capture_output=True, 
        text=True
    )
    
    output = process.stdout.strip()
    
    if output.startswith("ERROR"):
        raise ValueError(f"R script error: {output}")
   
    print(f"[R] Downloaded series {series_id} to: {output}")

    #This function will get the data series and series info from the excel file
    data_series, metadata_series = get_abs_series_from_excel(excel_file_path=output, series_id=series_id, verbose=True)   

    return data_series, metadata_series


def get_abs_series_from_excel(
    excel_file_path: str,
    series_id: str,
    verbose: bool = False
) -> Tuple[pd.Series, pd.Series]:
    """
    Extract ABS series from Excel file.
    
    Reads ABS Excel file, finds the specified series, extracts data and metadata.
    Also manages file copying to Full_Sheets directory and cleanup of LastPull.
    
    Parameters:
    -----------
    excel_file_path : str
        Path to ABS Excel file
    series_id : str
        Series ID to extract from file
    verbose : bool
        Print debug information
        
    Returns:
    --------
    Tuple[pd.Series, pd.Series]
        (data_series, metadata_series)
        
    Raises:
    -------
    FileNotFoundError : If Excel file doesn't exist
    ValueError : If series_id not found in file
    """
    if not os.path.isfile(excel_file_path):
        raise FileNotFoundError(f"Excel file not found: {excel_file_path}")
    
    if verbose:
        print(f"[Excel] Reading {excel_file_path}")
        print(f"[Excel] Looking for series: {series_id}")
    
    # Load all sheets
    all_data = pd.read_excel(excel_file_path, sheet_name=None, index_col=0)
    data_sheets = [sheet for sheet in all_data.keys() if "Data" in sheet]
    
    # Find series in data sheets
    column_found = False
    column_index = None
    
    for data_sheet in data_sheets:
        data = all_data[data_sheet]
        
        findcol = data.columns[data.isin([series_id]).any()]
        if findcol.empty:
            continue
        
        column = findcol[0]
        try:
            column_index = data.columns.get_loc(column)
            column_found = True
            if verbose:
                print(f"[Excel] Found {series_id} in column {column_index} (name: '{column}')")
            break
        except KeyError as e:
            if verbose:
                print(f"[Excel] Warning: Column '{column}' error: {e}")
            continue
    
    if not column_found or column_index is None:
        raise ValueError(f"Series ID '{series_id}' not found in any data sheets")
    
    # Extract series
    series = data.iloc[:, column_index]
    
    # File management
    _manage_abs_file_storage(excel_file_path, verbose)
    
    # Parse series data
    start_index = find_header_end(series.index)
    metadata_raw = series.iloc[:start_index]
    series_data = series.iloc[start_index:]
    
    # Create time series
    index = pd.to_datetime(series_data.index).date
    series_name = column.replace(".", "")
    
    data_series = pd.Series(
        series_data.to_list(), 
        index=pd.DatetimeIndex(index), 
        name=series_name
    )
    
    # Create metadata series
    metadata_series = metadata_raw.copy().astype('object')
    metadata_series.name = series_id
    
    if 'title' not in metadata_series.index:
        metadata_series['title'] = series_name
    elif len(str(metadata_series['title'])) < len(series_name):
        metadata_series['title'] = series_name
    
    if verbose:
        print(f"[Excel] Created series '{series_name}' with {len(data_series)} observations")
    
    return data_series, metadata_series


def _manage_abs_file_storage(excel_file_path: str, verbose: bool = False):
    """
    Copy Excel file to Full_Sheets and clean up LastPull directory.
    
    Internal helper function for file management.
    """
    try:
        module_dir = os.path.dirname(__file__)
        project_root = os.path.dirname(os.path.dirname(module_dir))
        
        # Copy to Full_Sheets
        dest_dir = os.path.join(project_root, "User_Data", "ABS", "Full_Sheets")
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, os.path.basename(excel_file_path))
        
        if os.path.abspath(excel_file_path) != os.path.abspath(dest_path):
            shutil.copy2(excel_file_path, dest_path)
            if verbose:
                print(f"[File] Copied to Full_Sheets: {dest_path}")
        
        # Clean up LastPull directory
        last_pull_dir = os.path.join(project_root, "User_Data", "ABS", "LastPull")
        current_file = os.path.basename(excel_file_path)
=======
from operator import index
import os
fdel = os.path.sep
wd = os.path.dirname(__file__)  ## This gets the working directory which is the folder where you have placed this .py file. 
parent = os.path.dirname(wd); grampa = os.path.dirname(parent)
import shutil

import re
import pandas as pd
import subprocess
import json
from pprint import pprint

def find_header_end(index) -> int:
    for i, val in enumerate(index):
        if pd.to_datetime(val, errors='coerce') is not pd.NaT:
            return i
    return 9  # Fallback to original if no date found

# Path to the Rscript executable
# You might need to specify the full path if Rscript is not in the PATH
r_script_path = wd+fdel+'abs_get_series.r'
r_executable_path = 'Rscript'  # Or specify path like '/usr/local/bin/Rscript'
abs_path = grampa+fdel+"User_Data"+fdel+"ABS"+fdel+"LastPull"

# Default input for the R script, here we want series_ID for the ABS series,savePath,
series_id = "A2302476C"

def abs_get_series(series_id: str = None, abs_path: str = abs_path):
    """ USES R Script to use read_abs package to download a data table from ABS & save to an excel file"""
    input_string = series_id + "," + abs_path

    # Run the R script
    process = subprocess.run([r_executable_path, r_script_path, input_string],
                            capture_output=True, text=True)

    # Capture the output (now the full file path)
    output = process.stdout.strip()
    print("R output:", output)

    # Check for errors in R output
    if output.startswith("ERROR"):
        raise ValueError(f"R script error: {output}")

    # Use the full file path directly (no need for table_name or regex)
    excel_file_path = output
    print(f"Data table containing series id {series_id} downloaded and saved to: \n{excel_file_path}")
    return excel_file_path

def get_abs_series_r(excel_file_path: str = None, series_id: str = "A2302476C") -> tuple[pd.Series, pd.Series]:
    """ USES R Script to use read_abs package to download a data table from ABS & save to an excel file"""

    if excel_file_path is None and series_id is not None: 
        excel_file_path = abs_get_series(series_id = series_id)
    # Verify the file exists
    if not os.path.isfile(excel_file_path):
        raise FileNotFoundError(f"Excel file not found at: {excel_file_path}")

    # Load the data (rest of your code remains similar)
    all_data = pd.read_excel(excel_file_path, sheet_name=None, index_col=0)
    data_sheets = [sheet for sheet in all_data.keys() if "Data" in sheet]
    column_found = False

    for data_sheet in data_sheets:
        data = all_data[data_sheet]
        #data.columns = data.columns.str.replace(";", "").str.strip()  # Clean semicolons and spaces as before
        all_data[data_sheet] = data
        
        # Find columns containing the series_id (existing logic)
        findcol = data.columns[data.isin([series_id]).any()]
        if findcol.empty:
            continue
        else:
            # Get the string name of the first matching column (for logging/debugging)
            column = findcol[0]
            
            # NEW: Get the integer index (iloc) of the column for reliable selection
            try:
                column_index = data.columns.get_loc(column)  # This gives the positional index
                column_found = True
                print(f"Series ID '{series_id}' found in column at index {column_index} (name: '{column}')")
                break  # Stop after finding the first match
            except KeyError as e:
                print(f"Warning: Could not get location for column '{column}' due to: {e}. Skipping sheet.")
                continue

    if not column_found or column_index is None:
        raise ValueError(f"Series ID: {series_id} not found in any data sheets.")

    # MODIFIED: Use iloc to select the column by index instead of string name
    series = data.iloc[:, column_index]

    # When copying the file, use the full path
    # Ensure destination folder exists and avoid copying if source and destination are identical
    try:
        dest_dir = os.path.join(grampa, "User_Data", "ABS", "Full_Sheets")
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, os.path.basename(excel_file_path))

        # If source and destination are the same file, skip copy to avoid shutil.SameFileError
        if os.path.abspath(excel_file_path) == os.path.abspath(dest_path):
            print(f"Source file is already in Full_Sheets ({dest_path}); skipping copy.")
        else:
            try:
                shutil.copy2(excel_file_path, dest_path)
                print(f"Copied file to Full_Sheets: {dest_path}")
            except shutil.SameFileError:
                # Defensive: should be handled by path check above, but catch just in case
                print("Source and destination are the same file; skipping copy.")
            except Exception as e:
                print(f"Warning: could not copy file to Full_Sheets: {e}")
    except Exception as e:
        print(f"Warning: error preparing Full_Sheets copy: {e}")
    
    # NEW: Clean up the "LastPull" directory - delete all files except the current one
    try:
        last_pull_dir = abs_path  # This is the "LastPull" directory
        current_file = os.path.basename(excel_file_path)  # Name of the newly downloaded file
>>>>>>> origin/liquidityRevamp
        
        if os.path.exists(last_pull_dir):
            for file_name in os.listdir(last_pull_dir):
                file_path = os.path.join(last_pull_dir, file_name)
<<<<<<< HEAD
                if os.path.isfile(file_path) and file_name != current_file:
                    os.remove(file_path)
                    if verbose:
                        print(f"[File] Deleted old file: {file_name}")
    
    except Exception as e:
        if verbose:
            print(f"[File] Warning during file management: {e}")


# ============================================================================
# RBA FUNCTIONS (R ONLY)
# ============================================================================

def browse_rba_tables(searchterm: str = "rate") -> pd.DataFrame:
    """
    Search RBA tables by keyword using R readrba package.
    
    Parameters:
    -----------
    searchterm : str
        Keyword to search for in table names/descriptions
        
    Returns:
    --------
    pd.DataFrame : Matching RBA tables
    """
    module_dir = os.path.dirname(__file__)
    rba_script_path = os.path.join(module_dir, "read_rba.r")
    
=======
                # Only delete if it's a file and not the current one
                if os.path.isfile(file_path) and file_name != current_file:
                    os.remove(file_path)
                    print(f"Deleted old file from LastPull: {file_name}")
        else:
            print(f"Warning: LastPull directory does not exist: {last_pull_dir}")
    except Exception as e:
        print(f"Warning: Could not clean up LastPull directory: {e}")

    # Use the new function to find where the header ends
    start_index = find_header_end(series.index)
    SeriesInfo = series.iloc[:start_index]
    series = series.iloc[start_index:]
    index = pd.to_datetime(series.index).date
    
    # Enhanced series name handling - use the actual column title as the series name
    seriesName = column.replace(".", "")  # Clean up the name but preserve the descriptive title
    the_series = pd.Series(series.to_list(), index = pd.DatetimeIndex(index), name = seriesName)
    
    # Enhanced SeriesInfo to include the proper title and ensure object dtype
    SeriesInfo = SeriesInfo.copy().astype('object')  # Ensure object dtype
    SeriesInfo.name = series_id  # Ensure SeriesInfo has the series_id as its name
    if 'title' not in SeriesInfo.index:
        SeriesInfo['title'] = seriesName  # Add the descriptive title to SeriesInfo
    else:
        # Update existing title if it's less descriptive than the column name
        if len(str(SeriesInfo['title'])) < len(seriesName):
            SeriesInfo['title'] = seriesName
    
    print(f"ABS series created with name: {seriesName}")

    return the_series, SeriesInfo

def browse_rba_tables_r(searchterm: str = "rate") -> pd.DataFrame:
>>>>>>> origin/liquidityRevamp
    input_dict = {
        "function": "browse_tables",
        "searchterm": searchterm
    }
<<<<<<< HEAD
    
    process = subprocess.run(
        ['Rscript', rba_script_path, json.dumps(input_dict)],
        capture_output=True, 
        text=True
    )
    
    output = process.stdout.strip()
    print(f"\n[RBA] Browse tables results:\n{output}\n")
    
    try:
        json_data = json.loads(output)
        df = pd.DataFrame(json_data)
        print(f"[RBA] Columns: {df.columns.tolist()}")
        return df
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to decode R output: {e}")


def browse_rba_series(searchterm: str = "rate") -> pd.DataFrame:
    """
    Search RBA series by keyword using R readrba package.
    
    Parameters:
    -----------
    searchterm : str
        Keyword to search for in series names/descriptions
        
    Returns:
    --------
    pd.DataFrame : Matching RBA series with columns renamed to 'id' and 'title'
    """
    module_dir = os.path.dirname(__file__)
    rba_script_path = os.path.join(module_dir, "read_rba.r")
    
=======
    input_string = json.dumps(input_dict)

    rba_script_path = wd + fdel + "read_rba.r"
    process = subprocess.run([r_executable_path, rba_script_path, input_string],
                             capture_output=True, text=True)

    output = str(process.stdout).strip()
    print("\nOutput from R browse RBA tables:\n", output, "\n\n")

    try:
        json_data = json.loads(output)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to decode JSON: {e}")
    df = pd.DataFrame(json_data)
    print("Columns in the dataframe search result: ", df.columns)
    return df

def browse_rba_series_r(searchterm: str = "rate") -> pd.DataFrame:
>>>>>>> origin/liquidityRevamp
    input_dict = {
        "function": "browse_series",
        "searchterm": searchterm
    }
<<<<<<< HEAD
    
    process = subprocess.run(
        ['Rscript', rba_script_path, json.dumps(input_dict)],
        capture_output=True, 
        text=True
    )
    
    output = process.stdout.strip()
    
    try:
        json_data = json.loads(output)
        df = pd.DataFrame(json_data).rename(
            columns={"series_id": "id", "table_title": "title"}
        )
        print(f"[RBA] Columns: {df.columns.tolist()}")
        return df
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to decode R output: {e}")


def get_rba_series(
    series_id: str, 
    save_path: Optional[str] = None,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Download RBA series data using R readrba package.
    
    Parameters:
    -----------
    series_id : str
        RBA series ID (e.g., "FIRMMCRTD")
    save_path : str, optional
        Directory to save data. Defaults to User_Data/RBA
        
    Returns:
    --------
    pd.DataFrame : RBA series data
    """
    if save_path is None:
        module_dir = os.path.dirname(__file__)
        project_root = os.path.dirname(os.path.dirname(module_dir))
        save_path = os.path.join(project_root, "User_Data", "RBA")
    
    module_dir = os.path.dirname(__file__)
    rba_script_path = os.path.join(module_dir, "read_rba.r")
    
    input_dict = {
        "function": "get_series",
        "series_id": series_id,
        "rba_path": save_path
    }
    
    process = subprocess.run(
        ['Rscript', rba_script_path, json.dumps(input_dict)],
        capture_output=True, 
        text=True
    )
    
    output = process.stdout.strip()

    if verbose:
        print(f"\n[RBA] {output}\n")
    
    try:
        json_data = json.loads(output)
        return pd.DataFrame(json_data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to decode R output: {e}")


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Testing ABS/RBA Data Retrieval Functions")
    print("=" * 70)
    
    # Test 1: Python readabs (preferred)
    print("\n[Test 1] Python readabs method:")
    try:
        data, meta = get_abs_series_python(
            series_id="A84423050A",
            catalog_num="6202.0",
            verbose=True
        )
        print(f"✓ Success! Data shape: {data.shape}\n")
    except Exception as e:
        print(f"✗ Failed: {e}\n")
    
    # Test 2: Excel file extraction
    print("\n[Test 2] Extract from Excel file:")
    try:
        test_file = "/Users/jamesbishop/Documents/Python/Bootleg_Macro/User_Data/ABS/Full_Sheets/340101.xlsx"
        if os.path.exists(test_file):
            data, meta = get_abs_series_from_excel(
                excel_file_path=test_file,
                series_id='A85232568L',
                verbose=True
            )
            print(f"✓ Success! Data shape: {data.shape}\n")
        else:
            print(f"✗ Test file not found: {test_file}\n")
    except Exception as e:
        print(f"✗ Failed: {e}\n")
    
    # Test 3: RBA series
    print("\n[Test 3] RBA series retrieval:")
    try:
        rba_data = get_rba_series(series_id="FIRMMCRTD")
        print(f"✓ Success! RBA data shape: {rba_data.shape}\n")
    except Exception as e:
        print(f"✗ Failed: {e}\n")
    
    print("=" * 70)
=======
    input_string = json.dumps(input_dict)

    rba_script_path = wd + fdel + "read_rba.r"
    process = subprocess.run([r_executable_path, rba_script_path, input_string],
                             capture_output=True, text=True)

    output = str(process.stdout).strip()
    #print("\nOutput from R browse RBA series:\n", output, "\n\n")
    try:
        json_data = json.loads(output)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to decode JSON: {e}")
    df = pd.DataFrame(json_data).rename(columns={"series_id": "id", "table_title": "title"})
    print("Columns in the dataframe search result: ", df.columns)
    return df

def get_rba_series_r(series_id: str = "FIRMMCRTD", rba_path: str = grampa+fdel+"User_Data"+fdel+"RBA") -> pd.DataFrame:
    input_dict = {
        "function": "get_series",
        "series_id": series_id,
        "rba_path": rba_path}
    
    input_string = json.dumps(input_dict)

    rba_script_path = wd + fdel + "read_rba.r"
    process = subprocess.run([r_executable_path, rba_script_path, input_string],
                             capture_output=True, text=True)

    output = str(process.stdout).strip()
    print("\n\n", output, "\n\n")
    json_data = json.loads(output)
    df = pd.DataFrame(json_data)
    return df

if __name__ == "__main__":
    search = get_rba_series_r()
    print(search)

    arrivals = get_abs_series_r(excel_file_path="/Users/jamesbishop/Documents/Python/Bootleg_Macro/User_Data/ABS/Full_Sheets/340101.xlsx",
                                                                     series_id = 'A85232568L')
    
    print(arrivals)
>>>>>>> origin/liquidityRevamp

