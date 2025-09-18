import pandas as pd
import numpy as np
import datetime
from typing import Optional, Dict, Any, Tuple
import warnings
import requests
import time

try:
    import pandasdmx as sdmx
    SDMX_AVAILABLE = True
except ImportError:
    SDMX_AVAILABLE = False
    print("Warning: pandasdmx not available. Install with: pip install pandasdmx")

def get_oecd_data(series_id: str, start_date: str = "1900-01-01", 
                  end_date: Optional[str] = None, timeout: int = 30) -> Tuple[pd.Series, pd.Series]:
    """
    Fetch OECD data using SDMX format via pandasdmx library with REST API fallback.
    
    Parameters:
    - series_id: str - OECD series identifier (e.g., "MEI.PRINTO01.AUS.M" or "AUS.GDP.A")
    - start_date: str - Start date in YYYY-MM-DD format
    - end_date: str - End date in YYYY-MM-DD format (optional, defaults to today)
    - timeout: int - Timeout in seconds for HTTP requests
    
    Returns:
    - Tuple[pd.Series, pd.Series] - (data_series, metadata_series)
    """
    
    if end_date is None:
        end_date = datetime.date.today().strftime('%Y-%m-%d')
    
    # Parse series_id to extract dataset and key components
    if '.' in series_id and len(series_id.split('.')) >= 2:
        parts = series_id.split('.')
        dataset_id = parts[0]
        series_key = '.'.join(parts[1:])
    else:
        # Default to common datasets
        dataset_id = 'MEI'  # Main Economic Indicators
        series_key = series_id
        print(f"No dataset specified, defaulting to {dataset_id}")
    
    print(f"Attempting to fetch OECD data: Dataset={dataset_id}, Key={series_key}")
    
    # Try SDMX first, then REST API fallback
    try:
        return _fetch_via_sdmx(dataset_id, series_key, series_id, start_date, end_date, timeout)
    except Exception as sdmx_error:
        print(f"SDMX method failed: {sdmx_error}")
        print("Trying REST API fallback...")
        try:
            return _fetch_via_rest_api(dataset_id, series_key, series_id, start_date, end_date, timeout)
        except Exception as rest_error:
            print(f"REST API fallback also failed: {rest_error}")
            # Return empty series with error info
            error_series = pd.Series([], name=series_id, dtype=float)
            error_metadata = pd.Series({
                'id': series_id,
                'title': f"OECD Error: {series_id}",
                'source': 'oecd',
                'error': f"Both SDMX and REST failed. SDMX: {sdmx_error}, REST: {rest_error}",
                'last_updated': datetime.datetime.now()
            }, name=series_id)
            return error_series, error_metadata

def _fetch_via_sdmx(dataset_id: str, series_key: str, series_id: str, 
                   start_date: str, end_date: str, timeout: int) -> Tuple[pd.Series, pd.Series]:
    """Fetch OECD data using pandasdmx library."""
    
    if not SDMX_AVAILABLE:
        raise ImportError("pandasdmx library is required for OECD data. Install with: pip install pandasdmx")
    
    # Initialize OECD SDMX connection with timeout
    oecd = sdmx.Request('OECD', timeout=timeout)
    
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    
    print(f"Fetching via SDMX with {timeout}s timeout...")
    
    # Skip data structure check that was causing issues
    # Request the actual data directly
    try:
        data_msg = oecd.data(
            dataset_id, 
            key=series_key,
            params={
                'startTime': start_dt.strftime('%Y-%m-%d'),
                'endTime': end_dt.strftime('%Y-%m-%d')
            }
        )
    except Exception as e:
        print(f"Failed to fetch data with key '{series_key}': {e}")
        # Try without specific key
        data_msg = oecd.data(
            dataset_id,
            params={
                'startTime': start_dt.strftime('%Y-%m-%d'),
                'endTime': end_dt.strftime('%Y-%m-%d')
            }
        )
        print("Retrieved dataset without specific key")
    
    # Convert to pandas with timeout protection
    start_time = time.time()
    df = sdmx.to_pandas(data_msg, datetime='TIME_PERIOD')
    
    if time.time() - start_time > timeout:
        raise TimeoutError(f"Pandas conversion took longer than {timeout} seconds")
    
    if df.empty:
        raise ValueError(f"No data returned for series {series_id}")
    
    return _process_oecd_dataframe(df, series_id, dataset_id, series_key)

