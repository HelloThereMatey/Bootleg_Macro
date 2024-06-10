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

print(os.environ['NODE_PATH'])


def js_search_tv(searchstr: str) -> dict:
    data_str = json.dumps(searchstr)

    # Run Node.js process and pass data
    #result = subprocess.run(['node', 'pyinout.js'], input=data, text=True, capture_output=True).stdout.replace('\n', '').replace("'", "")
    result = subprocess.run(['node', wd+fdel+'searchTV_js.js'], input=data_str, text=True, capture_output=True)
    print("Return code:", result.returncode)

    if result.returncode != 0:
        print("Error:", result.stderr)
        quit()
    else:
        print("Output:", result.stdout.replace('\n', '').replace("'", ""))
        response = result.stdout.replace('\n', '').replace("'", "")

    returned = response[2::].split("{    ")

    full_dict = {}; j = 0
    for st in returned:
        split2 = st.split(",")
        i = 0
        outdict = {}
        for st2 in split2:
            if i == 0:
                text = st2
                # Using re.sub to remove the middle part between two colons
                modified_text = re.sub(r'([^:]*):[^:]*(:.*)', r'\1\2', text)
                st2 = modified_text.replace("}", "")
            i += 1
            line = st2.replace("}", "").strip()
            els = line.split(":")
            try:
                outdict[els[0]] = els[1]
            except:
                pass
        full_dict[j] = outdict
        j += 1
    del full_dict[0]    
    return full_dict

def js_search_yf(searchstr: str) -> str:
    data_str = json.dumps(searchstr)

    # Run Node.js process and pass data
    #result = subprocess.run(['node', 'pyinout.js'], input=data, text=True, capture_output=True).stdout.replace('\n', '').replace("'", "")
    result = subprocess.run(['node', wd+fdel+'yfinance2_js.js'], input=data_str, text=True, capture_output=True)
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

if __name__ == "__main__":

    searchstr = "AMZN"
    print("Searching trading view data for:", searchstr)
    
    #Con  vert Python dictionary to JSON string
    #pprint(js_search_tv(searchstr))

    print("Searching yfinance data for:", searchstr)
    #Convert Python dictionary to JSON string
    yf_results = js_search_yf(searchstr)
    formatted = process_yf_stdout(yf_results)
    news_res = formatted['News']
    tickers_dict = formatted['Tickers']
    tick_df = formatted['tickers_df']
    print(news_res,"\n\n", tickers_dict, "\n\n", tick_df, "\n\n", type(news_res), type(tickers_dict), type(tick_df))

    
