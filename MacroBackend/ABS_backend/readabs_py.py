"""
Python readabs backend for downloading ABS data series.

This module provides a Python-based interface to the ABS data using the Python
readabs package, replacing the R-based implementation that had issues with series
ID handling.

Main functions:
- search_series_by_id(): Search for a series by its ABS series ID
- search_series_by_catalog(): Search for series within a catalog number
- get_series_metadata(): Retrieve metadata for a series
- download_series_data(): Download data for a specific series
- get_series_by_id(): High-level function to get series data and metadata by ID
"""

import os
import pandas as pd
from typing import Optional, Tuple, Dict, Any
import readabs as ra
from MacroBackend.Utilities import Search_DF_np

wd = os.path.dirname(os.path.abspath(__file__))
fdel = os.sep
parent = os.path.dirname(wd)


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

if __name__ == "__main__":
    # Example usage
    print("ABS Python readabs wrapper module")
    print("Available functions:")
    print("  - search_series_by_id()")
    print("  - search_series_by_catalog()")
    print("  - get_series_metadata()")
    print("  - download_series_data()")
    print("  - get_series_by_id()")
    print("  - search_by_description()")
    print("  - get_abs_catalogue()")
