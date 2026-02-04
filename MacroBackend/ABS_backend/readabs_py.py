"""
Python readabs backend for downloading ABS and RBA data series.

This module provides a Python-based interface to the ABS and RBA data using the Python
readabs package, replacing the R-based implementation that had issues with series
ID handling.

Main ABS functions:
- search_series_by_id(): Search for a series by its ABS series ID
- search_series_by_catalog(): Search for series within a catalog number
- get_series_metadata(): Retrieve metadata for a series
- download_series_data(): Download data for a specific series
- get_series_by_id(): High-level function to get series data and metadata by ID

Main RBA functions:
- get_rba_catalogue(): Get RBA catalogue of available tables
- browse_rba_tables(): Search RBA tables by keyword
- browse_rba_series(): Search RBA series within tables by keyword
- get_rba_series(): Download RBA series data by series ID
"""

import os
import sys
import pandas as pd
from typing import Optional, Tuple, Dict, Any
import readabs as ra

wd = os.path.dirname(os.path.abspath(__file__))
fdel = os.sep
parent = os.path.dirname(wd); grampa = os.path.dirname(parent)

sys.path.append(grampa)  # Adds MacroBackend to path

from MacroBackend.Utilities import Search_DF_np


def search_series_by_id(series_id: str, catnum: Optional[float] =  None, verbose: bool = False) -> Optional[Dict[str, Any]]:
    """
    Search for metadata of a specific ABS series by its series ID.
    
    Parameters:
    ----------
    series_id : str
        The ABS series ID (e.g., "A2326481T")
    verbose : bool
        Print debug information if True
        
    Returns:
    --------
    Dict[str, Any] or None
        Dictionary containing series metadata, or None if not found
    """
    try:
        if verbose:
            print(f"Searching for series ID: {series_id}")
        
        # Get the ABS catalogue to search metadata
        catalogue = ra.abs_catalogue(cache_only=False, verbose=verbose)
        
        if catalogue is None or catalogue.empty:
            print("No catalogue number supplied, we will search through all available catalogs, this'll take some time...")
            for catnum in catalogue.index:
                data_dict, metadata_df = ra.read_abs_cat(cat=catnum, verbose=verbose)
                series_mask = metadata_df['series_id'].astype(str) == series_id
                if series_mask.any():
                    return metadata_df[series_mask].iloc[0].to_dict()

    
    except Exception as e:
        print(f"Error searching for series {series_id}: {e}")
        return None


def search_series_by_catalog(
    catalog_num: str, 
    search_terms: Optional[Dict[str, str]] = None,
    verbose: bool = False
) -> Optional[pd.DataFrame]:
    """
    Search for series within an ABS catalog by search terms.
    
    Parameters:
    -----------
    catalog_num : str
        The ABS catalog number (e.g., "6202.0")
    search_terms : Dict[str, str], optional
        Dictionary of search terms to filter series
    verbose : bool
        Print debug information if True
        
    Returns:
    --------
    pd.DataFrame or None
        DataFrame with matching series, or None if none found
    """
    try:
        if verbose:
            print(f"Searching catalog {catalog_num}")
        
        # Read the entire catalog
        data_dict, metadata_df = ra.read_abs_cat(cat=catalog_num, verbose=verbose)
        
        if search_terms is None:
            return metadata_df
        
        # Filter metadata by search terms
        filtered = metadata_df.copy()
        for column, term in search_terms.items():
            if column in filtered.columns:
                filtered = filtered[filtered[column].astype(str).str.contains(term, case=False, na=False)]
        
        return filtered if len(filtered) > 0 else None
    
    except Exception as e:
        print(f"Error searching catalog {catalog_num}: {e}")
        return None


