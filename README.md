# Plebs_Macro
Open sourcing financial data that is generally hidden behind high paywalls. 

USD NET LIQUIDITY SCRIPT 
    The net lqiuidity metric (NLQ) was originally formulated by Darius Dale and 42Macro, much respect DD, 42 Macro is best in class. If you can afford it, you're best off to just get a 42 Macro subscription. If however, you are a low-time preferenced, humble, sat-stacking pleb that would rather use that money to stack sats and doesn't mind getting your hands dirty with coding and data diving, then this approach is for you. 
    The net liquidity time series is the Fed balance sheet (FedBal) - the balance in the reverse repo facility (RevRep) - the treasury general account (TGA). 
    The three series are available from FRED and this script pulls these series from FRED, does the necessary arithmetic and displays NLQ along with 1-5 comparison assets with data sourced from a range of free price history providers, inlcuding yahoo finance, google finance and trading view. 
    FedBal is updated on a weekly basis while, revrep and TGA have daily updates of their balance (mon-fri). RevRep series from FRED (RRPONTSYD) is a series with daily frequency while the TGA series from FRED is a weekly series (average of the week). In order to provide more rapid updating, I'm taking the TGA balance data from the treasury API for the TGA series. 
    The resultant net liquidity series makes significant moves on a daily basis when TGA and RevRep balances move significantly. NLQ can be viewed on trading view yet only with weekly frequency. This script is possibly a better way to view NLQ as it updates on a daily basis just like the original 42 macro NLQ series.
    Apart from standard, well vetted, python packages, my script uses another script 'PriceImporter' that contains my functions for pulling price history from different APIs. 
    There is also a package 'tvDatafeed' which is used and the files of which are included in this repo. This package is great and allows us to pull data for any asset that you can find on tradingview from tradingview itself without needing a subscription. I'm quite sure that it is safe and have been using it for months. I suspect that it doesn't get hosted on PyPi as the scraping of data from sites can be legally dubious in some jursidictions. Anyhow teh script could operate fine without it, you'd just not be able to get data from TV and would need to modify all references to the module in the script. 
    
    How to use scipt: 
     - Place Plebs_Macro project folder where you wish. Set working directory to PlebsMacro/NetLiquidity.
     - Install the necessary modules using requirements.txt - 'pip install -r requirements.txt' enter in terminal. 
     - Set your input parameters in the excel file 'NetLiquidityInputParams.xlsx'. Correlation will be calculated between NLQ & the asset in slot #1 in            this spreadsheet. 
     - Run script.
V1.1 update:
    - One can look at YoY % change for assets and NLQ. Other features have been added and are outlined in the excel file. 
    - There is now also a more generic script for looking at correlations between any two assets. This is in the folder PairCorrelation. Use
    script 'TheCorellatooorrr_V2.py' in a similar way to the NetLiqudity script, with input parameters set in the Input excel file in that folder. 
    - MacroBackend folder now contains all of the utility scripts for pulling price data and formatting matplotlib charts etc. 
V1.2:
    - Added option to pull data for the Bank of Japan Balance sheet in USD and add to NLQ series. 
    - For this, BOJ bal. sheet data is pulled from from FRED (JPNASSETS, monthly data series) & JPYUSD FX data pulled from trading view. The two are   convolved to produce a BOJ bal. sheet series with daily frequency measured in USD. This is then added to NLQ. 

A more detailed usage guide can be found here in my twitter threads about the NLQ script: 
https://twitter.com/Tech_Pleb/status/1619542486208372737?s=20&t=lwqXKHnHwTkcF2V1RMnzBg
https://twitter.com/Tech_Pleb/status/1622916354008584192?s=20&t=k0nnXAlNTvv5iiISzwvyAA
- Since V1.1 the script uses the tkinter package. It may be necessary to install this using the command:
sudo apt-get install python3-tk
- That will install tkinter. This fixes a bug where matplotlib does not display the figures. On windows use python inplace of python3. 

V1.3: 
    - Big upgrades here. Added option to add bal. sheets of the other 4 main world CB's to create a 'global liquidity'index. 
    - Upgrades in the usability of the excel control input params file. Much easier to use and you have more possibilities. 
    Get at it. 

     
     
