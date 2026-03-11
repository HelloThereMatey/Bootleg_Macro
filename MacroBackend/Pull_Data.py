###### Required modules/packages #####################################
import os
fdel = os.path.sep
wd = os.path.dirname(__file__)  ## This gets the working directory which is the folder where you have placed this .py file. 
parent = os.path.dirname(wd)
print(wd,parent)
import sys
sys.path.append(parent)
from typing import Literal

## This is one of my custom scripts holding functions for pulling price data from APIs. Your IDE might not find it before running script. 
from MacroBackend import PriceImporter, Utilities, js_funcs
from MacroBackend.BEA_Data import bea_data_mate
from MacroBackend.ABS_backend import abs_series_by_r
from MacroBackend.Glassnode import GlassNode_API
import datetime
import pandas as pd
import nasdaqdatalink as ndl
import tedata as ted ##This is my package that scrapes data from Trading Economics
import json
import concurrent.futures

def tedata_search(searchstr: str = "gdp", wait_time: int = 5):
    """Search Trading Economics for data series matching a keyword.

    Args:
        searchstr: Search term to query Trading Economics with.
        wait_time: Seconds to wait for the browser-driven search to complete.

    Returns:
        pd.DataFrame: Table of matching search results.
    """
    ted.find_active_drivers()
    search = ted.search_TE(use_existing_driver=True)
    search.search_trading_economics(searchstr, wait_time=wait_time)
    return search.result_table

# Note: signal-based timeouts are unsafe in threaded environments (Jupyter/notebooks).
# Use a ThreadPoolExecutor timeout wrapper instead of signal.alarm.

####### CLASSES ######################################################
class get_data_failure(Exception):
    """Raised when a data pull from any source fails or returns no data."""
    pass
      