def get_series_metadata(
    series_id: str,
    catalog_num: str = None,
    return_dict: bool = False,
    verbose: bool = False
) -> Optional[pd.Series]:
    """
    Get metadata for a specific series within a catalog.
    
    Parameters:
    -----------
    catalog_num : str
        The ABS catalog number
    series_id : str
        The ABS series ID
    verbose : bool
        Print debug information if True
        
    Returns:
    --------
    pd.Series or None
        Series containing metadata for the specified series
    """

    if catalog_num is None:
        catalog_num = get_catalogue_num_for_series(series_id)
        if catalog_num is None:
            if verbose:
                print(f"Could not find catalog number for series {series_id}")
            return None
    
    metadata_df = get_metadata_from_index(series_id, catalog_num = catalog_num)

    if metadata_df is not None:
        return metadata_df
    else:

        if verbose:
            print(f"Metadata for series {series_id} not found in index, checking catalog {catalog_num}")
        try:
            if verbose:
                print(f"Getting metadata for {series_id} from catalog {catalog_num}")
            
            # Read the catalog data and metadata
            data_dict, metadata_df = ra.read_abs_cat(cat=catalog_num, verbose=verbose)
            
            # Find the series in metadata
            series_mask = metadata_df['series_id'].astype(str) == series_id
            
            if series_mask.any():
                if return_dict:
                    return data_dict, metadata_df[series_mask].iloc[0]
                else:
                    return metadata_df[series_mask].iloc[0]
            else:
                if verbose:
                    print(f"Series {series_id} not found in catalog {catalog_num}")
                return None
        
        except Exception as e:
            print(f"Error getting metadata for {series_id}: {e}")
            return None


def download_series_data(
    catalog_num: str,
    series_id: str,
    verbose: bool = False,
    cache_only: bool = False
) -> Optional[pd.DataFrame]:
    """
    Download ABS time series data for a specific series.
    
    Parameters:
    -----------
    catalog_num : str
        The ABS catalog number (e.g., "6202.0")
    series_id : str or list of str
        The ABS series ID(s) to download
    verbose : bool
        Print debug information if True
    cache_only : bool
        Only use cached data if True
        
    Returns:
    --------
    pd.DataFrame or None
        DataFrame containing the series data, or None if download failed
    """
    try:
        if verbose:
            print(f"Downloading series {series_id} from catalog {catalog_num}")
        
        # Use read_abs_series to download the specific series
        data_df, metadata_df = ra.read_abs_series(
            cat=catalog_num,
            series_id=series_id,
            verbose=verbose,
            cache_only=cache_only
        )
        
        return data_df
    
    except Exception as e:
        print(f"Error downloading series data: {e}")
        return None


def get_series_by_id(
    series_id: str,
    catalog_num: Optional[str] = None,
    verbose: bool = False,
    cache_only: bool = False
) -> Tuple[Optional[pd.Series], Optional[pd.Series]]:
    """
    High-level function to get both data and metadata for an ABS series.
    
    This function attempts to find and download a specific ABS series by its ID.
    If catalog_num is not provided, it will search available catalogs.
    
    Parameters:
    -----------
    series_id : str
        The ABS series ID (e.g., "A2326481T")
    catalog_num : str, optional
        The ABS catalog number. If not provided, the function will try to find it
    verbose : bool
        Print debug information if True
    cache_only : bool
        Only use cached data if True
        
    Returns:
    --------
    Tuple[pd.Series or None, pd.Series or None]
        (data_series, metadata_series) where:
        - data_series: pd.Series with the time series data
        - metadata_series: pd.Series with metadata about the series
        Returns (None, None) if series not found
    """
    try:
        if verbose:
            print(f"Getting series {series_id}")
        
        if catalog_num is None:
            catalog_num = get_catalogue_num_for_series(series_id)
            if catalog_num is None:
                if verbose:
                    print(f"Could not find catalog number for series {series_id}")
                return None, None
        
        # Download the series data
        data_df = download_series_data(
            catalog_num=catalog_num,
            series_id=series_id,
            verbose=verbose,
            cache_only=cache_only
        )
        
        if data_df is None or data_df.empty:
            if verbose:
                print(f"No data found for series {series_id}")
            return None, None
        
        # Get the series data (typically a column in the returned DataFrame)
        if isinstance(data_df, pd.DataFrame):
            if series_id in data_df.columns:
                data_series = data_df[series_id]
            else:
                # If series_id is not a column, get first column
                data_series = data_df.iloc[:, 0] if len(data_df.columns) > 0 else None
        else:
            data_series = data_df
        
        # Get metadata
        metadata_series = get_series_metadata(
            catalog_num=catalog_num,
            series_id=series_id,
            verbose=verbose
        )
        
        # Ensure the data series has the series_id as its name
        if data_series is not None:
            data_series.name = series_id
        
        return data_series, metadata_series
    
    except Exception as e:
        print(f"Error getting series {series_id}: {e}")
        return None, None


