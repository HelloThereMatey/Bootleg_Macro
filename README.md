# Bootleg Macro
Toolkit for sourcing financial data, analysis and charting. Our goal is to provide access to data that is usually hidden behinnd paywalls and to help with analysis. 
Includes web-scraping to get data from sources such as tradingview and yahoo finance without needing accounts at these sources. 
Provides interfaces that makes downloading macroeconomic data from easy to use sources such as FRED and much harder to deal with API's such as the BEA and ABS a breeze. 

Multiple tools for obtaining and then charting and comparing economic data with asset price data. Includes aggregated liquidity indexes such as aggregated Central bank balance sheets and global M2 aggregate. 

## Tools for the layman 
### These are python scripts controlled via an excel file and/or a PyQt6 based control panel. Usage is as easy as choosing settings and press run.
- Watchlist creation GUI. Search for data from the list of standard sources and build watchlists that can act as the basis for a financial study that can self-update over time.
    - The standard data sources currently implemented are:
        - MacroEconomic data: FRED, BEA, ABS (FRED and BEA require free API keys). 
        - Equity, Index, Commodity etc.: TradingView, Yahoo Finance. These are provided via data scraping. Nasdaq data link also included but requires free API key. 
        - Crypto: Coin Gecko, Glassnode (requires Glassnode subscription and API key). If you want data from this source & don't want to buy subscription, contact me and I'll setup an API to provide it to you.
        - More sources to come in the future, particularly via data scraping, this is what Bootleg Macro is all about. 
### Generic Charting tool "Macro_Chartist":
<img src="/examples/chartist.jpg" alt="Example of chartist output." width="1100"/>
Left: screenshot of the excel file control panel. Right: Example output chart. 


- Chart up to 5 traces on the same chart on up to 5 different axes or a dataframe of many traces on the same axis. 
- Transform data to first order derivatives, year on year % change, 6 month annualized etc.
- Smooth data with MA's. Add bars for recessions.
- Save chart templates to plot later with updated data. One can build up a watchlist this way. 
- Decent generic charting tool for display of macrioeconomic data. 
### Correlation tool:
- Look at rolling correlations between any two time series.
  
### Central bank global money index "NetLiquidity":
- Aggregated customizable index that shows the sum of the major central bank balance sheets. Included more elaborate index for the Fed (Net liquidity).
- Option to add other data sources such as the Bank-term funding program (BTFP balance), Fed remittances and governments deficits. 
- Compare the liquidity index with up to 5 comparison assets.

### Aggregated global M2 money supply index.
- This takes M2 money supply data for the top 50 economies and aggregates. Check it out. 