class dataset(object):

    def __init__(self):
        """
        The PullData class is responsible for pulling data from various sources.

        Attributes:
        - supported_sources (list): A list of supported data sources.
        - added_sources (list): A list of sources that have been added.
        - keySources (list): A list of sources that need api-key to access.
        - keyz (Utilities): An instance of the Utilities.api_keys class that should have access to your keys.
        - api_keys (dict): A dictionary containing API keys.
        - data (None): Placeholder for the pulled data.
        """
        self.added_sources = ['fred', 'yfinance', 'yfinance2', 'tv', 'coingecko', 'nasdaq', 'glassnode', 'abs_series', 
                      'abs_tables', 'bea', 'rba_tables', 'rba_series', 'saveddata', "hdfstores", "tedata"]
        self.supported_sources = list(self.added_sources)
        self.keySources = ['fred', 'bea', 'glassnode', 'nasdaq']

        self.keyz = Utilities.api_keys(JSONpath=parent + fdel + 'MacroBackend' + fdel + 'SystemInfo')
        self.api_keys = dict(self.keyz.keys)
        self.data = None

    def check_key(self):
        """Verify that the required API key exists for the current source.

        If the key is missing, prompts the user interactively to paste it in.
        Sets nothing if the key is already present.
        """
        # print("Checking API keys: ", self.api_keys)
        if self.source in self.keySources and self.source not in self.api_keys.keys():
            print("No API key found for your source: ", self.source, "do you have the key at hand ready to paste into terminal?")
            if input("y/n?") == 'y':
                self.keyz.add_key(self.source)
            else:
                print("You need an API key to get data from ", self.source)    
            return None
        else:
            return    

    @staticmethod
    def _sanitize_hdf_key(key: str) -> str:
        """Sanitize a string so it is a valid HDF5 store key.

        Replaces non-alphanumeric characters with underscores, collapses
        consecutive underscores, and ensures the key starts with a letter or '_'.

        Args:
            key: Raw key string to sanitize.

        Returns:
            str: Cleaned key safe for use in pd.HDFStore.
        """
        cleaned = ''.join(ch if ch.isalnum() or ch == '_' else '_' for ch in str(key))
        while '__' in cleaned:
            cleaned = cleaned.replace('__', '_')
        if cleaned and not (cleaned[0].isalpha() or cleaned[0] == '_'):
            cleaned = '_' + cleaned
        return cleaned

    def _map_bea_frequency(self, freq: str = None) -> str:
        """Map a user-supplied frequency string to a BEA API frequency code.

        Args:
            freq: Frequency hint such as 'quarterly', 'Q', 'annual', etc.
                  Defaults to 'M' (monthly) when None.

        Returns:
            str: One of 'A', 'Q', or 'M'.
        """
        if freq is None:
            return 'M'
        f = str(freq).strip().lower()
        mapping = {
            'a': 'A', 'annual': 'A', 'yearly': 'A', '1y': 'A',
            'q': 'Q', 'quarterly': 'Q', '1q': 'Q',
            'm': 'M', 'monthly': 'M', '1m': 'M'
        }
        return mapping.get(f, 'M')

    def _normalize_bea_dataset(self, dataset_name: str = None) -> str:
        """Normalize a BEA dataset name to its canonical API form.

        Args:
            dataset_name: Raw dataset name (e.g. 'nipa', 'fixedassets').
                          Defaults to 'NIPA' when None.

        Returns:
            str: Canonical dataset name such as 'NIPA', 'NIPA_Details', or 'FixedAsset'.
        """
        ds = 'NIPA' if dataset_name is None else str(dataset_name).strip()
        ds_l = ds.lower()
        mapping = {
            'nipa': 'NIPA',
            'niunderlyingdetail': 'NIPA_Details',
            'nipa_details': 'NIPA_Details',
            'nipa-details': 'NIPA_Details',
            'fixedassets': 'FixedAsset',
            'fixedasset': 'FixedAsset'
        }
        return mapping.get(ds_l, ds)

    def _parse_bea_request(self) -> dict:
        """Parse ``self.data_code`` into BEA request components.

        Supports several delimiter formats:
          - ``Dataset|TableCode|SeriesCode[|LineDescription]``
          - ``TableCode|SeriesCode``
          - Colon or comma-separated equivalents

        Falls back to ``self.exchange_code`` for the series code when
        the data_code string contains only a table code.

        Returns:
            dict: Keys 'dataset', 'table_code', 'series_code',
                  'line_description', 'frequency'.
        """
        raw = str(self.data_code).strip()
        dataset = None
        table_code = raw
        series_code = None
        line_description = None

        if '|' in raw:
            parts = [p.strip() for p in raw.split('|') if str(p).strip() != '']
            if len(parts) >= 3:
                dataset, table_code, series_code = parts[0], parts[1], parts[2]
                if len(parts) >= 4:
                    line_description = parts[3]
            elif len(parts) == 2:
                table_code, series_code = parts
        elif ':' in raw:
            parts = [p.strip() for p in raw.split(':') if str(p).strip() != '']
            if len(parts) >= 3:
                dataset, table_code, series_code = parts[0], parts[1], parts[2]
                if len(parts) >= 4:
                    line_description = parts[3]
        elif ',' in raw:
            parts = [p.strip() for p in raw.split(',') if str(p).strip() != '']
            if len(parts) >= 2:
                table_code, series_code = parts[0], parts[1]
                if len(parts) >= 3:
                    dataset = parts[2]

        if (series_code is None or str(series_code).strip() == '') and self.exchange_code not in [None, '', 'N/A', 'nan']:
            series_code = str(self.exchange_code).strip()

        return {
            'dataset': self._normalize_bea_dataset(dataset),
            'table_code': str(table_code).strip(),
            'series_code': None if series_code is None else str(series_code).strip(),
            'line_description': line_description,
            'frequency': self._map_bea_frequency(self.data_freq)
        }

    def _bea_cache_path(self) -> str:
        """Return the file path for the BEA HDF5 table cache, creating the directory if needed.

        Returns:
            str: Absolute path to ``bea_table_cache.h5s``.
        """
        cache_dir = parent + fdel + 'User_Data' + fdel + 'BEA' + fdel + 'bea_tables'
        os.makedirs(cache_dir, exist_ok=True)
        return cache_dir + fdel + 'bea_table_cache.h5s'

    def _load_bea_table(self, dataset_name: str, table_code: str, frequency: str) -> tuple[pd.DataFrame, pd.Series]:
        """Load a full BEA table, using the HDF5 cache when available.

        On a cache miss the table is fetched from the BEA API via
        ``BEA_Data.Get_BEA_Data()`` and then persisted to the cache.

        Args:
            dataset_name: Canonical BEA dataset (e.g. 'NIPA').
            table_code: Table identifier (e.g. 'T10101').
            frequency: BEA frequency code — 'A', 'Q', or 'M'.

        Returns:
            tuple[pd.DataFrame, pd.Series]: (table_data, table_meta) where
                table_data has DatetimeIndex rows and one column per series,
                and table_meta maps series codes to descriptions.

        Raises:
            get_data_failure: If the BEA API returns no data.
        """
        cache_path = self._bea_cache_path()
        key_root = self._sanitize_hdf_key(f"{dataset_name}_{table_code}_{frequency}")
        data_key = f"bea_{key_root}_data"
        meta_key = f"bea_{key_root}_meta"

        if os.path.isfile(cache_path):
            try:
                cached_data = pd.read_hdf(cache_path, key=data_key)
                cached_meta_df = pd.read_hdf(cache_path, key=meta_key)
                cached_meta = cached_meta_df.squeeze(axis=1) if isinstance(cached_meta_df, pd.DataFrame) else pd.Series(cached_meta_df)
                cached_data.index = pd.DatetimeIndex(cached_data.index)
                print(f"Loaded BEA table from cache: {dataset_name}, {table_code}, {frequency}")
                return cached_data, pd.Series(cached_meta, dtype='object')
            except Exception:
                pass

        info_path = wd + fdel + 'BEA_Data' + fdel + 'Datasets' + fdel + 'BEAAPI_Info.xlsx'
        bea = bea_data_mate.BEA_API_backend.BEA_Data(api_key=self.api_keys['bea'], BEA_Info_filePath=info_path)
        bea.Get_BEA_Data(dataset=dataset_name, tCode=table_code, frequency=frequency, year='ALL')
        if bea.Data is None:
            raise get_data_failure(f"BEA table pull failed for dataset={dataset_name}, table={table_code}, frequency={frequency}")

        table_data = pd.DataFrame(bea.Data['Series_Split']).copy()
        table_data.index = pd.DatetimeIndex(table_data.index)
        table_meta = pd.Series(bea.Data.get('SeriesInfo', pd.Series(dtype='object')), dtype='object')

        try:
            table_data.to_hdf(cache_path, key=data_key, mode='a')
            table_meta.to_frame(name='value').to_hdf(cache_path, key=meta_key, mode='a')
        except Exception as e:
            print(f"Warning: failed to persist BEA cache for {table_code}. Error: {e}")

        return table_data, table_meta

    @staticmethod
    def _extract_bea_series(table_data: pd.DataFrame, table_meta: pd.Series, series_code: str = None,
                            line_description: str = None) -> tuple[pd.Series, str]:
        """Extract a single series from a cached BEA table DataFrame.

        Resolution order:
          1. Exact match on *line_description* in column names.
          2. Exact match on *series_code* in column names (case-insensitive).
          3. Reverse-lookup *series_code* through table_meta values.
          4. If the table has only one column, use it.
          5. Raise ``get_data_failure`` with available columns/codes.

        Args:
            table_data: DataFrame of the full BEA table (columns = series).
            table_meta: Series mapping internal keys to BEA series codes.
            series_code: BEA series code to look up (e.g. 'A191RL').
            line_description: Human-readable line description to match.

        Returns:
            tuple[pd.Series, str]: (extracted_series, column_name_used).

        Raises:
            get_data_failure: If the series cannot be resolved.
        """
        selected_col = None

        if line_description is not None and line_description in table_data.columns:
            selected_col = line_description

        if selected_col is None and series_code is not None:
            target = str(series_code).strip().upper()
            direct = [col for col in table_data.columns if str(col).strip().upper() == target]
            if direct:
                selected_col = direct[0]
            else:
                mapped = [idx for idx, val in table_meta.items()
                          if str(val).strip().upper() == target and str(idx) in table_data.columns]
                if mapped:
                    selected_col = mapped[0]

        if selected_col is None:
            if len(table_data.columns) == 1:
                selected_col = table_data.columns[0]
            else:
                sample_codes = [str(v) for v in table_meta.values[:12]]
                raise get_data_failure(
                    f"Unable to resolve BEA series_code '{series_code}'. "
                    f"Available table columns: {list(table_data.columns[:12])}. "
                    f"Sample BEA series codes: {sample_codes}"
                )

        series = pd.Series(table_data[selected_col], name=str(selected_col))
        return series, str(selected_col)
        
    def pull_data(self):
        """Execute the data pull for the currently configured source.

        Reads ``self.source``, ``self.data_code``, ``self.start_date``,
        ``self.end_date``, ``self.data_freq``, etc. and populates
        ``self.data``, ``self.SeriesInfo``, and ``self.dataName``.

        Called internally by ``get_data()`` inside a timeout-wrapped thread.
        Not intended to be called directly — use ``get_data()`` instead.
        """

        if self.source == 'fred':
            SeriesInfo, TheData = PriceImporter.PullFredSeries(self.data_code, self.api_keys['fred'],
                        start = self.start_date.strftime('%Y-%m-%d'), end = self.end_date.strftime('%Y-%m-%d'))
            self.dataName = SeriesInfo['id']

            self.SeriesInfo = SeriesInfo
            self.data = TheData

        elif self.source == 'yfinance':
            try:
                print("Trying yfinance package to get historical data for ", self.data_code)  
                TheData, _, series_info = PriceImporter.pullyfseries(self.data_code, start = self.start_date.strftime('%Y-%m-%d'),
                                                    interval = self.data_freq)
                if len(TheData) < 1:
                    raise get_data_failure('Could not get data for the data-code from the source specified.')
                self.filterData(TheData)
                self.SeriesInfo = series_info

            except Exception as e:
                print("Could not score data for asset: "+self.data_code," from yfinance. Error: ", e) 

        elif self.source == 'yfinance2':
            print("Using yahoo-finance2 JS package to get historical data..")  
            result = js_funcs.js_get_historical_data(
                self.data_code, 
                self.start_date.strftime('%Y-%m-%d'), 
                self.end_date.strftime('%Y-%m-%d'), 
                self.data_freq
            )
            
            if result.get('success', False):
                # Convert the JSON data to pandas DataFrame
                TheData = js_funcs.convert_js_data_to_pandas(result)
                print(f"Data fetched successfully for {self.data_code} from yfinance2")

                if not TheData.empty:
                    # Create series info
                    self.SeriesInfo = pd.Series({
                        'id': self.data_code,
                        'source': 'yfinance2',
                        'start_date': result.get('start_date'),
                        'end_date': result.get('end_date'),
                        'interval': result.get('interval'),
                        'title': self.data_code
                    })
                    self.filterData(TheData)
                else:
                    print(f"No data returned for {self.data_code}")
                    self.data = pd.DataFrame()
            else:
                print(f"Failed to fetch data: {result.get('error', 'Unknown error')}")
                self.data = pd.DataFrame()

        elif self.source == 'tv': 
            if self.exchange_code is None:
                try:
                    split = self.data_code.split(',', maxsplit=1)   #Data codes for tv are input in the format: DATA_CODE,EXCHANGE_CODE
                    self.data_code = split[0].strip(); self.exchange_code = split[1].strip()
                except:
                    print("You need to provide the exchange code for the data code you want to pull from TV. Try again.")
                    return None
                if self.exchange_code is None:
                    print("You need to provide the exchange code for the data code you want to pull from TV. Try again.")
                    return None
            if self.data_freq == '1d':
                self.data_freq = 'D'
            TheData, info = PriceImporter.DataFromTVGen(self.data_code, self.exchange_code, start_date = self.start_date, 
                                                        end_date = self.end_date, BarTimeFrame = self.data_freq)
            if TheData is None:
                print("No data returned from TV for the data code: ", self.data_code, " and exchange code: ", self.exchange_code)
                print("Check the symbol and exchange code you provided, or try a different data source.")
                self.data = pd.Series(); self.SeriesInfo = pd.Series()
            
            else:
                dtIndex = pd.DatetimeIndex(pd.DatetimeIndex(TheData.index).date)
                TheData.columns = TheData.columns.str.capitalize()
                if 'Symbol' in TheData.columns:
                    TheData.drop('Symbol',axis=1,inplace=True)

                self.SeriesInfo = info
                TheData.set_index(dtIndex,inplace=True)
                print('Data pulled from TV for ticker: ', self.data_code)  
                
                # Overwrite the start and end dates to match the data pulled from TV.
                self.start_date = TheData.index[0]; self.end_date = TheData.index[-1]
                self.data = TheData[self.start_date:self.end_date]      
                self.filterData(self.data)
        
        elif self.source == 'coingecko':
            CoinID = PriceImporter.getCoinID(self.data_code, InputTablePath=parent+fdel+'MacroBackend'+fdel+'AllCG.csv')
            numDays = (self.end_date - self.start_date).days
            TheData = PriceImporter.CoinGeckoPriceHistory(CoinID[1],TimeLength = numDays) 
            TheData.rename({"Price (USD)":"Close"},axis=1,inplace=True) 
            TheData = pd.Series(TheData['Close'], name = self.dataName) 
            self.data = TheData

        elif self.source == 'nasdaq':
            if ndl.ApiConfig.api_key == self.api_keys['nasdaq']:
                print('nasdaq key already set: ', ndl.ApiConfig.api_key)    
            else:    
                ndl.ApiConfig.api_key = self.api_keys['nasdaq']
                print('nasdaq API key set just now: ', ndl.ApiConfig.api_key) 
            print(self.start_date, self.end_date)
            self.data = ndl.get(self.exchange_code+'/'+self.data_code, start_date = self.start_date, end_date = self.end_date)

        elif self.source == 'glassnode':
            # For GlassNode we need the data_code. specification to be in thee format METRIC,ASSET,TIME_RESOLUTION
            # TIME_RESOLUTION parameter is optional, default = '24h'            
            
            # params = {'a':splitted[1].strip(),'i':splitted[2].strip(),'f':'json','api_key': self.api_keys['glassnode']} 
            gnpull = glassnode_data()
            gnpull.chosen_met(self.data_code)
            gnpull.get_data(asset = self.asset, resolution = self.resolution, format = self.format)
            self.data = gnpull.data
            self.SeriesInfo = gnpull.seriesInfo; self.dataName = gnpull.seriesInfo["metric_short"]
            if isinstance(self.data, pd.DataFrame):
                self.data = self.filterData(self.data)
            elif isinstance(self.data, pd.Series):
                self.data = pd.Series(self.data, index = pd.DatetimeIndex(self.data.index))
            else:
                print("Data pulled from Glassnode is not series or dataframe. Returning data for you to look at. ")
                return self.data

        elif self.source.lower() == 'abs_tables':
            print("This source will return a pandas dataframe, not a series. It is therefore not suitable for this method. Use 'abs_series' instead.")
            return None

        ##### Start ABS block ######   
        elif self.source.lower() == 'abs_series'.lower():  
            abs_path = parent+fdel+"User_Data"+fdel+"ABS"+fdel+"Full_Sheets"
            #Data codes for abs_series are input in the format: series_id,catalog_num, where catalog_num is the ABS catalogue number
            # Alternatively: series_id,excel_file_name for local Excel files
            # Supply id in the form of tuple like that in order to load an excel file from the Full_Sheets folder instead of getting data from ABS. 
            split = self.data_code.split(',', maxsplit=1)
            
            if len(split) > 1:
                self.data_code = split[0].strip()
                self.exchange_code = split[1].strip()  # Can be either catalog_num or excel_file_name
            
                # Check if exchange_code is an Excel file (contains .xlsx or .xls)
                if self.exchange_code.endswith('.xlsx') or self.exchange_code.endswith('.xls'):
                    # Local Excel file mode
                    excel_path = abs_path+fdel+self.exchange_code if not os.path.isabs(self.exchange_code) else self.exchange_code
                    print(f"Using ABS excel file: {excel_path} to find series id: {self.data_code}")
                    series, SeriesInfo = abs_series_by_r.get_abs_series_from_excel(excel_file_path=excel_path, series_id=self.data_code)
                    
                else:
                    # Assume it's a catalog number - use Python readabs
                    print(f"Getting ABS series {self.data_code} from catalog {self.exchange_code}")
                    try:
                        series, SeriesInfo = abs_series_by_r.abs_download_with_r(series_id=self.data_code)

                    except Exception as e:
                        print(f"R script readabs failed, falling back to python readabs: {e}")
                        series, SeriesInfo = abs_series_by_r.get_abs_series_python(
                            series_id=self.data_code,
                            catalog_num=self.exchange_code,
                            verbose=False)
                
            else:
                # Series ID only - attempt to use Python readabs (requires catalog number to be determined)
                print(f"Getting ABS series directly for series id: {self.data_code}")
                try:
                    series, SeriesInfo = abs_series_by_r.abs_download_with_r(series_id=self.data_code)

                except Exception as e:
                    print(f"R script readabs failed, falling back to python readabs: {e}")
                    series, SeriesInfo = abs_series_by_r.get_abs_series_python(series_id=self.data_code, verbose=False)
            
            # Data obtained now process it
            self.data = series
            self.SeriesInfo = SeriesInfo if isinstance(SeriesInfo, pd.Series) else pd.Series(SeriesInfo)
            self.SeriesInfo = self.SeriesInfo.astype('object')  # Ensure object dtype
            self.dataName = series.name if hasattr(series, 'name') else self.data_code
            
            # Enhance SeriesInfo with more detailed information
            if hasattr(series, 'name') and series.name:
                self.SeriesInfo['title'] = series.name
            ### End ABS block ######

        elif self.source.lower() == 'bea':
            req = self._parse_bea_request()
            print(f"Pulling BEA series. dataset={req['dataset']}, table={req['table_code']}, series={req['series_code']}, freq={req['frequency']}")

            table_data, table_meta = self._load_bea_table(req['dataset'], req['table_code'], req['frequency'])
            series, line_desc = self._extract_bea_series(
                table_data=table_data,
                table_meta=table_meta,
                series_code=req['series_code'],
                line_description=req['line_description']
            )

            series = series.sort_index()
            series = series[self.start_date:self.end_date]
            self.data = pd.Series(series, name=line_desc)
            self.dataName = f"{req['dataset']}|{req['table_code']}|{req['series_code'] or line_desc}"

            units = table_meta.get('CL_UNIT') if isinstance(table_meta, pd.Series) else None
            if units is None:
                units = table_meta.get('METRIC_NAME') if isinstance(table_meta, pd.Series) else None

            self.SeriesInfo = pd.Series({
                'id': self.dataName,
                'title': line_desc,
                'source': 'bea',
                'original_source': 'Bureau of Economic Analysis',
                'Datasetname': req['dataset'],
                'TableName': req['table_code'],
                'Frequency': req['frequency'],
                'frequency': req['frequency'],
                'Series Code': req['series_code'],
                'units': units,
                'start_date': self.data.index.min().date() if len(self.data) else None,
                'end_date': self.data.index.max().date() if len(self.data) else None,
                'length': int(self.data.dropna().shape[0])
            }, dtype='object')

        elif self.source.lower() == 'rba_tables':
            print("This source will return a pandas dataframe, not a series. It is therefore not suitable for this method. Use 'rba_series' instead.")
            return None

        elif self.source.lower() == 'rba_series':
            out_df = abs_series_by_r.get_rba_series(series_id = self.data_code)
            print(out_df)
            series = out_df.set_index("date",  drop=True)["value"].rename(self.data_code)
            self.data = series
            series_info = out_df.drop(columns = ["value"]).rename(columns = {"date":"start_date"}).head(1).squeeze()
            self.SeriesInfo = series_info
            if "series" in self.SeriesInfo.index:
                self.data = self.data.rename(self.SeriesInfo["series"])

        elif self.source.lower() == 'tedata':
            scraped = ted.scrape_chart(id = self.data_code, use_existing_driver=True)
            self.data = scraped.series
            self.SeriesInfo = scraped.series_metadata

        elif self.source == "saveddata":
            path = parent + fdel + "User_Data" + fdel + "SavedData"
            self.data = pd.read_excel(path+fdel+self.data_code+".xlsx", sheet_name = "Closing_Price", index_col=0)
            self.SeriesInfo = pd.read_excel(path+fdel+self.data_code+".xlsx", sheet_name = "SeriesInfo", index_col=0)
        
        elif self.source == "hdfstores":
            path = parent + fdel + "User_Data" + fdel + "hd5s"
            self.data = pd.read_hdf(path+fdel+self.data_code+".hd5", key = "data")
            self.SeriesInfo = pd.read_hdf(path+fdel+self.data_code+".hd5", key = "metadata")

        else:
            if self.source in self.supported_sources and self.source not in self.added_sources:
                print("Your specified source will be supported but the coding has not been done yet, sorry sucker..") 
                return "Sorry sucker."
            else:
                print("Your specified source is not supported, get the fuck out of town you cunt.") 
                return "A kick in the nutz"

    def get_data(self, source: str, data_code: str, start_date: str = "1800-01-01", exchange_code: str = None, 
                 end_date: str = datetime.date.today().strftime('%Y-%m-%d'), data_freq: str = "1d", dtype: str = "close",
                 capitalize_column_names: bool = False,
                 asset: str = "BTC", resolution: str = '24h', format: str = 'json', timeout: int = 60):
        """
        The get_data method is responsible for pulling data from various sources. Pulled data will be stored in 3 important 
        attributes: 
        
        - self.data -> Contains the data as a pandas DataFrame or Series.
        - self.SeriesInfo -> contains metdata about the data series pulled, as a series.
        - self.dataName -> contains the name of the data series pulled, string. 

        Parameters:
        - source: str, the source to pull data from, source options can be listed by printing self.added_sources attribute
        - data_code: str, the data code/ticker/id for the asset or data series you want to pull.
        - start_date: str YYYY-MM-DD format, the start date for the data series you want to pull.
        - exchange_code: str, the exchange code for the asset you want to pull data for, default is None. This applies to tv source only atm. 
        - end_date: str YYYY-MM-DD format, the end date for the data series you want to pull, default is to use today's date.
        - data_freq: str, the frequency of the data you want to pull, default is daily, formats of the string vary by source. Try "1w" for weekly maybe.
        - dtype: str, the type of data you want to pull, default is "close", other options are "OHLCV" for open, high, low, close, volume data.
        - capitalize_column_names: bool, default is False, if True, the column names of the data will be capitalized.
        - timeout: int, default 60 - timeout in seconds for the data pull operation
        """
        
        self.data_freq = data_freq
        self.source = source.lower()
        self.asset = asset
        self.resolution = resolution    
        self.format = format
        self.timeout = timeout
        self.check_key()

        if self.source not in self.supported_sources:
            print('The data source: ', "\n", source, "\n", 'is not supported. You must choose from the following sources: \n', self.supported_sources)
            print("Your specified source is not supported, get the fuck out of town you cunt.") 
            return

        self.data_code = data_code
        if exchange_code is not None:
            self.exchange_code = exchange_code
        else:
            self.exchange_code = "N/A"

        self.start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        self.end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d') 
        self.SeriesInfo = pd.Series([],dtype=str)
        self.dataName = data_code
        self.d_type = dtype 

        print("Looking for data from source: ", self.source, "data code: ", self.data_code)
        
        # Run pull_data in a separate thread and enforce timeout using futures.
        # This avoids using `signal` (which only works in main thread) and is
        # safe to call from Jupyter notebooks or worker threads.
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                future = ex.submit(self.pull_data)
                # future.result will raise concurrent.futures.TimeoutError on timeout
                future.result(timeout=self.timeout)
        except concurrent.futures.TimeoutError:
            print(f"Data pull timed out after {self.timeout} seconds for {self.data_code} from {self.source}")
            self.data = pd.Series([f"Data pull timed out after {self.timeout} seconds"],
                                  name=f"Timeout_{self.data_code}", index=[0])
            return
        except Exception as e:
            # propagate real errors from pull_data
            raise e

        if capitalize_column_names and dtype != "close" and len(self.data.columns) > 0:
            self.data.columns = self.data.columns.str.capitalize()

    def filterData(self, TheData: pd.DataFrame):
        """Filter a multi-column OHLCV DataFrame down based on ``self.d_type``.

        Depending on the requested dtype:
          - 'OHLCV': keeps Open/High/Low/Close/Volume columns.
          - 'close': extracts just the Close column as a named pd.Series.
          - anything else: keeps the full DataFrame.

        The result is stored in ``self.data``.

        Args:
            TheData: Raw price DataFrame with capitalizable column names.
        """
        TheData.columns = TheData.columns.str.capitalize()
        columns_to_keep = ['Open', 'High', 'Low', 'Close', 'Volume']
        columns_to_keep = list(set(TheData.columns) & set(columns_to_keep))

        TheData = pd.DataFrame(TheData, index = pd.DatetimeIndex(TheData.index))
        if self.d_type == 'OHLCV':
            self.data = TheData[columns_to_keep]

        elif self.d_type == 'close':    
            self.data = pd.Series(TheData['Close'], name = self.dataName)       
        else:
            self.data = TheData        

