# Bootleg_Macro
Open sourcing and charting financial data that you may've had to pay for before. We don't like paying stuff, no thanks.

Multiple tools for obtaining and then charting and comparing economic data with asset price data. Has two aggregated liquidity indexes that you won't find elsewhere for free. Tools:
- Generic Charting tool "Macro_Chartist":
    - Chart up to 5 traces on the same chart on up to 5 different axes or a dataframe of many traces on the same axis. 
    - Transform data to first order derivatives, year on year % change, 6 month annualized etc.
    - Smooth data with MA's. Add bars for recessions.
    - Save chart templates to plot later with updated data. One can build up a watchlist this way. 
    - Decent generic charting tool for display of macrioeconomic data. 
- Correlation tool:
    - Look at rolling correlations between any two time series. 
- Central bank global money index "NetLiquiity":
    - Aggregated customizable index that shows the sum of the major central bank balance sheets. Included more elaborate index for the Fed (Net liquidity). Net liquidity metric formulation devised by 42 Macro, see info below. 
    - Compare this index with up to 5 comparison assets. 
- Aggregated global M2 money supply index.
    - This takes M2 money supply data for the top 50 economies and aggregates. Check it out. 

 ## Installation: 
 - Install [git](https://github.com/git-guides/install-git) on your machine if you don't already have it.
 - _Optional yet recommended:_ Create a virtual environment to run this in. I recommend [miniconda](https://docs.conda.io/projects/miniconda/en/latest/). An example of virtual environment creation that may work well with here could be something like:

   `conda create --name financial python=3.9`
 - That will create a conda viirtual environment called _financial_ and will install the latest version of python 3.9 into it. 

   `conda activate financial`
 - This will activate your virtual environment and any packages you install after this will be installed into that environment.  
 - Install [python 3](https://realpython.com/installing-python/) if you don't already have it (skip if already done with conda). This repo has mainly been tested with Python 3.9.6. On-linux you could use:

   `sudo apt-get install python3-tk`
 - Set your working directory where you would like to install the _Bootleg_Macro_ repo:

   `cd <your directory>`
 - Clone this repo to your desired directory:

   `git clone https://github.com/HelloThereMatey/Bootleg_Macro.git`
 - Install the required packages if not already present. Must have directory set to Bootleg_Macro directory:

   `pip install -r requirements.txt`
 - (pip on windows pip3 on mac/ linux or if python 2 is present on system). That will install all the python modules listed in requirements.txt. 
     
## Controlling tools:
 - Each of the tools are controlled by an excel sheet which acts as a control panel (.xlsx file). Open the control file in the folder of the tool you wish to use, e.g _Control.xlsx_ in the 'Macro_Chartist' folder.
 - Usage information is found within the excel file. Choose values in yellow cells and enter necessary values into grey cells. Then save file.
 - Run the python script corresponding to the control file used. e.g after saving 'Control.xlsx' file and with your terminal at ..Bootleg_Macro/Macro_Chartist directory, run the 'chartist.py' script:

   `python chartist.py`
   
 - You could alternatively run everything in an editor such as VS code yet if your're not planning to edit any code I'd recommend to stick with the terminal method. 
 - A free excel alternative such as libre office can be used but make sure that the file type is always ".xlsx". 

### USD NET LIQUIDITY SCRIPT:
The net lqiuidity metric (NLQ) was originally formulated by Darius Dale and 42Macro, much respect DD, 42 Macro is best in class.
The net liquidity time series is the Fed balance sheet (FedBal) - the balance in the reverse repo facility (RevRep) - the treasury general account (TGA). 
This script pulls daily data for the TGA from the treasury along with series from FRED. You can look at NLQ along with 1-5 comparison assets, data sourced from a range of free price history providers, including yahoo finance, google finance and even trading view.

#### A more detailed usage guide can be found here in my twitter threads about the NLQ script: 
https://twitter.com/Tech_Pleb/status/1619542486208372737?s=20&t=lwqXKHnHwTkcF2V1RMnzBg
https://twitter.com/Tech_Pleb/status/1622916354008584192?s=20&t=k0nnXAlNTvv5iiISzwvyAA
- Since V1.1 the script uses the tkinter package. It may be necessary to install this using the command:
sudo apt-get install python3-tk
- That will install tkinter. This fixes a bug where matplotlib does not display the figures. On windows use python inplace of python3. 

     
#### TROUBLESHOOTING:
 - If you get an error message "UserWarning: Matplotlib is currently using agg, which is a non-GUI backend, so cannot show the figure.", you have a
  version of python that does not inculde the tkinter package. 
 - Install latest python with tkinter, e.g sudo apt-get install python3-tk 
     
