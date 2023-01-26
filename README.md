# Plebs_Macro
Open sourcing financial data that is generally hidden behind paywalls. 
USD NET LIQUIDITY SCRIPT - The net lqiuidity metric (NLQ) was originally formulated by Darius Dale and 42Macro, much respect DD, 42 Macro is best in class. If you can afford it, you're best off to
just get a 42 Macro subscription. If however, you are a low-time preferenced, humble, sat-stacking pleb that would rather use that money to stack sats and doesn't mind getting your hands dirty
with coding and data diving, then this approach is for you. The net liquidity time series is the Fed balance sheet (FedBal) - the balance in the reverse repo facility (RevRep) - the treasury general account (TGA). The
three series are available from FRED and this script pulls these series from FRED, does the necessary arithmetic and displays NLQ along with 1-5 comparison assets with data sourced from a range of free price history providers,
inlcuding yahoo finance, google finance and trading view. 
    FedBal is updated on a weekly basis while, revrep and TGA have daily updates of their balance (mon-fri). RevRep series from FRED (RRPONTSYD) is a series with daily frequency while the TGA series
from FRED is a weekly series (average of the week). In order to provide more rapid updating, I'm taking the TGA balance data from the treasury API for the TGA series. The resultant net liquidity series
makes significant moves on a daily basis when TGA and RevRep balances move significantly. NLQ can be viewed on trading view yet only with weekly frequency & this script is possibly a better way
to view NLQ as it updates on a daily basis just like the original 42 macro NLQ series.
    Apart from standard, well vetted, python packages, my script uses another script 'PriceImporter' that contains my functions for pulling price history from different APIs. There is also a package
tvDatafeed which is used. This package is great and allows us to pull data for any asset that you can find on tradingview from tradingview. I'm quite sure that it is safe and have been using it for 
months, it just doesn't achieve legitimancy due to the legal grey area in which it operates.
    How to use scipt: 
     - Place NetLiquidity project folder where you wish. Set working directory to the folder. 
     - Install the necessary modules using requirements.txt.
     - Set your input parameters in the excel file. Correlation will be calculated between NLQ & the asset in slot #1 on excel file.
     - Run script.
A more detailed usage guide can be found here in my twitter thread about NLQ: (link to twitterThread)
     
     