def search_by_description(
    catalog_num: str,
    description_filter: str,
    verbose: bool = False,
    exact_match: bool = False,
    regex: bool = False
) -> Optional[pd.DataFrame]:
    """
    Search for series by description within a catalog.
    
    Parameters:
    -----------
    catalog_num : str
        The ABS catalog number
    description_filter : str
        The description text to search for
    verbose : bool
        Print debug information if True
    exact_match : bool
        Use exact string matching if True
    regex : bool
        Use regex matching if True
        
    Returns:
    --------
    pd.DataFrame or None
        DataFrame with matching series metadata
    """
    try:
        if verbose:
            print(f"Searching catalog {catalog_num} for description: {description_filter}")
        
        # Get the catalog metadata
        _, metadata_df = ra.read_abs_cat(cat=catalog_num, verbose=verbose)
        
        # Search in common description columns
        desc_columns = ['description', 'series', 'did', 'table_title']
        matches = None
        
        for col in desc_columns:
            if col in metadata_df.columns:
                if exact_match:
                    col_matches = metadata_df[metadata_df[col].astype(str) == description_filter]
                elif regex:
                    col_matches = metadata_df[metadata_df[col].astype(str).str.contains(description_filter, regex=True, case=False, na=False)]
                else:
                    col_matches = metadata_df[metadata_df[col].astype(str).str.contains(description_filter, case=False, na=False)]
                
                if matches is None:
                    matches = col_matches
                else:
                    matches = pd.concat([matches, col_matches]).drop_duplicates()
        
        return matches if matches is not None and len(matches) > 0 else None
    
    except Exception as e:
        print(f"Error searching by description: {e}")
        return None


def get_abs_catalogue(
    cache_only: bool = False,
    verbose: bool = False
) -> Optional[pd.DataFrame]:
    """
    Get the complete ABS catalogue listing.
    
    Parameters:
    -----------
    cache_only : bool
        Only use cached data if True
    verbose : bool
        Print debug information if True
        
    Returns:
    --------
    pd.DataFrame or None
        DataFrame with ABS catalogue information
    """
    try:
        if verbose:
            print("Retrieving ABS catalogue")
        
        catalogue = ra.abs_catalogue(cache_only=cache_only, verbose=verbose)
        return catalogue
    
    except Exception as e:
        print(f"Error getting ABS catalogue: {e}")
        return None

def get_catalogue_num_for_series(series_id: str) -> str:
        """
        Get the catalogue number for a given series ID by searching the ABS master index, loaded from file (HDFStore)

        Parameters:

        series_id : str
            The ABS series ID to look up
        Returns:
        --------
        str
            The catalogue number associated with the series ID
        """
        masterIndex = pd.read_hdf(wd+fdel+"abs_master_index.h5s", key='data')
        result = Search_DF_np(masterIndex, series_id, use_cols=['Data Item Description', "Series ID"], verbose=False)
        catalog_num = result.iloc[0]['Catalogue number'] if result is not None and not result.empty else None

        if catalog_num is None:
            raise ValueError(f"Series ID {series_id} not found in any catalog")
        
        return catalog_num

def get_metadata_from_index(series_id: str, catalog_num: str) -> Optional[pd.Series]:
    """
    Get metadata for a series ID from the ABS master index.

    Parameters:
    -----------
    series_id : str
        The ABS series ID to look up

    Returns:
    --------
    pd.Series or None
        Series containing metadata for the specified series, or None if not found
    """
    masterIndex = pd.read_hdf(wd+fdel+"abs_master_index.h5s", key='data')

    if catalog_num is not None:
        result = masterIndex[(masterIndex['Catalogue number'] == catalog_num) & (masterIndex['Series ID'] == series_id)]
        if not result.empty:
            return result.iloc[0]
        else:
            return None
    else:
        result = Search_DF_np(masterIndex, series_id, use_cols=['Data Item Description', "Series ID"], verbose=False)

    if result is not None and not result.empty:
        return result.iloc[0]
    else:
        return None


# ============================================================================
# RBA FUNCTIONS - PYTHON READABS
# ============================================================================

def get_rba_catalogue(verbose: bool = False) -> Optional[pd.DataFrame]:
    """
    Get the complete RBA catalogue listing of available tables.
    
    Parameters:
    -----------
    verbose : bool
        Print debug information if True
        
    Returns:
    --------
    pd.DataFrame or None
        DataFrame with RBA catalogue information containing table numbers and descriptions
    """
    try:
        if verbose:
            print("Retrieving RBA catalogue")
        
        catalogue = ra.rba_catalogue()
        return catalogue
    
    except Exception as e:
        print(f"Error getting RBA catalogue: {e}")
        return None