def _fetch_via_rest_api(dataset_id: str, series_key: str, series_id: str, 
                       start_date: str, end_date: str, timeout: int) -> Tuple[pd.Series, pd.Series]:
    """Fetch OECD data using direct REST API calls."""
    
    # OECD REST API endpoint
    base_url = "https://stats.oecd.org/restsdmx/sdmx.ashx/GetData"
    
    # Construct URL
    url = f"{base_url}/{dataset_id}/{series_key}/all"
    
    params = {
        'startTime': start_date,
        'endTime': end_date,
        'format': 'json'
    }
    
    print(f"Fetching via REST API: {url}")
    
    response = requests.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    
    # Parse JSON response
    data = response.json()
    
    # Extract time series data from OECD JSON structure
    if 'dataSets' not in data or not data['dataSets']:
        raise ValueError(f"No datasets found in response for {series_id}")
    
    dataset = data['dataSets'][0]
    
    if 'observations' not in dataset:
        raise ValueError(f"No observations found for {series_id}")
    
    # Extract time dimension
    structure = data['structure']
    time_values = None
    
    for dim in structure['dimensions']['observation']:
        if dim['id'] == 'TIME_PERIOD':
            time_values = [val['id'] for val in dim['values']]
            break
    
    if not time_values:
        raise ValueError("Could not find time dimension in OECD data")
    
    # Extract observations
    observations = dataset['observations']
    values = []
    dates = []
    
    for i, time_val in enumerate(time_values):
        if str(i) in observations:
            obs = observations[str(i)]
            if obs and len(obs) > 0:
                values.append(float(obs[0]))
                dates.append(pd.to_datetime(time_val))
    
    if not values:
        raise ValueError(f"No valid observations found for {series_id}")
    
    # Create pandas Series
    data_series = pd.Series(values, index=dates, name=series_id)
    
    # Create metadata
    metadata = pd.Series({
        'id': series_id,
        'title': f"OECD {dataset_id}: {series_key}",
        'source': 'oecd',
        'dataset': dataset_id,
        'series_key': series_key,
        'frequency': _infer_frequency(data_series.index),
        'units': 'Unknown',
        'start_date': data_series.index.min().date(),
        'end_date': data_series.index.max().date(),
        'last_updated': datetime.datetime.now(),
        'length': len(data_series),
        'min_value': float(data_series.min()),
        'max_value': float(data_series.max()),
        'description': f"OECD data series {series_id} from dataset {dataset_id} (REST API)"
    }, name=series_id)
    
    print(f"Successfully fetched {len(data_series)} observations via REST API")
    return data_series, metadata

