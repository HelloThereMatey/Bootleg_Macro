import requests
import pandas as pd
# monkeypatch using faster simplejson module
import numpy as np
import matplotlib.pyplot as plt
import os
import re
import sys
import io

# monkeypatch using standard python json module
import json
pd.io.json._json.loads = lambda s, *a, **kw: json.loads(s)

wd = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(wd); grandpa = os.path.dirname(parent)
fdel = os.path.sep
sys.path.append(grandpa)

from MacroBackend import Utilities
KeysPath = parent+fdel+'SystemInfo'+fdel+'API_Keys.json'

keys = Utilities.api_keys().keys
API_KEY = keys['glassnode']

def unpack_dict_columns(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df, pd.Series):
        if df.apply(lambda x: isinstance(x, dict)).any():
            df = df.apply(pd.Series)
    else:
        for col in df.columns:
            if df[col].apply(lambda x: isinstance(x, dict)).any():
                # Unpack dictionaries into new DataFrame
                unpacked = df[col].apply(pd.Series)
                # Drop the original column from the DataFrame
                df = df.drop(col, axis=1)
                # Concatenate the original DataFrame with the new DataFrame
                df = pd.concat([df, unpacked], axis=1)
    return df

def search_series(search_string, series:pd.Series):  ##This unction will be used to search throuigh the list of glassnode metrics.
    matches = []; match_indices = []; i = 0
    search_regex = re.compile(search_string.replace('*', '.*'), re.IGNORECASE)
    for s in series:
        if search_regex.search(s):
            matches.append(s)
            match_indices.append(i)
        i += 1
    return matches, match_indices

def UpdateGNMetrics(APIKey:str) -> pd.DataFrame: #Use this to occaisonally update the excel file containing the list of all GN metrics. 
    print('Updating excel file that has the list of all GlassNode metrics/endpoints.....')
    #make API request
    res = requests.get('https://api.glassnode.com/v2/metrics/endpoints', params={'a': 'BTC', 'api_key': APIKey})
    #convert to pandas dataframe
    df = pd.read_json(res.text, convert_dates=['t'])
    print('File updated, here is a preview:', df)
    return df

########### Active code below ###################################
def SearchMetrics(MetricsList, SearchString:str): 
    if str(type(MetricsList) =="<class 'str'>"):  
        df = pd.read_csv(MetricsList, index_col=0)  #Load the GNMetrics list as pandas dataframe. 
        df.index.rename('Index',inplace=True) 
    elif str(type(MetricsList) == "<class 'pandas.core.frame.DataFrame'>"):
        pass
    else:
        print('List must be supplied as a dataframe or as a str containing a path to an excel file to load the dataframe from.')    
        quit()

    #Set your serach term here. Wildcard characters (*) not needed. Will list all partial matches. Case insensitive. 
    print("Loading gn metric df.....: ", df.head())
    search, indices = search_series(SearchString, df['path'])  #search 
    Metrics_df = pd.DataFrame(df.iloc[indices])
    return Metrics_df

def GetMetric(path:str,APIKey:str = None, params:dict=None, format: str='json'):
    split = path.split('/'); name = split[len(split)-1]
    print('Getting data for GN metric, ',name,', from Glassnode API.')
    url = 'https://api.glassnode.com'+path
    print('Making request to url: ',url)

    if params is not None:
        format = params.get("f", "json")
        key = params.get("api_key", APIKey)
        if key is None:
            print("No API key provided in params. We need API key yo. Pull out........")
            quit()
        else:
            params['api_key'] = key
        r = requests.get(url, params)
    else:    
        r = requests.get(url, params={'a': 'BTC', 'api_key': APIKey, 'f': format})
    if r.status_code != 200:
        print('Failure! What went wrong?',r.status_code, r.reason)
        print("If you have an error code in the 400's, the error is probably due to an invalid API key.\n\
        Glassnode makes you recycle API keys every few weeks or so. Login to your account on Glassnode & check your current API key.\n\
        If a different API key is shown, copy that new key to the API_KEY variable at top of 'Glassnode_API.py'.")
        quit()
    else:
        print('Success with getting data from GlassNode API.')    

    if format == 'csv':
        print("csv format expected, reading csv data into pandas dataframe....")
        df = pd.read_csv(io.StringIO(r.text))
    else:
        json_obj = json.loads(r.text)
        df = pd.DataFrame(json_obj)
        print("json format expected, reading json data into pandas dataframe....")
    
    if 't' in df.columns:
        df.rename(columns={'t': 'timestamp'}, inplace=True)
    elif "v" in df.columns:
        df.rename(columns={'v': name}, inplace=True)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    df.set_index('timestamp', inplace=True, drop=True); df.index.rename('datetime',inplace=True) 

    ### Unpack columns that are dicts....
    df = unpack_dict_columns(df)

    if len(df.columns) < 2 and isinstance(df, pd.DataFrame):
        df = pd.Series(df.squeeze(), name = name)
        print("Returning the glassnode data as a Series..")
    else:
        print("Returning the glassnode data as a DataFrame..") 
  
    return df

if __name__ == '__main__':
   
   print("Glassnode api key: ", API_KEY)
   has_rib = '/v1/metrics/indicators/hash_ribbon'
   price_ohlc = '/v1/metrics/market/price_usd_ohlc'
   price_close = '/v1/metrics/market/price_usd_close'
   df = GetMetric(price_close, params = {'a': 'BTC', 'i': '24h', 'f': 'json', "api_key": keys['glassnode']})
   print(df)