def browse_rba_tables(searchterm: str = "rate", verbose: bool = False) -> Optional[pd.DataFrame]:
    """
    Search RBA tables by keyword using Python readabs package.
    
    Parameters:
    -----------
    searchterm : str
        Keyword to search for in table names/descriptions
    verbose : bool
        Print debug information if True
        
    Returns:
    --------
    pd.DataFrame or None
        DataFrame with matching RBA tables (renamed to have 'id' and 'title' columns)
    """
    try:
        if verbose:
            print(f"Searching RBA tables for: {searchterm}")
        
        # Get the full RBA catalogue
        catalogue = ra.rba_catalogue()
        
        if catalogue is None or catalogue.empty:
            if verbose:
                print("No RBA catalogue data available")
            return None
        
        # Search in table descriptions
        # RBA catalogue typically has columns like 'table_no', 'table_title', etc.
        mask = catalogue.astype(str).apply(
            lambda x: x.str.contains(searchterm, case=False, na=False)
        ).any(axis=1)
        
        results = catalogue[mask]
        
        if results.empty:
            if verbose:
                print(f"No tables found matching '{searchterm}'")
            return None
        
        # Rename columns to standardized 'id' and 'title' format
        # Adjust these column names based on actual RBA catalogue structure
        if 'table_no' in results.columns and 'table_title' in results.columns:
            results = results.rename(columns={'table_no': 'id', 'table_title': 'title'})
        
        if verbose:
            print(f"Found {len(results)} matching tables")
        
        return results
    
    except Exception as e:
        print(f"Error browsing RBA tables: {e}")
        return None


def browse_rba_series(
    searchterm: str = "rate", 
    table_filter: Optional[str] = None,
    max_tables: int = 20,
    verbose: bool = False
) -> Optional[pd.DataFrame]:
    """
    Search RBA series by keyword within specified tables using Python readabs package.
    
    Note: This function can be slow as it needs to download and read RBA tables.
    Use table_filter to narrow down which tables to search, or use browse_rba_tables()
    first to find relevant tables.
    
    Parameters:
    -----------
    searchterm : str
        Keyword to search for in series names/descriptions
    table_filter : str, optional
        Filter tables by description before searching (e.g., "interest" to only search interest rate tables)
    max_tables : int
        Maximum number of tables to search (default 20 to avoid long wait times)
    verbose : bool
        Print debug information if True
        
    Returns:
    --------
    pd.DataFrame or None
        DataFrame with matching RBA series with columns 'id', 'title', 'description', 'table_no', 'table_title'
    """
    import warnings
    
    try:
        if verbose:
            print(f"Searching RBA series for: {searchterm}")
        
        # Get the RBA catalogue first
        catalogue = ra.rba_catalogue()
        
        if catalogue is None or catalogue.empty:
            if verbose:
                print("No RBA catalogue available")
            return None
        
        # Filter catalogue if table_filter provided
        if table_filter:
            desc_col = 'Description' if 'Description' in catalogue.columns else 'table_title'
            if desc_col in catalogue.columns:
                mask = catalogue[desc_col].str.contains(table_filter, case=False, na=False)
                catalogue = catalogue[mask]
                if verbose:
                    print(f"Filtered to {len(catalogue)} tables matching '{table_filter}'")
        
        # Limit number of tables to search
        catalogue = catalogue.head(max_tables)
        
        all_series = []
        tables_searched = 0
        
        # Suppress warnings about print areas and xlrd
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UserWarning)
            
            # Iterate through tables to find series
            for idx, row in catalogue.iterrows():
                try:
                    table_no = idx if isinstance(idx, str) else (row.get('table_no') or row.get('id') or idx)
                    
                    # Read the table to get both data and metadata
                    table_data, metadata = ra.read_rba_table(table=str(table_no))
                    tables_searched += 1
                    
                    if table_data is not None and not table_data.empty and metadata is not None:
                        # Search in both series IDs and titles/descriptions
                        for series_id in table_data.columns:
                            series_id_str = str(series_id)
                            
                            # Get the title from metadata if available
                            if series_id in metadata.index:
                                series_title = metadata.loc[series_id, 'Title'] if 'Title' in metadata.columns else series_id_str
                                series_description = metadata.loc[series_id, 'Description'] if 'Description' in metadata.columns else ''
                            else:
                                series_title = series_id_str
                                series_description = ''
                            
                            # Check if searchterm matches series ID, title, or description
                            if (searchterm.lower() in series_id_str.lower() or 
                                searchterm.lower() in str(series_title).lower() or
                                searchterm.lower() in str(series_description).lower()):
                                all_series.append({
                                    'id': series_id,
                                    'title': series_title,
                                    'description': series_description,
                                    'table_no': table_no,
                                    'table_title': row.get('Description', row.get('table_title', ''))
                                })
                except Exception:
                    # Silently skip tables that can't be read (old formats, errors, etc.)
                    continue
        
        if verbose:
            print(f"Searched {tables_searched} tables")
        
        if not all_series:
            if verbose:
                print(f"No series found matching '{searchterm}'")
            return None
        
        results_df = pd.DataFrame(all_series)
        
        if verbose:
            print(f"Found {len(results_df)} matching series")
        
        return results_df
    
    except Exception as e:
        print(f"Error browsing RBA series: {e}")
        return None


