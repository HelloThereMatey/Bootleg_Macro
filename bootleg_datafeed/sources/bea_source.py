"""
Bureau of Economic Analysis (BEA) source for bm.

Standalone implementation based on the working bea_data_mate/pybea/client.py.
No dependency on pip-installed pybea package.
"""

from typing import Optional, Union, List
from urllib.parse import urlencode

import numpy as np
import pandas as pd
import requests

from ..auxiliary import FrequencyConverter, convert_to_standard_series, calculate_metadata_stats
from ..models import SeriesMetadata, StandardSeries


class BureauEconomicAnalysisClient:
    """Standalone BEA API client.

    Based on bea_data_mate/pybea/client.py - the working local implementation.
    """

    BASE_URL = "https://apps.bea.gov/api/data/"

    def __init__(self, api_key: str) -> None:
        """Initialize BEA API client.

        Args:
            api_key: BEA API key
        """
        self.api_key = api_key
        self._format = "JSON"

    def _make_request(self, http_method: str, params: dict) -> Union[dict, str]:
        """Make HTTP request to BEA API.

        Args:
            http_method: HTTP method (GET/POST)
            params: Query parameters including BEA API method

        Returns:
            JSON or XML response
        """
        # Ensure BEA API method is uppercase in params
        params = {k.upper() if k.lower() != 'method' else k: v for k, v in params.items()}

        request_session = requests.Session()
        request_session.verify = True

        request_request = requests.Request(
            method=http_method.upper(),
            url=self.BASE_URL,
            params=params,
        ).prepare()

        response = request_session.send(request=request_request)
        request_session.close()

        if response.ok and self._format == "JSON":
            final_response = response.json()
        elif response.ok and self._format == "XML":
            final_response = response.text
        else:
            raise requests.ConnectionError(f"BEA API error: {response.status_code} - {response.text}")

        return final_response

    def get_dataset_list(self) -> dict:
        """Get list of available BEA datasets.

        Returns:
            Dict with dataset list
        """
        params = {"UserID": self.api_key, "Method": "GetDataSetList", "ResultFormat": self._format}
        return self._make_request(http_method="get", params=params)

    def get_parameters_list(self, dataset_name: str) -> dict:
        """Get parameters for a dataset.

        Args:
            dataset_name: Name of dataset (e.g., 'NIPA')

        Returns:
            Dict with parameter list
        """
        params = {
            "UserID": self.api_key,
            "Method": "GetParameterList",
            "DataSetName": dataset_name,
            "ResultFormat": self._format,
        }
        return self._make_request(http_method="get", params=params)

    def national_income_and_product_accounts(
        self,
        table_name: str,
        year: Union[str, List[str]] = "ALL",
        frequency: Union[str, List[str]] = "A,Q,M",
    ) -> dict:
        """Fetch NIPA (National Income and Product Accounts) data.

        Args:
            table_name: Table code (e.g., 'T10101' for GDP)
            year: Year(s) or 'ALL'
            frequency: 'A', 'Q', 'M' or combinations

        Returns:
            BEA API response dict
        """
        if isinstance(year, list):
            year = ",".join(year)
        if isinstance(table_name, list):
            table_name = ",".join(table_name)
        if isinstance(frequency, list):
            frequency = ",".join(frequency)

        params = {
            "UserID": self.api_key,
            "Method": "GetData",
            "DataSetName": "NIPA",
            "Year": year,
            "Frequency": frequency,
            "TableName": table_name,
            "ResultFormat": self._format,
        }
        return self._make_request(http_method="get", params=params)

    def national_income_and_product_accounts_detail(
        self,
        table_name: str,
        year: Union[str, List[str]] = "ALL",
        frequency: Union[str, List[str]] = "A,Q,M",
    ) -> dict:
        """Fetch NIPA Underlying Detail data.

        Args:
            table_name: Table code
            year: Year(s) or 'ALL'
            frequency: 'A', 'Q', 'M' or combinations

        Returns:
            BEA API response dict
        """
        if isinstance(year, list):
            year = ",".join(year)
        if isinstance(table_name, list):
            table_name = ",".join(table_name)
        if isinstance(frequency, list):
            frequency = ",".join(frequency)

        params = {
            "UserID": self.api_key,
            "Method": "GetData",
            "DataSetName": "NIUnderlyingDetail",
            "Year": year,
            "Frequency": frequency,
            "TableName": table_name,
            "ResultFormat": self._format,
        }
        return self._make_request(http_method="get", params=params)

    def fixed_assets(
        self,
        table_name: Union[str, List[str]] = "ALL",
        year: Union[str, List[str]] = "ALL",
    ) -> dict:
        """Fetch Fixed Assets data.

        Args:
            table_name: Table name(s) or 'ALL'
            year: Year(s) or 'ALL'

        Returns:
            BEA API response dict
        """
        if isinstance(year, list):
            year = ",".join(year)
        if isinstance(table_name, list):
            table_name = ",".join(table_name)

        params = {
            "UserID": self.api_key,
            "Method": "GetData",
            "DataSetName": "FixedAssets",
            "Year": year,
            "TableName": table_name,
            "ResultFormat": self._format,
        }
        return self._make_request(http_method="get", params=params)