## Tools to be used in jupyter notebooks for finanical studies.
- Modules from the backend (MacroBackend) can be used flexibly inside environments such as Jupyter nb. This is the most powerful way to use the toolkit.
- Example notebooks are provided in User_Data/Research_notebooks. These show how to use GUI to build watchlist and then perform batch analysis routines on that list of time-series. 
- Combining this with the open BB platform toolkit [link here](https://github.com/OpenBB-finance/OpenBB) is especially powerful for financial/investment/quant studies.

## Installation: 
### Using command line in windows, mac or linux. 
Use Bash terminal in Linux/Mac.
For windows use Git Bash terminal which will let you execute the setup shell script (.sh file). Info on using git bash in windows terminal:
- [Setup git bash in windows terminal](https://www.commandlinewizardry.com/post/how-to-add-git-bash-to-windows-terminal), [Alternate link](https://www.educative.io/answers/how-to-install-git-bash-in-windows), You could also run a git bash terminal in VSCode. 

- Install [git](https://github.com/git-guides/install-git) on your machine if you don't already have it, this will include the git bash terminal for windows.
- Install miniconda environment manager, if not already running it [miniconda installation information](https://docs.conda.io/projects/miniconda/en/latest/).

 - Set your working directory where you would like to install the Bootleg_Macro_ repo. You can just type cd and then drag the folder where you want to install and drop on the terminal, to copy the path to that folder:

   `cd <your directory>`
 - Clone the Bootleg_Macro repo to your system:An example of virtual environment creation that may work well with here could be something like:

   `git clone https://github.com/HelloThereMatey/Bootleg_Macro.git`
   
 - Setup is done using a bash script "setup.sh" in Bootleg_Macro/setup folder. This will create a conda environment called bm which will contain all the python, r and js packages used by the repo.
 - This also installs basic versions of R base and NodeJS from the miniconda forge. Run the script as such below when the wd is set to Bootleg_Macro/setup. 

   `.\setup.sh`

It may be necessary to first make the script executable prior to running it:

   `chmod +x setup.sh`

 - If setup script completes successfully then it should be ready to go. Make sure to use "bm" environment when working with the repo. 

## USAGE:
 - There are two main ways of using the tools. Users without Python proficiency can utilize the pre-written scripts controlled via excel file or Qt6 GUI as a control panel.
 - **Example:**
        Use the chartist tool to create a chart showing the YoY % changes in U.S M2, GDP, Unemployment and the S&P 500 Equity Index:
   - Activate the 'bm' environment:
   
   `conda activate bm`
   
   - Set wd to the relevant folder (for windows use \\ instead of / for directory separator in paths):
   
   `cd ....Bootleg_Macro/Macro_Chartist`
   
   - Fill in the relevant cells in the "Control.xlsx" file. This includes the data codes and sources for each data series e.g "M2SL, fred", "GDP, fred", "^GSPC, yfinance" for the 3 data series                 mentioned above, chart title etc... Detailed instructions are found in the file. Select from dropdown menus values in yellow cells and enter necessary values into grey cells. The majority of              cells can be left blank. Save file. 
   - Run "chartist.py":
     
   `python chartist.py`
   
 - Each of the other 2 script tools (NetLiquidity & Pair_Correlation) are controlled by a different excel file control panel in the same way. 
 - Usage information is found within the excel file. Choose values in yellow cells and enter necessary values into grey cells. Then save file.
   
 - You could alternatively run everything in an editor such as VS code, yet if you're not planning to edit any code I'd recommend to stick with the terminal method. 
 - A free excel alternative such as libre office can be used but make sure that the file type is always ".xlsx".

- **More experienced python users can import the MacroBackend module into their Jupyter notebook or python script**. Use:
  ```
    import os
    wd = os.path.dirname(__file__)  ## This gets the working directory which is the folder where you have placed this .py file. 
    parent = os.path.dirname(wd); grampa = os.path.dirname(parent)
    import sys  #We'll append the path to the Botleg_Macro directory to sys.path so that the modules are found to import.
    #Note, this is for a working .ipynb file located in Bootleg_Macro/User_Data/Research_notebooks, modify if in different location, paths are relative to the location your working file. 
    sys.path.append(grampa)
    from MacroBackend import PriceImporter, Utilities, Charting, Pull_Data, chart_rip, Fitting, search_symbol_gui  #or just import MacroBackend.
    from MacroBackend.BEA_Data import bea_data_mate   #For BEA data, bea_data_mate will be a standalone module for BEA data.
  ```
  - You'll want to add the Bootleg_Macro directory to your Python > Analysis > Extra_paths in settings in vscode (if using vscode). This will provide vscode access to the files for popup documentation and syntax coloring. 


### USD NET LIQUIDITY SCRIPT:
The net lqiuidity metric (NLQ) was originally formulated by Darius Dale and 42Macro, much respect DD, 42 Macro is best in class.
The net liquidity time series is the Fed balance sheet (FedBal) - the balance in the reverse repo facility (RevRep) - the treasury general account (TGA). 
This script pulls daily data for the TGA from the treasury along with series from FRED. You can look at NLQ along with 1-5 comparison assets, data sourced from a range of free price history providers, including yahoo finance, google finance and even trading view.

#### A more detailed usage guide can be found here in my twitter threads about the NLQ script: 
https://twitter.com/Tech_Pleb/status/1619542486208372737?s=20&t=lwqXKHnHwTkcF2V1RMnzBg
https://twitter.com/Tech_Pleb/status/1622916354008584192?s=20&t=k0nnXAlNTvv5iiISzwvyAA
     
