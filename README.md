# Plebs_Macro
Open sourcing financial data that is generally hidden behind high paywalls. 

Multiple tools for obtaining and then charting and comparing economic data with asset price data. Has two aggregated liquidity indexes that you won't find elsewhere for free. Tools:
- Generic Charting tool:
    - Chart up to 5 traces on the same chart on up to 5 different axes.Transform data to first order derivatives, year on year % change, 6 month annualized etc.
    - Smooth data with MA's. Add bars for recessions.
    - Decent generic charting tool for display of macrioeconomic data. 
- Correlation tool:
    - Look at correlation between any two datasets. 
- Central bank global money index.
    - Aggregated customizable index that shows the sum of the major central bank balance sheets. Included more elaborate index for the Fed (Net liquidity). Net liquidity metric formulation devised by 42 Macro, see info below. 
    - Compare this index with up to 5 comparison assets. 
    - This script is the most developed & best to start with this one. 
- Aggregated global M2 money supply index.
    - This takes M2 money supply data for the top 50 economies and aggregates. Check it out. 

 Installation: 
     - Download the repo as zip file. Unzip to any location. Change the folder name from "Plebs_Macro-main" to "Plebs_Macro".
     - Install the required packages if not already present. In terminal:
        - cd wd      (where wd is your Plebs_Macro directory full path).
        - pip3 install -r requirements.txt   (pip on windows pip3 on mac/ linux) - That will install the python modules listed in requirements.txt. 
        - set working directory to folder containg the tool you wanna use (e.g cd ...............Plebs_Macro/NetLiquidity)
        - Fill in the necessary parameters in the control excel file. Save file.
        - Run script (e.g enter 'python3 ShowNetLiq.py' into terminal when working directory set to Plebs_Macro/NetLiquidity). 
        - Could alternatively be run in an editor such as VS code or pycharm. 
     
    
     
Controlling tools:
    - All of the tools are controlled by excel sheets (.xlsx). 
    - Fill in the indicated cells in each sheet and then run the corresponding script. 
    - Usage information is found in each excel sheet. 
    - A free excel alternative such as libre office can be used but make sure that the file type is .xlsx. 

USD NET LIQUIDITY SCRIPT 
    The net lqiuidity metric (NLQ) was originally formulated by Darius Dale and 42Macro, much respect DD, 42 Macro is best in class. If you can afford it, you're best off to just get a 42 Macro subscription. If however, you are a low-time preferenced, humble, sat-stacking pleb that would rather use that money to stack sats and doesn't mind getting your hands dirty with coding and data diving, then this approach is for you. 
    The net liquidity time series is the Fed balance sheet (FedBal) - the balance in the reverse repo facility (RevRep) - the treasury general account (TGA). 
    The three series are available from FRED and this script pulls these series from FRED, does the necessary arithmetic and displays NLQ along with 1-5 comparison assets with data sourced from a range of free price history providers, inlcuding yahoo finance, google finance and trading view. 
    FedBal is updated on a weekly basis while, revrep and TGA have daily updates of their balance (mon-fri). RevRep series from FRED (RRPONTSYD) is a series with daily frequency while the TGA series from FRED is a weekly series (average of the week). In order to provide more rapid updating, I'm taking the TGA balance data from the treasury API for the TGA series. 
    The resultant net liquidity series makes significant moves on a daily basis when TGA and RevRep balances move significantly. NLQ can be viewed on trading view yet only with weekly frequency. This script is possibly a better way to view NLQ as it updates on a daily basis just like the original 42 macro NLQ series.
    Apart from standard, well vetted, python packages, my script uses another script 'PriceImporter' that contains my functions for pulling price history from different APIs. 
    There is also a package 'tvDatafeed' which is used and the files of which are included in this repo. This package is great and allows us to pull data for any asset that you can find on tradingview from tradingview itself without needing a subscription. I'm quite sure that it is safe and have been using it for months. I suspect that it doesn't get hosted on PyPi as the scraping of data from sites can be legally dubious in some jursidictions. Anyhow teh script could operate fine without it, you'd just not be able to get data from TV and would need to modify all references to the module in the script. 
    
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
V1.4:
    - Added the generic chating tool and the aggregated global M2 toolz. 

     
TROUBLESHOOTING:
    - If you get an error message "UserWarning: Matplotlib is currently using agg, which is a non-GUI backend, so cannot show the figure.", you have a
    version of python that does not inculde the tkinter package. 
    - Install latest python with tkinter by entering into terminal:
        sudo apt-get install python3-tk
    - That should fix that issue.     
     
