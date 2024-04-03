import requests
import pandas as pd
# monkeypatch using faster simplejson module
import numpy as np
import matplotlib.pyplot as plt
import os
import re
import sys

# monkeypatch using standard python json module
import json
pd.io.json._json.loads = lambda s, *a, **kw: json.loads(s)

wd = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(wd); grandpa = os.path.dirname(parent)
fdel = os.path.sep
sys.path.append(grandpa)
from MacroBackend import Utilities
KeysPath = parent+fdel+'SystemInfo'+fdel+'API_Keys.json'

if os.path.exists(KeysPath) and os.path.splitext(KeysPath)[1]:
    keys = open(parent+fdel+'SystemInfo'+fdel+'API_Keys.json')
    apikeys = dict(json.load(keys))
    API_KEY = apikeys['glassnode']
else:
    print('Need to set api key for glassnode in the API_Keys.json file at: ',KeysPath)
    Utilities.api_keys()

def search_series(search_string, series:pd.Series):  ##This unction will be used to search throuigh the list of glassnode metrics.
    matches = []; match_indices = []; i = 0
    search_regex = re.compile(search_string.replace('*', '.*'), re.IGNORECASE)
    for s in series:
        if search_regex.search(s):
            matches.append(s)
            match_indices.append(i)
        i += 1
    return matches, match_indices

def UpdateGNMetrics(APIKey:str) -> pd.DataFrame(): #Use this to occaisonally update the excel file containing the list of all GN metrics. 
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
        df = pd.read_excel(MetricsList)  #Load the GNMetrics list as pandas dataframe. 
        df.set_index(df.columns[0],inplace=True); df.index.rename('Index',inplace=True) 
    elif str(type(MetricsList) == "<class 'pandas.core.frame.DataFrame'>"):
        pass
    else:
        print('List must be supplied as a dataframe or as a str containing a path to an excel file to load the dataframe from.')    
        quit()

    #Set your serach term here. Wildcard characters (*) not needed. Will list all partial matches. Case insensitive. 
    search, indices = search_series(SearchString, df['path'])  #search 
    Metrics_df = pd.DataFrame(df.iloc[indices])
    return Metrics_df

def GetMetric(path:str,APIKey:str,params:dict=None):
    split = path.split('/'); name = split[len(split)-1]
    print('Getting data for GN metric, ',name,', from Glassnode API.')
    url = 'https://api.glassnode.com'+path
    print('Making request to url: ',url)
    if params is not None:
        r = requests.get(url, params)
    else:    
        r = requests.get(url, params={'a': 'BTC', 'api_key': APIKey})
    if r.status_code != 200:
        print('Failure! What went wrong?',r.status_code, r.reason)
        print("If you have an error code in the 400's, the error is probably due to an invalid API key.\n\
        Glassnode makes you recycle API keys every few weeks or so. Login to your account on Glassnode & check your current API key.\n\
        If a different API key is shown, copy that new key to the API_KEY variable at top of 'Glassnode_API.py'.")
        quit()
    else:
        print('Success. Here is a preview of the raw data: ',r.text[0:100])    
    #convert to pandas dataframe
    df = pd.read_json(r.text, convert_dates=['t'])
    split = path.split('/'); name = split[len(split)-1]
    df.set_index(df.columns[0],inplace=True)
    df.index.rename('Date',inplace=True); df.rename({'v':name},axis=1,inplace=True)
    if len(df.columns) < 2:
        df = pd.Series(df.squeeze(), name = name)
    else:
        print("Warning, this metric has more than one data column, we'll need to recode this.")
        print(df)
        quit()     
    return df
