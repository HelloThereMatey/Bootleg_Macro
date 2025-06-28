import subprocess
import pandas as pd
import json
from pprint import pprint
import re
import os

wd = os.path.dirname(os.path.abspath(__file__))
fdel = os.path.sep

# Get the global node_modules directory
node_path = subprocess.check_output('npm root -g', shell=True).decode().strip()

# Add the global node_modules directory to the NODE_PATH environment variable
os.environ['NODE_PATH'] = node_path

#print(os.environ['NODE_PATH'])

def remove_ansi_escape_sequences(s):
    ansi_escape_pattern = re.compile(r'\x1b\[[0-9;]*m')
    return ansi_escape_pattern.sub('', s)

def js_search_tv(searchstr: str) -> dict:
    data_str = json.dumps(searchstr)

    # Prepare environment with NODE_PATH
    env = os.environ.copy()
    env['NODE_PATH'] = node_path

    # Run Node.js process and pass data
    result = subprocess.run(['node', wd+fdel+'searchTV_js.js'], 
                          input=data_str, text=True, capture_output=True, env=env)
    print("Return code:", result.returncode)

    if result.returncode != 0:
        print("Error:", result.stderr)
        return {"error": result.stderr, "success": False}
    
    try:
        # Parse the JSON response directly
        response = json.loads(result.stdout.strip())
        print("Parsed JSON response:", response)
        
        # Convert list to numbered dictionary format if it's a list
        if isinstance(response, list):
            full_dict = {}
            for i, item in enumerate(response):
                full_dict[i] = item
            return full_dict
        else:
            return response
            
    except json.JSONDecodeError as e:
        print("Failed to parse JSON response:", e)
        print("Raw output:", result.stdout)
        return {"error": "JSON parse error", "success": False}

def js_search_yf(searchstr: str) -> str:
    data_str = json.dumps(searchstr)

    # Prepare environment with NODE_PATH
    env = os.environ.copy()
    env['NODE_PATH'] = node_path

    # Run Node.js process and pass data
    result = subprocess.run(['node', wd+fdel+'yfinance2_js.js'], 
                          input=data_str, text=True, capture_output=True, env=env)
    if result.returncode != 0:
        print("Error:", result.stderr)
        quit()
    else:
        print("Success with yfinance request.")
    #print("Return code:", result.returncode, "\n\n", result.stderr, "\n\n", 'stdout:', result.stdout, result.stdout)

    return result.stdout

def process_yf_stdout(input: str) -> dict:
    
    json_form = json.loads(input)
    news = json_form['news']
    tickers = json_form['quotes']
    
    df = pd.DataFrame() 
    i = 0
    for res in tickers:
        ser = pd.Series(res)
        if i == 0:
            df = ser
        else:
            df = pd.concat([df, ser], axis=1)
        i += 1
    df = df.T.reset_index(drop=True)
    df.index.rename("Result #", inplace=True)
    
    outdict = {"News": news, "Tickers": tickers, "tickers_df": df}
    return outdict

def search_yf_tickers(searchstr: str) -> tuple:
    yf_results = js_search_yf(searchstr)
    formatted = process_yf_stdout(yf_results)

    return formatted

def js_search_yf_enhanced(searchstr: str) -> dict:
    """Enhanced Yahoo Finance search using Node.js script with better error handling"""
    data_str = json.dumps(searchstr)

    # Prepare environment with NODE_PATH
    env = os.environ.copy()
    env['NODE_PATH'] = node_path

    # Run Node.js process and pass data via stdin
    result = subprocess.run(['node', wd+fdel+'yfinance2_js.js'], 
                          input=data_str, text=True, capture_output=True, env=env)
    
    if result.returncode != 0:
        print("Error in yfinance search:", result.stderr)
        return {"quotes": [], "news": [], "error": result.stderr}
    
    try:
        response = json.loads(result.stdout)
        return response
    except json.JSONDecodeError as e:
        print("Failed to parse JSON response:", e)
        return {"quotes": [], "news": [], "error": "JSON parse error"}