def _parse_time_period(time_period: str, frequency: str) -> pd.Timestamp:
    """Parse BEA TimePeriod string to Timestamp.

    Args:
        time_period: BEA time period string (e.g., '2024Q1', '2024M01', '2024')
        frequency: 'A', 'Q', or 'M'

    Returns:
        pd.Timestamp
    """
    tp = str(time_period).strip()
    if frequency == 'M':
        # '2024M01' -> 2024-01-01
        return pd.to_datetime(tp.replace('M', '-'))
    elif frequency == 'Q':
        # '2024Q1' -> 2024-01-01 (first month of quarter)
        year, quarter = tp.split('Q')
        month = (int(quarter) - 1) * 3 + 1
        return pd.Timestamp(year=int(year), month=month, day=1)
    else:  # Annual '2024'
        return pd.to_datetime(tp, format='%Y')


def _convert_value(value: str) -> float:
    """Convert BEA DataValue to float.

    Args:
        value: String value (may contain commas or be '(NA)')

    Returns:
        float or NaN
    """
    if pd.isna(value):
        return np.nan
    s = str(value).strip()
    if s in ('(NA)', '(NM)', '', 'N/A'):
        return np.nan
    # Remove commas from numbers like "26,484.9"
    s = s.replace(',', '')
    try:
        return float(s)
    except ValueError:
        return np.nan


def _parse_bea_response(data: dict, frequency: str) -> pd.DataFrame:
    """Parse BEA API response into DataFrame.

    Args:
        data: BEA API response dict
        frequency: 'A', 'Q', or 'M'

    Returns:
        DataFrame with parsed data
    """
    results = data.get('BEAAPI', {}).get('Results', {})
    if not results:
        # Check for error
        error = data.get('BEAAPI', {}).get('Error') or results.get('Error')
        if error:
            raise ValueError(f"BEA API error: {error}")
        raise ValueError(f"Unexpected BEA response structure: {list(data.keys())}")

    data_list = results.get('Data', [])
    if not data_list:
        raise ValueError("No data returned from BEA API")

    df = pd.DataFrame(data_list)

    # Parse datetime
    df['datetime'] = df['TimePeriod'].apply(lambda x: _parse_time_period(str(x), frequency))

    # Convert values
    df['value'] = df['DataValue'].apply(_convert_value)

    # Set index
    df = df.set_index('datetime').sort_index()

    return df