def get_rba_series(
    series_id: str,
    table_no: Optional[str] = None,
    verbose: bool = False
) -> Tuple[Optional[pd.Series], Optional[pd.Series]]:
    """
    Download RBA series data using Python readabs package.
    
    Parameters:
    -----------
    series_id : str
        RBA series ID (column name in RBA table)
    table_no : str, optional
        RBA table number. If not provided, will search all tables
    verbose : bool
        Print debug information if True
        
    Returns:
    --------
    Tuple[pd.Series or None, pd.Series or None]
        (data_series, metadata_series) where:
        - data_series: pd.Series with the time series data
        - metadata_series: pd.Series with metadata about the series
        Returns (None, None) if series not found
    """
    try:
        if verbose:
            print(f"Getting RBA series {series_id}")
        
        # If table number provided, read that specific table
        if table_no:
            table_data, _ = ra.read_rba_table(table=table_no)
            
            if table_data is None or table_data.empty:
                if verbose:
                    print(f"No data found in table {table_no}")
                return None, None
            
            # Find the series in the table
            if series_id in table_data.columns:
                data_series = table_data[series_id]
            else:
                if verbose:
                    print(f"Series {series_id} not found in table {table_no}")
                return None, None
        else:
            # Search all tables for the series
            catalogue = ra.rba_catalogue()
            
            if catalogue is None or catalogue.empty:
                if verbose:
                    print("No RBA catalogue available")
                return None, None
            
            data_series = None
            table_no = None
            
            for idx, row in catalogue.iterrows():
                try:
                    tbl_no = row.get('table_no') or row.get('id') or idx
                    table_data, _ = ra.read_rba_table(table=str(tbl_no))
                    
                    if table_data is not None and series_id in table_data.columns:
                        data_series = table_data[series_id]
                        table_no = tbl_no
                        break
                except Exception as e:
                    if verbose:
                        print(f"Warning: Could not read table {tbl_no}: {e}")
                    continue
            
            if data_series is None:
                if verbose:
                    print(f"Series {series_id} not found in any RBA table")
                return None, None
        
        # Create metadata series
        metadata_series = pd.Series({
            'series_id': series_id,
            'title': series_id,
            'table_no': table_no,
            'source': 'RBA',
            'frequency': 'Unknown'  # RBA tables may have different frequencies
        })
        
        # Ensure the data series has the series_id as its name
        data_series.name = series_id
        
        if verbose:
            print(f"Successfully retrieved series {series_id} from table {table_no}")
            print(f"Data shape: {data_series.shape}")
        
        return data_series, metadata_series
    
    except Exception as e:
        print(f"Error getting RBA series {series_id}: {e}")
        return None, None


if __name__ == "__main__":
    # Example usage
    print("ABS & RBA Python readabs wrapper module")
    print("\nABS Functions:")
    print("  - search_series_by_id()")
    print("  - search_series_by_catalog()")
    print("  - get_series_metadata()")
    print("  - download_series_data()")
    print("  - get_series_by_id()")
    print("  - search_by_description()")
    print("  - get_abs_catalogue()")
    print("\nRBA Functions:")
    print("  - get_rba_catalogue()")
    print("  - browse_rba_tables()")
    print("  - browse_rba_series()")
    print("  - get_rba_series()")