class glassnode_data(object):
    """Standalone helper for pulling on-chain crypto data from the Glassnode API.

    Can be used independently of the ``dataset`` class.  Loads the master
    metrics list on init and exposes ``chosen_met()`` + ``get_data()`` to
    select a metric and fetch its time-series.
    """

    def __init__(self):
        """Load the Glassnode metrics catalogue and API keys."""
        self.metric_df = pd.read_csv(wd+fdel+"Glassnode"+fdel+"Saved_Data"+fdel+"GN_MetricsList.csv", index_col=0)
        self.metric_list = pd.Series([str(path).split("/")[-1] for path in self.metric_df["path"]])
        self.keys = Utilities.api_keys().keys

    def chosen_met(self, metric):
        """Select a Glassnode metric and resolve its path, supported assets, and resolutions.

        Args:
            metric: Short metric name (e.g. 'price_usd_ohlc', 'sopr').
                    Must match an entry in the GN_MetricsList catalogue.
        """
        self.metric = metric
        metIndex = (self.metric_list == metric).idxmax()
        self.metric_path = self.metric_df['path'].iloc[metIndex]
        ass_json = json.loads(str(self.metric_df['assets'].iloc[metIndex]).strip().replace("'", '"'))
        self.met_assets = [asset["symbol"] for asset in ass_json]
        self.met_currs = [curr for curr in self.metric_df['currencies'].iloc[metIndex]]
        self.met_resolutions = [res for res in self.metric_df['resolutions'].iloc[metIndex]]
        self.met_formats = [form for form in self.metric_df['formats'].iloc[metIndex]]
        dom_json = json.loads(str(self.metric_df['paramsDomain'].iloc[metIndex]).strip().replace("'", '"'))
        self.met_domain = [dom for dom in dom_json.values()]

    def get_data(self, asset: str = "BTC", tier: int = 1, resolution: str = '24h', format: str = 'csv', paramsDomain: str = "a"):
        """Fetch time-series data for the currently selected Glassnode metric.

        Populates ``self.data`` with the returned DataFrame/Series and
        ``self.seriesInfo`` with descriptive metadata.

        Args:
            asset: Crypto asset ticker (e.g. 'BTC', 'ETH').
            tier: Glassnode API tier level.
            resolution: Time resolution string (e.g. '24h', '1h', '10m').
            format: Response format — 'csv' or 'json'.
            paramsDomain: Domain parameter for the Glassnode API.
        """
        params = {'a': asset,'i': resolution,'f': format,'api_key': self.keys['glassnode']} 
        self.data = GlassNode_API.GetMetric(path = self.metric_path, APIKey = self.keys['glassnode'], params = params)
        self.seriesInfo = pd.Series({"source": "glassnode", "metric_short": self.metric, "metric_full": self.metric_path, "asset": asset,
                           "tier": tier, "resolution": resolution, "format": format, "paramsDomain": paramsDomain} , name = "metadata_gn")
               