def pull_bea(
    dataset: str,
    table_code: str,
    api_key: str,
    series_code: Optional[str] = None,
    frequency: str = "Q",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> StandardSeries:
    """Pull data from Bureau of Economic Analysis.

    Args:
        dataset: BEA dataset name ('NIPA', 'NIUnderlyingDetail', 'FixedAssets')
        table_code: Table code (e.g., 'T10101' for GDP)
        series_code: Optional specific series code within table
        frequency: Data frequency ('A', 'Q', 'M')
        start_date: Start date (YYYY-MM-DD) - filters after fetch
        end_date: End date (YYYY-MM-DD) - filters after fetch
        api_key: BEA API key

    Returns:
        StandardSeries with data and metadata
    """
    # Map friendly names to BEA API dataset names
    dataset_map = {
        'NIPA': ('NIPA', 'national_income_and_product_accounts'),
        'NIUnderlyingDetail': ('NIUnderlyingDetail', 'national_income_and_product_accounts_detail'),
        'FixedAssets': ('FixedAssets', 'fixed_assets'),
    }

    if dataset not in dataset_map:
        raise ValueError(f"Unknown dataset '{dataset}'. Must be one of: {list(dataset_map.keys())}")

    bea_dataset, method_name = dataset_map[dataset]

    # Create client and fetch data
    client = BureauEconomicAnalysisClient(api_key=api_key)
    method = getattr(client, method_name)

    data = method(table_name=table_code, year="ALL", frequency=frequency)

    # Parse response
    df = _parse_bea_response(data, frequency)

    # Filter by series_code if specified
    if series_code and 'SeriesCode' in df.columns:
        df = df[df['SeriesCode'] == series_code]

    # Use LineDescription as series name
    if 'LineDescription' in df.columns:
        series_name = df['LineDescription'].iloc[0]
    else:
        series_name = f"{dataset}_{table_code}"

    # Create series
    series = pd.Series(df['value'].values, index=df.index, name=series_name)
    series = convert_to_standard_series(series)

    # Filter by date range
    if start_date:
        start = pd.Timestamp(start_date)
        series = series[series.index >= start]
    if end_date:
        end = pd.Timestamp(end_date)
        series = series[series.index <= end]

    # Build metadata
    metadata = SeriesMetadata(
        id=f"{dataset}_{table_code}_{series_code or 'all'}",
        title=f"BEA {dataset} Table {table_code}",
        source='bea',
        original_source='Bureau of Economic Analysis',
        start_date=series.index.min().date() if len(series) > 0 else None,
        end_date=series.index.max().date() if len(series) > 0 else None,
        frequency=FrequencyConverter.standardize(frequency),
        **calculate_metadata_stats(series),
    )

    return StandardSeries.from_pandas(series, metadata)


def list_bea_datasets(api_key: str) -> pd.DataFrame:
    """List all available BEA datasets.

    Args:
        api_key: BEA API key

    Returns:
        DataFrame with dataset names and descriptions
    """
    client = BureauEconomicAnalysisClient(api_key=api_key)
    data = client.get_dataset_list()
    datasets = data.get('BEAAPI', {}).get('Results', {}).get('Dataset', [])
    return pd.DataFrame(datasets)


def search_bea_tables(
    dataset: str,
    api_key: str,
) -> pd.DataFrame:
    """List available tables for a BEA dataset.

    Args:
        dataset: BEA dataset name ('NIPA', 'NIUnderlyingDetail', 'FixedAssets')
        api_key: BEA API key

    Returns:
        DataFrame with table codes/names
    """
    client = BureauEconomicAnalysisClient(api_key=api_key)
    data = client.get_parameters_list(dataset)
    params = data.get('BEAAPI', {}).get('Results', {}).get('Parameter', [])
    # Filter to TableName parameter
    table_params = [p for p in params if p.get('ParameterName') == 'TableName']
    if table_params:
        # Get table values
        params_list = {
            "datasetname": dataset,
            "method": "GETPARAMETERVALUES",
            "parametername": "TableName",
        }
        params_list = {k.upper(): v for k, v in params_list.items()}
        params_list["UserID"] = api_key
        params_list["ResultFormat"] = "JSON"

        response = requests.get(client.BASE_URL, params=params_list)
        if response.ok:
            data = response.json()
            values = data.get('BEAAPI', {}).get('Results', {}).get('ParamValue', [])
            return pd.DataFrame(values)
    return pd.DataFrame()


def search_bea_series(
    dataset: str,
    table_code: str,
    frequency: str = "Q",
    api_key: str = None,
) -> pd.DataFrame:
    """Get series codes and descriptions for a BEA table.

    Args:
        dataset: BEA dataset name ('NIPA', 'NIUnderlyingDetail', 'FixedAssets')
        table_code: Table code
        frequency: Data frequency ('A', 'Q', 'M')
        api_key: BEA API key

    Returns:
        DataFrame with SeriesCode and LineDescription
    """
    data = pull_bea(
        dataset=dataset,
        table_code=table_code,
        frequency=frequency,
        api_key=api_key,
    )
    df = data.to_pandas().to_frame()
    df.columns = ['value']
    return df