def js_get_historical_data(symbol: str, start_date: str, end_date: str, interval: str = "1d") -> dict:
    """Get historical data using Node.js Yahoo Finance script"""
    # Convert dates to timestamps
    start_timestamp = int(pd.Timestamp(start_date).timestamp())
    end_timestamp = int(pd.Timestamp(end_date).timestamp())
    
    # Prepare environment with NODE_PATH
    env = os.environ.copy()
    env['NODE_PATH'] = node_path
    
    # Run Node.js process with command line arguments
    cmd = ['node', wd+fdel+'yfinance2_js.js', 'fetch', symbol, 
           str(start_timestamp), str(end_timestamp), interval]
    
    result = subprocess.run(cmd, text=True, capture_output=True, env=env)
    
    if result.returncode != 0:
        print("Error fetching historical data:", result.stderr)
        return {"success": False, "error": result.stderr, "data": []}
    
    try:
        response = json.loads(result.stdout)
        return response
    except json.JSONDecodeError as e:
        print("Failed to parse JSON response:", e)
        return {"success": False, "error": "JSON parse error", "data": []}

def convert_js_data_to_pandas(js_data) -> pd.DataFrame:
    """Convert JavaScript data to pandas DataFrame - handles both historical data and search results"""
    
    # Handle case where js_data is a dict with success/data structure (historical data)
    if isinstance(js_data, dict) and 'success' in js_data:
        if not js_data.get("success", False) or not js_data.get("data"):
            return pd.DataFrame()
        
        data = js_data["data"]
        
        # Handle case where data is a list of dictionaries (JSON format)
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            # Handle case where data is already a dictionary that can be converted to DataFrame
            df = pd.DataFrame(data)
        else:
            # Data is already a pandas DataFrame or other format
            df = pd.DataFrame(data)
        
        if not df.empty:
            # Ensure Date column exists and convert to datetime (for historical data)
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                df.set_index('Date', inplace=True)
            elif 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                
            # Convert numeric columns (for historical data)
            numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume', 'AdjClose']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
        print("Converted historical data to DataFrame:", df)
        
        return df
    
    # Handle case where js_data is directly a list (like TV search results)
    elif isinstance(js_data, list) and len(js_data) > 0:
        df = pd.DataFrame(js_data)
        return df
    
    # Handle case where js_data is a dict but not the success/data structure
    elif isinstance(js_data, dict):
        # Try to convert dict directly to DataFrame
        try:
            df = pd.DataFrame(js_data)
            return df
        except:
            # If that fails, try to convert as a single-row DataFrame
            df = pd.DataFrame([js_data])
            return df
    
    # Default case - try to convert whatever it is to DataFrame
    else:
        try:
            df = pd.DataFrame(js_data)
            return df
        except:
            return pd.DataFrame()

if __name__ == "__main__":

    searchstr = "ES1!"
    # print("Searching trading view data for:", searchstr)
    
    #Con  vert Python dictionary to JSON string
    pprint(js_search_tv(searchstr))

    # print("Searching yfinance data for:", searchstr)
    # #Convert Python dictionary to JSON string
    # yf_results = js_search_yf(searchstr)
    # formatted = process_yf_stdout(yf_results)
    # news_res = formatted['News']
    # tickers_dict = formatted['Tickers']
    # tick_df = formatted['tickers_df']
    # print(news_res,"\n\n", tickers_dict, "\n\n", tick_df, "\n\n", type(news_res), type(tickers_dict), type(tick_df))

    # # print("Testing enhanced yfinance search for:", searchstr)
    # # yf_search_results = js_search_yf_enhanced(searchstr)
    # # pprint(yf_search_results)
    
    # print(f"Testing historical data retrieval for {searchstr}:")
    # hist_data = js_get_historical_data(searchstr, "1999-01-01", "2025-06-01", "1d")
    # print("Raw historical data response:", hist_data)
    # if hist_data.get("success"):
    #     df = convert_js_data_to_pandas(hist_data)
    #     print("Converted DataFrame:")
    #     print(df)
    # else:
    #     print("Failed to get historical data:", hist_data.get("error"))
    # print(f"Testing historical data retrieval for {searchstr}:")
    # hist_data = js_get_historical_data(searchstr, "1999-01-01", "2025-06-01", "1d")
    # print("Raw historical data response:", hist_data)
    # if hist_data.get("success"):
    #     df = convert_js_data_to_pandas(hist_data)
    #     print("Converted DataFrame:")
    #     print(df)
    # else:
    #     print("Failed to get historical data:", hist_data.get("error"))