if __name__ == "__main__":
    
    me_data = dataset()
    me_data.get_data('yfinance', 'AAPL',"2005-01-01", dtype="OHLCV")
    print(me_data.data)
    print(me_data.SeriesInfo)
    # print(me_data.data, me_data.SeriesInfo, me_data.dataName, me_data.data.index, type(me_data.data.index))
    # me_data = dataset(source = 'abs', data_code = 'A3605929A',start_date="2011-01-01")
    # print(me_data.data, me_data.SeriesInfo, me_data.dataName)
    # me_data = dataset()
    # me_data.get_data(source = 'tv', data_code = 'NQ1!,CME', start_date="2008-01-01")
    # print(me_data.data, me_data.SeriesInfo, me_data.dataName)

    #DXY = PriceImporter.ReSampleToRefIndex(DXY,Findex,'D') 
    #print(me_data.data.iloc[len(me_data.data)-1])
    # keyz = Utilities.api_keys()
    # res = PriceImporter.FREDSearch("Gross",apiKey=keyz.keys['fred'])
    # print(res)
    # data = PriceImporter.tv_data("SPY", "NSE", search=True)
    # print(data.seriesInfo)
   
    
    # print(full_results1['symbol'][0], full_results1['exchange'][0])
    # data = yf('AAPL')
    # print(data.get_financial_data('annual'))
    #.get_historical_price_data('2020-01-01', '2020-01-10', 'daily')
    #print(data)
    # tvd = PriceImporter.tv_data("BTCUSD", 'INDEX')#, username="NoobTrade181", password="4Frst6^YuiT!")
    # #tvd.all_data_for_timeframe(timeframe = "4H")
    # datas = tvd.tv.exp_ws("NQ", exchange = 'CME', interval=PriceImporter.TimeInterval("4H"),n_bars=5000)
    # print(datas)
     
    # gn = glassnode_data()
    # gn.chosen_met("price_usd_ohlc")
    # print(gn.met_assets, gn.met_resolutions, gn.met_formats, gn.met_currs, gn.met_domain)
    # gn.get_data(asset = "BTC", resolution = '24h', format = 'json', paramsDomain = "a")
    # print(gn.data)

    # me_data = dataset()
    # me_data.get_data(source = 'glassnode', data_code = 'price_usd_ohlc,BTC,24h',start_date="2011-01-01", dtype="OHLCV")
    # print(me_data.data, me_data.SeriesInfo, me_data.dataName)

    # tv_data = dataset()
    # tv_data.get_data("tv", "ES1!", "1998-01-01", exchange_code="CME")
    # print(tv_data.data, tv_data.SeriesInfo, tv_data.dataName)








