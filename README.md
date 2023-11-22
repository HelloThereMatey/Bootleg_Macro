# Bootleg_Macro
Open sourcing and charting financial data that you may've had to pay for before. We don't like paying stuff, no thanks.

Multiple tools for obtaining and then charting and comparing economic data with asset price data. Has two aggregated liquidity indexes that you won't find elsewhere for free. Tools:
- Generic Charting tool "Macro_Chartist":
    - Chart up to 5 traces on the same chart on up to 5 different axes.Transform data to first order derivatives, year on year % change, 6 month annualized etc.
    - Smooth data with MA's. Add bars for recessions.
    - Save chart templates to plot later with updated data. One can build up a big watchlist this way. 
    - Decent generic charting tool for display of macrioeconomic data. 
- Correlation tool:
    - Look at rolling correlations between any two data series. 
- Central bank global money index "NetLiquiity":
    - Aggregated customizable index that shows the sum of the major central bank balance sheets. Included more elaborate index for the Fed (Net liquidity). Net liquidity metric formulation devised by 42 Macro, see info below. 
    - Compare this index with up to 5 comparison assets. 
- Aggregated global M2 money supply index.
    - This takes M2 money supply data for the top 50 economies and aggregates. Check it out. 

 Installation: 
     - Install git on your machine if you don't already have it. 
     - Install python if you don't already have it. Mostly tested with Python 3.9.6. Can use: sudo apt-get install python3-tk on linux/mac.
     - Clone this repo to your desired directory:
         - e.g cd directory, where directory is where you want the repo.
         - git clone https://github.com/HelloThereMatey/Bootleg_Macro.git
     - Install the required packages if not already present. In terminal:
        - cd wd      (where wd is your Bootleg_Macro directory full path).
        - pip3 install -r requirements.txt   (pip on windows pip3 on mac/ linux) - That will install the python modules listed in requirements.txt. 
        - set working directory to folder containg the tool you wanna use (e.g cd ...............Bootleg_Macro/NetLiquidity)
        - Fill in the necessary parameters in the control excel file. Save file.
        - Run script (e.g enter 'python3 nlq.py' into terminal when working directory set to Bootleg_Macro/NetLiquidity). 
        - Could alternatively be run in an editor such as VS code or pycharm. 
     
Controlling tools:
    - All of the tools are controlled by an excel sheet which acts as a control panel (.xlsx). 
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

A more detailed usage guide can be found here in my twitter threads about the NLQ script: 
https://twitter.com/Tech_Pleb/status/1619542486208372737?s=20&t=lwqXKHnHwTkcF2V1RMnzBg
https://twitter.com/Tech_Pleb/status/1622916354008584192?s=20&t=k0nnXAlNTvv5iiISzwvyAA
- Since V1.1 the script uses the tkinter package. It may be necessary to install this using the command:
sudo apt-get install python3-tk
- That will install tkinter. This fixes a bug where matplotlib does not display the figures. On windows use python inplace of python3. 

     
TROUBLESHOOTING:
    - If you get an error message "UserWarning: Matplotlib is currently using agg, which is a non-GUI backend, so cannot show the figure.", you have a
    version of python that does not inculde the tkinter package. 
    - Install latest python with tkinter by entering into terminal:
        sudo apt-get install python3-tk
    - That should fix that issue.     
     