def _process_oecd_dataframe(df: pd.DataFrame, series_id: str, dataset_id: str, series_key: str) -> Tuple[pd.Series, pd.Series]:
    """Process OECD DataFrame into Series and metadata."""
    
    print(f"Retrieved data shape: {df.shape}")
    print(f"Data columns: {df.columns.tolist()}")
    
    # Handle multi-level columns if present
    if isinstance(df.columns, pd.MultiIndex):
        if len(df.columns) == 1:
            data_series = df.iloc[:, 0]
            series_name = str(df.columns[0])
        else:
            # Multiple series - try to find the one matching our key
            matching_cols = [col for col in df.columns if series_key in str(col)]
            if matching_cols:
                data_series = df[matching_cols[0]]
                series_name = str(matching_cols[0])
            else:
                data_series = df.iloc[:, 0]
                series_name = str(df.columns[0])
                print(f"Using first available series: {series_name}")
    else:
        if len(df.columns) == 1:
            data_series = df.iloc[:, 0]
            series_name = df.columns[0]
        else:
            # Multiple columns, select first numeric one
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                data_series = df[numeric_cols[0]]
                series_name = numeric_cols[0]
            else:
                data_series = df.iloc[:, 0]
                series_name = df.columns[0]
    
    # Clean and rename the series
    data_series = data_series.dropna()
    data_series.name = series_id
    
    # Ensure datetime index
    if not isinstance(data_series.index, pd.DatetimeIndex):
        data_series.index = pd.to_datetime(data_series.index)
    
    # Create metadata series
    metadata = pd.Series({
        'id': series_id,
        'title': f"OECD {dataset_id}: {series_key}",
        'source': 'oecd',
        'dataset': dataset_id,
        'series_key': series_key,
        'frequency': _infer_frequency(data_series.index),
        'units': 'Unknown',
        'start_date': data_series.index.min().date() if not data_series.empty else None,
        'end_date': data_series.index.max().date() if not data_series.empty else None,
        'last_updated': datetime.datetime.now(),
        'length': len(data_series),
        'min_value': float(data_series.min()) if not data_series.empty and pd.api.types.is_numeric_dtype(data_series) else None,
        'max_value': float(data_series.max()) if not data_series.empty and pd.api.types.is_numeric_dtype(data_series) else None,
        'description': f"OECD data series {series_id} from dataset {dataset_id}"
    }, name=series_id)
    
    print(f"Successfully processed OECD data for {series_id}")
    return data_series, metadata

def _infer_frequency(index: pd.DatetimeIndex) -> str:
    """
    Infer the frequency of a datetime index.
    """
    if len(index) < 2:
        return 'Unknown'
    
    try:
        freq = pd.infer_freq(index)
        if freq:
            return freq
        
        # Manual inference for common OECD frequencies
        diff = (index[1] - index[0]).days
        if diff <= 1:
            return 'D'  # Daily
        elif 5 <= diff <= 10:
            return 'W'  # Weekly
        elif 25 <= diff <= 35:
            return 'M'  # Monthly
        elif 80 <= diff <= 100:
            return 'Q'  # Quarterly
        elif 350 <= diff <= 380:
            return 'A'  # Annual
        else:
            return 'Unknown'
    except:
        return 'Unknown'

def search_oecd_datasets() -> pd.DataFrame:
    """
    Return a list of common OECD datasets that can be used with this connector.
    """
    common_datasets = {
        'MEI': 'Main Economic Indicators',
        'QNA': 'Quarterly National Accounts',
        'EO': 'Economic Outlook',
        'KEI': 'Key Economic Indicators',
        'PRICES_CPI': 'Consumer Price Indices',
        'LFS': 'Labour Force Statistics',
        'FTRADE': 'Foreign Trade Statistics',
        'GOV': 'Government Finance Statistics',
        'HEALTH': 'Health Statistics',
        'EDU': 'Education Statistics'
    }
    
    return pd.DataFrame(list(common_datasets.items()), columns=['Dataset_ID', 'Description'])

if __name__ == "__main__":
    # Test the OECD data connector
    print("Testing OECD data connector...")
    
    # Test with a simple series and shorter timeout
    try:
        print("Testing with MEI dataset...")
        data, metadata = get_oecd_data("MEI.PRINTO01.AUS.M", "2020-01-01", timeout=15)
        print(f"Test successful! Retrieved {len(data)} data points")
        print(f"Data sample:\n{data.head()}")
        print(f"Metadata sample: {metadata[['title', 'frequency', 'start_date', 'end_date']].to_dict()}")
    except Exception as e:
        print(f"MEI test failed: {e}")
    
    # Test with QNA dataset
    try:
        print("\nTesting with QNA dataset...")
        data2, metadata2 = get_oecd_data("QNA.AUS.B1_GE.VOBARSA.Q", "2020-01-01", timeout=15)
        print(f"QNA test successful! Retrieved {len(data2)} data points")
        print(f"Data sample:\n{data2.head()}")
    except Exception as e:
        print(f"QNA test failed: {e}")
    
    # Show available datasets
    print("\nCommon OECD datasets:")
    print(search_oecd_datasets())
