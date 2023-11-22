import pandas as pd
import numpy as np
from typing import Union
import os
fdel = os.path.sep
import json

wd = os.path.dirname(__file__)

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec
from fuzzywuzzy import fuzz, process

####### UTILITY FUNCTIONS ##################################################################################################

def closest_column_match(search_str: str, df: pd.DataFrame):
    """
    Find the closest match to the search string among the DataFrame's columns.
    Parameters:
    - search_str (str): The string to search for.
    - df (DataFrame): The DataFrame to search in.

    Returns:
    - str: The closest matching column name.
    """
    # Get the list of column names
    column_names = df.columns.tolist()
    # Use fuzzywuzzy's process to find the closest match
    match = process.extractOne(search_str, column_names, score_cutoff=30) #score_cutoff=70
    if match is None:
        return None
    else:
        closest_match, score = match[0], match [1]
        return closest_match, score 

def CheckIndexDifference(series1:Union[pd.DataFrame, pd.Series], series2:Union[pd.DataFrame, pd.Series]):
    diffs = (series1.index.difference(series2.index), series2.index.difference(series1.index))
    differences = False
    for diff in diffs:
        if len(diff) > 0:
            differences = True
            return differences, diff
        else:
            pass
    return differences 

def PadSeries(Series1: pd.Series, Series2: pd.Series) -> pd.Series: #Pads a series of with Nans to same length so the two can be concatenated. 
    if len(Series1) > len(Series2): 
        LongOne = Series1; shortOne = Series2
    elif len(Series2) > len(Series1): 
        LongOne = Series2; shortOne = Series1
    else:
        print("Series are the same length.")
        return None
    padNum = len(LongOne) - len(shortOne)
    pad = [np.nan for i in range(padNum)]
    padded = pd.Series(shortOne.to_list().extend(pad), name = shortOne.name)
    return padded
    
def GetClosestDateInIndex(df: Union[pd.DataFrame, pd.Series], searchDate: str = "2012-01-01"):
    ## searchDate should bee in "YYYY-MM-DD" format. 
    if type(df.index) != pd.DatetimeIndex:
        print('Input dataframe must have a datetime index.')
        return

    # Convert the Datestring to a Timestamp object
    date_ts = pd.Timestamp(searchDate)
    # Find the closest date in the index
    closest_date = min(df.index, key=lambda x: abs(x - date_ts))
    index = df.index.get_loc(closest_date)
    return closest_date, index

def find_index_ofNearestVal(series:pd.Series, value: Union[int, float]):
    return (series - value).abs().idxmin()

def ManShift(input: Union[pd.DataFrame, pd.Series], numPeriods: int = 1):  #pandas shift not working for me. 
    shifted = {}

    if type(input) == pd.DataFrame:
        for col in input.columns:
            cat = input[col].copy()
            fur = cat.to_list()
            for l in range(numPeriods):
                fur.insert(0, np.nan)
                fur.pop(len(fur)-1)
            ser = pd.Series(fur, index = input.index)
            shifted[col] = ser
        output = pd.DataFrame(shifted, index = input.index)  
    elif type(input) == pd.Series:
        cat = input.copy().to_list()
        for l in range(numPeriods):
                cat.insert(0, np.nan)
                cat.pop(len(cat)-1)   
        output = pd.Series(cat, index = input.index)      
    return output 

def GetFirstNonNanZero(df_col: pd.Series):    
    for i in range(len(df_col)):
        if pd.isna(df_col.iloc[i]) or df_col.iloc[i] == 0:
            continue
        else:
            baseVal = df_col.iloc[i]
            return baseVal, i
    return np.nan   

def excel_to_json_hierarchy(XL_filepath: str, XLsheet_name: str):
    """Convert Excel file with hierarchical data into a nested JSON structure."""
    # Load the excel file into a DataFrame
    df = pd.read_excel(XL_filepath, sheet_name = XLsheet_name)

    # Initialize an empty dictionary for the results
    result = {}

    def recursive_dict_insert(data, levels):
        """Recursive function to insert levels into dictionary."""
        if len(levels) == 1:
            return [levels[0]]  # Return list containing the single item
        else:
            key = levels[0]
            if key not in data:
                if len(levels) > 2:
                    data[key] = {}
                else:
                    data[key] = []
            # When there are only 2 levels left and the next key is already a list, append to that list
            if len(levels) == 2 and isinstance(data[key], list):
                data[key].append(levels[1])
            else:
                data[key] = recursive_dict_insert(data[key], levels[1:])
            return data

    result = {}
    for _, row in df.iterrows():
        levels = row.dropna().tolist()
        result = recursive_dict_insert(result, levels)

    # Convert the dictionary to JSON
    json_output = json.dumps(result, indent=4)
    proper_json = json.loads(json_output)
    return proper_json

def save_to_json_file(data, filename="output.json"):
    """Save a dictionary to a JSON file."""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

def search_key(json_dict: dict, target_key):
        for key, value in json_dict.items():
            if key == target_key:
                return {key: value}
            elif isinstance(value, dict):
                result = search_key(value, target_key)
                if result is not None:
                    return result
        return None        

######## CLASSES BELOW ############################            
class CategoryData:
    def __init__(self, CategoryJSON_File_Path: str = None, CategoryDict: dict = None):
        if CategoryJSON_File_Path is not None:
            with open(CategoryJSON_File_Path) as Categories_json:
                self.Category_data = json.load(Categories_json)
        elif CategoryDict is not None:
            self.Category_data = CategoryDict
        else:
            print("Please provide either a JSON file path or a dictionary of categories.")
            exit()

        self.Category_data_name = list(self.Category_data.keys())[0]
        self.levels = self.find_category_levels()

        for level, value in self.levels.items():
            val = int(level[len(level)-1])
            setattr(self, f"Aggregate_level_{val}", value)
            #self.aggregate_level[int(level)+1] = value

    def find_category_levels(self):
        levels = {}

        def max_depth(d, level=0):
            if isinstance(d, dict):
                return max(max_depth(v, level + 1) for v in d.values())
            elif isinstance(d, list):
                return max(max_depth(item, level + 1) for item in d)
            else:
                return level - 1 

        depth = max_depth(self.Category_data)
        print("Depth of input dict:", self.Category_data_name, depth)

        def inner(CatSubDict: dict, current_level: int):
            temp_list = []
            LevelName = "Aggregate_level_"+str(current_level)
            if LevelName not in levels:
                levels[LevelName] = []

            for key, value in CatSubDict.items():
                if isinstance(value, dict):
                    sub_list = inner(value, current_level - 1)
                    temp_list.append({key: sub_list})
                else:
                    temp_list.extend(value)

            levels[LevelName].extend(temp_list)
            return temp_list

        inner(self.Category_data, depth)
        return levels
    
########################################## FISHER INDEX CALCULATION ##################################################################################################
class BEA_FisherIndex(object):

    def __init__(self, PCE_loadPath: str, PricesloadPath: str, CategoryDataFile: str, StartDate: str = None, 
                  BaseDate: str = "2017-08-31", base_value:float = 100, IndexName: str = "Personal consumption expenditures",
                  nearestAggregate = "Personal consumption expenditures", studyTitle: str = 'PCE data study',excludeList: list = None):   #All of the parameters are strings containing paths to load data from. 

        self.title = studyTitle
        self.PCE_Data = pd.read_excel(PCE_loadPath, sheet_name="Series_Split", index_col=0)
        self.TableData = pd.read_excel(PCE_loadPath, sheet_name = 'Notes',index_col=0)
        self.TableName = str(self.TableData.iloc[0].iat[1]).split('[')[0]
        self.Prices_Indexes = pd.read_excel(PricesloadPath, sheet_name="Series_Split", index_col=0) 
        NearestAgg, score = closest_column_match(nearestAggregate, self.Prices_Indexes)
        if score < 85:
            print('Warning: The nearest aggregate match value is less than 85, column found: ',NearestAgg, "Go with that column as your aggregate target?")
            if input("y/n?") == "y":
                pass
            else:
                exit()
        self.IndexName = IndexName

        self.FI_BaseDate = BaseDate
        self.ReBaseDate = None
        self.base_value = base_value
        self.Quantities_Indexes = None
        self.off_weightings = None
        self.ref_priceIndex = None
        self.refIndex_pct = None
        self.startDate = StartDate

        self.nearest_agg = NearestAgg

        ### Construct category lists and dicts from json 
        self.Category_data = CategoryData(CategoryJSON_File_Path=CategoryDataFile)
        self.CatSubList = search_key(self.Category_data.Category_data, self.nearest_agg)
        self.ReducedCatz = CategoryData(CategoryDict=self.CatSubList)

        self.BaseCatz = self.ReducedCatz.Aggregate_level_1

        if self.startDate is not None:
            self.ShortenData(self.startDate)

        if excludeList is not None:
            exclude = [closest_column_match(category, self.PCE_Data)[0] for category in excludeList]
            FullLength = len(self.BaseCatz)
            print('Categories before exclusion: ', self.BaseCatz)
            self.Final_Catz = [cat for cat in self.BaseCatz if cat not in exclude]
            print('Full number of PCE base categories: ', FullLength, ", excluding categories: ", exclude, ', final number of categories', len(self.Final_Catz))  
        else:
            self.Final_Catz = self.BaseCatz

        self.Quantities, self.Prices = self.PriceQuantSep()

    def Calculate_FI(self, method: str = "1b"): 
        if self.ref_priceIndex is None:
            print('Warning: The base date for the Fisher index has not been derived from a reference price index, using deafult base date: ', self.FI_BaseDate)   
            print("You're better off to load reference price index data first with BEA_FisherIndex.LoadRefData(), to get the target baseDate.")
        if method == "1b":
            self.Fisher_Index_1b = self.Fisher_Index(self.Prices, self.Quantities, categoryList = self.Final_Catz, method = method)
            self.FI_1b_chain = self.ChainFisherIndex(self.Fisher_Index_1b, self.FI_BaseDate, self.base_value)
            self.FI_1b_pct = 100*(self.Fisher_Index_1b-1).rename('FI_1b_PctChange').fillna(0)  #Convert Fisher Prcie index to % change from previous period. 
            if self.ref_priceIndex is not None:
                self.residual_1b, self.resPct_1b, self.fudged_1b = self.FudgeIt(self.FI_1b_chain, self.ref_priceIndex)
            print("Fisher index calculated from price & quantity data derived from PCE current dollar data & price index data (method '1b').")
        elif method == "1a": 
            if self.Quantities_Indexes is not None:
                self.Fisher_Index_1a = self.Fisher_Index(self.Prices_Indexes, self.Quantities_Indexes, categoryList = self.Final_Catz, method = method)
                self.FI_1a_chain = self.ChainFisherIndex(self.Fisher_Index_1a, self.FI_BaseDate, self.base_value)
                self.FI_1a_pct = 100*(self.Fisher_Index_1a-1).rename('FI_1a_PctChange').fillna(0)  #Convert Fisher Prcie index to % change from previous period.   
                if self.ref_priceIndex is not None:
                    self.residual_1a, self.resPct_1a, self.fudged_1a = self.FudgeIt(self.FI_1a_chain, self.ref_priceIndex)
                print("Fisher index calculated from price index & quantity index data (method '1a').")
            else:    
                print("Load quantity index data first in order to calculate a Fisher index using method '1a'.")
                return 
        else:
            print("Method should be set to either '1b' or '1a'.")    

    def loadQuantityIndexes(self, QuantitiesloadPath: str):    
        self.Quantities_Indexes = pd.read_excel(QuantitiesloadPath, sheet_name="Series_Split", index_col=0)

    def loadOffWeightings(self, OffWeightingsPath: str):    
        self.off_weightings = pd.read_excel(OffWeightingsPath, sheet_name="Series_Split", index_col=0)    

    def LoadRefData(self, refIndexName: str = None, pctPricesPath: str = None, AltPriceIndexesPath: str = None, PriceIndexes: pd.DataFrame = None, pctPrices: pd.DataFrame = None):    
        if PriceIndexes is not None and pctPrices is not None:
            name, score = closest_column_match(refIndexName, PriceIndexes)
            if score > 90:
                self.ref_priceIndex = PriceIndexes[name]
                self.refIndex_pct = pctPrices[name]
            return    

        if refIndexName is None:
            refIndexName = self.nearest_agg
        if AltPriceIndexesPath is not None:
            self.Prices_Indexes2  = pd.read_excel(AltPriceIndexesPath, sheet_name="Series_Split", index_col=0)
            name, score = closest_column_match(refIndexName, self.Prices_Indexes2)
            if score > 90:
                self.ref_priceIndex = self.Prices_Indexes2[name]
        else:    
            name, score = closest_column_match(refIndexName, self.Prices_Indexes)
            if score > 90:
                self.ref_priceIndex = self.Prices_Indexes[name]
            else:
                print("Reference price index name not found in prices index data. Check refIndexName.")
                return
        if pctPricesPath is not None:
            self.PctPrices = pd.read_excel(pctPricesPath, sheet_name="Series_Split", index_col=0)
            name, score = closest_column_match(refIndexName, self.PctPrices)
            if score > 90:
                self.refIndex_pct = self.PctPrices[name]
            else:
                print("Reference price index name not found in prices pc change data. Check refIndexName.")
                return
        else:
            self.refIndex_pct = self.ref_priceIndex.pct_change()*100
        
        BaseDate = pd.Timestamp(find_index_ofNearestVal(self.ref_priceIndex, 100))
        BD_str = BaseDate.strftime("%Y-%m-%d")
        self.FI_BaseDate = BD_str   

    def RebaseIndexes(self, newBaseDate: str = "2012-06-30", method: int = 1):
        self.ReBaseDate = newBaseDate
    
        self.PCE_Data = self.RebaseIndexFrame(self.PCE_Data, self.ReBaseDate, method = method)
        self.Prices_Indexes = self.RebaseIndexFrame(self.Prices_Indexes, self.ReBaseDate, method = method)
        
        if self.Quantities_Indexes is not None: 
            self.Quantities_Indexes = self.RebaseIndexFrame(self.Quantities_Indexes, self.ReBaseDate, method = method)    
     
        # ######################### SLICE DATAFRAMES IF YOU WANT TO SHORTEN THE TIMESPAN ########################################################################################
    def ShortenData(self, startDate):
        self.PCE_Data = self.PCE_Data.iloc[GetClosestDateInIndex(self.PCE_Data,startDate)[1]::]
        self.Prices_Indexes = self.Prices_Indexes.iloc[GetClosestDateInIndex(self.Prices_Indexes,startDate)[1]::]
        
        if self.off_weightings is not None:
            self.off_weightings = self.off_weightings.iloc[GetClosestDateInIndex(self.off_weightings,startDate)[1]::]       
        if self.Quantities_Indexes is not None:
            self.Quantities_Indexes = self.Quantities_Indexes.iloc[GetClosestDateInIndex(self.Quantities_Indexes,startDate)[1]::]      

    def Calc_FI_AltMethods(self, method: int = 3):    
        
        if method == 2:
            if self.off_weightings is None:
                print('Load table of percentage contributions to PCE change first.')
                return
            else:
                if self.ref_priceIndex is None:
                    print('Load reference price index data first.')
                ManIndexData = self.ManAddIndex(self.off_weightings, self.Final_Catz, self.ref_priceIndex.name, self.IndexName+"_Meth2")
                self.ManIndex_meth2 = ManIndexData[1]

        elif method == 3:
            if self.Quantities_Indexes is None:
                print('Load quantity index data first.')
                return
            meth3_Index = self.CustomFisherIndex(self.PCE_Data, self.Quantities_Indexes, self.Final_Catz, self.ref_priceIndex.name, self.IndexName+"_Meth3")[0]
            self.ManIndex_meth3 = self.ChainFisherIndex(meth3_Index, BaseDate = self.FI_BaseDate)
   
    def Fisher_Index(self, Prices: pd.DataFrame, Quantities: pd.DataFrame, categoryList: list, SeriesName: str = 'Fisher price index', method: str = "1a") -> pd.Series:
        """
        Calculate the Fisher Price Index from price (p) and quantity (q) index data or from the raw pq data (PCE_raw - PCE measured in current dollars).
        
        Parameters:
        - Price and quantity DF's: Dataframes containing the price & quantity time-series for the different categories of goods/services. 
        - Categories: list of strings containing the names of the series to pull from both dataframes. Both dataframes need to have the same column names. 
        - SeriesName: Name to give to the output series. 
        
        Returns:
        - fisher_index: Fisher Index as a Pandas Series.
        """  
        Prices.fillna(method="backfill", inplace=True)
        Prices.fillna(method='ffill', inplace=True)
        Quantities.fillna(method="backfill", inplace=True)
        Quantities.fillna(method='ffill', inplace=True)
        shifted_P = ManShift(Prices)
        shifted_Q = ManShift(Quantities)

        i = 0
        for category in categoryList:
            p_t = Prices[category].copy()
            p_t_1 = shifted_P[category].fillna(method='backfill')
            q_t = Quantities[category].copy()
            q_t_1 = shifted_Q[category].fillna(method='backfill')  # Shift to get quantities at t-1
        
            if i == 0:
                print("First category.")
                laspeyres_numerator = (p_t * q_t_1)
                laspeyres_denominator = (p_t_1 * q_t_1)  
                paasche_numerator = (p_t * q_t)
                paasche_denominator = (p_t_1 * q_t)
            else:
                laspeyres_numerator += (p_t * q_t_1)
                laspeyres_denominator += (p_t_1 * q_t_1) 
                paasche_numerator += (p_t * q_t)
                paasche_denominator += (p_t_1 * q_t)
            i += 1
            
        laspeyres_index = laspeyres_numerator / laspeyres_denominator
        paasche_index = paasche_numerator / paasche_denominator
        
        # Calculate Fisher Index as geometric mean of Laspeyres and Paasche indexes
        index = pd.Series(np.sqrt(laspeyres_index * paasche_index))
        fisher_index = pd.Series(index, name = SeriesName).fillna(1)
        fisher_index.rename(SeriesName+"_manual_FI_"+method, inplace=True)
        
        return fisher_index
    
    def PriceQuantSep(self) -> pd.DataFrame:
        print(self.Final_Catz)
        for cat in self.Final_Catz:
            if cat not in self.PCE_Data.columns:
                print('This cat not in PCE_Data.columns: ', cat)
                nearest, score = closest_column_match(cat, self.PCE_Data)
                print('Nearest column in data: ', nearest, score)
                if score > 94:
                    self.PCE_Data.rename({nearest:cat}, axis = 1, inplace = True)
                else:
                    print("Rename: ", nearest, "to ", cat, "? (y), or drop column (n).")
                    if input("y/n? ") == "y":
                        self.PCE_Data.rename({nearest:cat}, axis = 1, inplace = True)
                    else:    
                        self.PCE_Data.drop(nearest, axis = 1, inplace = True)
                print(cat in self.PCE_Data.columns)        
            
            if cat not in self.Prices_Indexes.columns:
                print('This cat not in Prices_Indexes.columns: ', cat)
                nearest, score = closest_column_match(cat, self.Prices_Indexes)
                print('Nearest column in data: ', nearest, score)
                if score > 94:
                    self.Prices_Indexes.rename({nearest:cat}, axis = 1, inplace = True)
                    print(cat in self.Prices_Indexes.columns)
                else:
                    print("Rename: ", nearest, "to ", cat, "? (y), or drop column (n).")
                    if input("y/n? ") == "y":
                        self.Prices_Indexes.rename({nearest:cat}, axis = 1, inplace = True)
                    else:    
                        self.Prices_Indexes.drop(nearest, axis = 1, inplace = True)
                print(cat in self.PCE_Data.columns)         
        
        diff1 = list(self.PCE_Data.columns.difference(self.Prices_Indexes.columns))
        diff2 = list(self.Prices_Indexes.columns.difference(self.PCE_Data.columns))
        print(diff1, diff2)
        
        if len(diff1) > len(diff2):
            for cat in diff1:
                self.PCE_Data.drop(cat, axis = 1, inplace = True)   
        elif len(diff2) > len(diff1):
            for cat in diff2:
                self.Prices_Indexes.drop(cat, axis = 1, inplace = True)                 
        
        diff1 = list(self.PCE_Data.columns.difference(self.Prices_Indexes.columns))
        diff2 = list(self.Prices_Indexes.columns.difference(self.PCE_Data.columns))
        print(diff1, diff2)
        categories = list(self.PCE_Data.columns)

        quantities = self.PCE_Data.copy()
        prices = self.PCE_Data.copy()
        
        for category in categories:
            quantities[category] /= self.Prices_Indexes[category]
            prices[category] /= quantities[category]    

        return quantities, prices      
        
    def ChainFisherIndex(self, Fisher_Index: pd.Series, BaseDate: str = "2012-11-30", base_value:float = 100 )-> pd.Series:
        """
        Chain Fisher Index values from a middle base period.

        Parameters:
        - fisher_series: Pandas Series containing Fisher Index values.
        - base_date: The base date for the index.
        - base_value: Value to set for the base period.
        
        Returns:
        - chained_index: Chained Fisher Index as a Pandas Series.
        """
        # Initialize the chained index series
        chained_index = pd.Series(index=Fisher_Index.index, name = Fisher_Index.name).fillna(method='backfill')
        chained_index.fillna(method='ffill', inplace=True)
        BasingDate = GetClosestDateInIndex(Fisher_Index, BaseDate)
        #print('Chaining ',Fisher_Index.name, BasingDate)
        # Set the base value
        chained_index[BasingDate[0]] = base_value
        

        # Forward chaining
        for t in range(BasingDate[1] + 1, len(Fisher_Index)):
            chained_index.iloc[t] = chained_index.iloc[t-1]*Fisher_Index.iloc[t]
          
        if BasingDate[1] > 1:
            # Backward chaining
            for t in range(BasingDate[1] - 1, -1, -1):
                chained_index.iloc[t] = chained_index.iloc[t+1]/Fisher_Index.iloc[t+1]      
        chained_index.rename(self.IndexName+" chainFI") 
        return chained_index.round(decimals=3)

    def RebaseIndexFrame(self, Index_df: pd.DataFrame, NewBaseDate: str = "1970-01-01", method: int = 1, filepath: str = None) -> pd.DataFrame:

        og_copy = Index_df.copy()
        Index_df.replace(0, np.nan, inplace=True)
        for col in Index_df.columns:
            firstNonZero = GetFirstNonNanZero(Index_df[col])
            Index_df[col][0:firstNonZero[1]] = firstNonZero[0] 
        Index_df.fillna(method='ffill', inplace=True) 
        output = pd.Series(index=Index_df.index)
        unchained = None
    
        baseDate, baseindex = GetClosestDateInIndex(output, NewBaseDate)
        print('Rebasing DF to date: ', baseDate, ', using rebase method: ', method)

        if method == 1:
            for col in Index_df.columns:   
                baseVal = Index_df.loc[baseDate].at[col].copy()
                newIndex = Index_df[col].copy()/baseVal
                output = pd.concat([output, newIndex], axis = 1)
        elif method == 2:
            unchained = pd.DataFrame((Index_df.copy().pct_change() + 1)).fillna(1)
            for col in unchained.columns: 
                baseVal = Index_df.loc[baseDate].at[col].copy()
                newIndex = self.ChainFisherIndex(unchained[col], BaseDate= NewBaseDate, base_value=baseVal)
                output = pd.concat([output, newIndex], axis = 1)   
        else:
            return 0   
        output.drop(output.columns[0],axis=1, inplace=True)  

        if filepath is not None: 
            if os.path.isfile(filepath) is False:
                og_copy.to_excel(filepath, sheet_name='originalDF_'+str(self.savecount)) 
            with pd.ExcelWriter(filepath, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:  
                og_copy.to_excel(writer, sheet_name='originalDF_'+str(self.savecount)) 
                Index_df.to_excel(writer, sheet_name='Index_df_'+str(self.savecount)) 
                if unchained is not None:
                    unchained.to_excel(writer, sheet_name='Unchained_'+str(self.savecount)) 
                output.to_excel(writer, sheet_name='Rebased_df_'+str(self.savecount))   
            self.savecount += 1   
        return output

    def CustomFisherIndex(self, PCE_Raw: pd.DataFrame, Quantities_Indexes: pd.DataFrame, categories: list, Aggregate_Target: str = "Personal consumption expenditures",
                        SeriesName: str = 'Fisher price index - custom method: ') -> pd.Series:
        """This function makes a fisher index from the current dollar PCE data (pq), what I'm calling PCE_Raw, and the quantities index. Based upon 
        re-arrangement of the current dollar change in ratio form of Raw_PCE = PQ (price x quantitiy indexes) on page 93 of the NIPA handbook. 
        This is fisher index calculation method #3. 
        """
        Aggregate = closest_column_match(Aggregate_Target, Quantities_Indexes)
        shifted_PCE = ManShift(PCE_Raw)
        Aggregate_Q = pd.Series(Quantities_Indexes[Aggregate[0]]).pct_change().fillna(0) + 1
        
        i = 0
        for category in categories:
            pce_t = PCE_Raw[category].copy()
            pce_t_1 = shifted_PCE[category]

        if i == 0:
            print("First category.") 
            sum_t = pce_t
            denom = pce_t_1
        else:
            sum_t = round(sum_t + pce_t) 
            denom = round(denom + pce_t_1)    
        denom *= Aggregate_Q
        fisher_c = pd.Series(sum_t/denom, name=SeriesName, index=PCE_Raw.index).fillna(1)
        Results = pd.concat([Quantities_Indexes[Aggregate[0]],Aggregate_Q,PCE_Raw[Aggregate[0]],shifted_PCE[Aggregate[0]],fisher_c], axis = 1)
        return fisher_c, Results  

    def ManAddIndex(PriceIndexes: pd.DataFrame, PctWeightings: pd.DataFrame, categories: list = ["Goods", "Services"], 
            target: str = "Personal consumption expenditures (PCE)", IndexName: str = "Man calc PCE") -> pd.Series:
        
        """ This approxiates a Fisher price index using the reported percentage contribution of each category to the total % change in PCE prices & 
        the price indexes from BEA. This is calculation method #2b. #2a was dropped as the results looked to be straight up wrong."""

        Sum_Contributions = pd.Series(0, index = PriceIndexes.index, name = "% change, summed contributions of categories")
        Manual_Index = pd.Series(0, index = PriceIndexes.index, name = IndexName)
        PCE_del_Pct = closest_column_match("Personal consumption expenditures (PCE)", PctWeightings)
        WeightDF = pd.Series(PctWeightings[PCE_del_Pct[0]], name = PCE_del_Pct[0])
        Target_Series = closest_column_match(target, PriceIndexes)
        Target_Weight = closest_column_match(target, PctWeightings)
        BasingDate = GetClosestDateInIndex(PriceIndexes[Target_Series[0]], "2012-12-31")
        # Set the base value
        BaseVal = PriceIndexes[Target_Series[0]][BasingDate[0]]
        print("Using base value of: ",BaseVal, 'from series ', Target_Series[0], 'at date: ', BasingDate[0], 'index: ',BasingDate[1])
        Manual_Index[BasingDate[0]] = BaseVal
        print(Manual_Index[BasingDate[0]], BasingDate[0])
        
        for category in categories:
            cati = closest_column_match(category,PctWeightings)
            cat_contribution = pd.Series(PctWeightings[cati[0]], name = cati[0])
            WeightDF = pd.concat([WeightDF,PctWeightings[cati[0]]],axis=1)
            Sum_Contributions += cat_contribution    
        Sum_Contributions = Sum_Contributions.round(decimals=1)    

        # Forward chaining
        for t in range(BasingDate[1] + 1, len(Sum_Contributions), 1):
            Manual_Index.iloc[t] = round((Manual_Index.iloc[t-1] + Manual_Index.iloc[t-1]*(Sum_Contributions.iloc[t]/100)), 3)
            
        # Backward chaining
        for t in range(BasingDate[1] - 1, -1, -1):
            Manual_Index.iloc[t] = round(Manual_Index.iloc[t+1]*(1-(Sum_Contributions.iloc[t+1]/100)), 3) 

        TheResults = pd.concat([PctWeightings[Target_Weight[0]], Sum_Contributions, PriceIndexes[Target_Series[0]], Manual_Index], axis = 1)
        return Sum_Contributions, Manual_Index, TheResults, WeightDF

    def FudgeIt(self, manual_index: pd.Series, Official_Index: pd.Series) -> pd.Series:
        residual = pd.Series(manual_index - Official_Index, name = "Residual")
        fudged = pd.Series(manual_index - residual, name = manual_index.name + " residual corrected")
        residual_pct = ((manual_index/Official_Index)*100-100).rename("Residual dev. pct")
        return residual, residual_pct, fudged
    
    def PlotIndexSet(self, title:str = None, method: str = "1b", manual_metricName: str = None, official_metricName: str = None):
        if title is None:
            title = self.title
        title = title + " (calc. meth. " + method+")"
        
        if self.ref_priceIndex is None or self.refIndex_pct is None:
                print('Load reference index data first with BEA_FisherIndex.LoadRefData(), before plotting the manual index set.')
                return
        
        if manual_metricName is None:
            manual_metricName = self.IndexName+" (manual)"
        if official_metricName is None:    
            official_metricName = self.IndexName+' (official)'
    
        if method == "1b":
            Fig = plt.figure(FigureClass = PCE_Fig, title = self.title,  residual = self.resPct_1b)
            Fig.PlotData(self.FI_1b_chain, self.ref_priceIndex, self.FI_1b_pct, self.refIndex_pct, 
                            manual_metricName = manual_metricName, official_metricName = official_metricName)
            
        elif method == "1a":
            Fig = plt.figure(FigureClass = PCE_Fig, title = self.title,  residual = self.resPct_1a)
            Fig.PlotData(self.FI_1a_chain, self.ref_priceIndex, self.FI_1a_pct, self.refIndex_pct, 
                            manual_metricName = manual_metricName, official_metricName = official_metricName, residual = self.resPct_1a)    
        
        elif method == '2':
            Fig = plt.figure(FigureClass = PCE_Fig, title = self.title)
            # Not done yet. Need to test calc. method 2 using the annual or maybe quarterly data. 
        
        elif method == '3':
            Fig = plt.figure(FigureClass = PCE_Fig, title = self.title)
            manIPct = self.ManIndex_meth3.pct_change()*100
            Fig.PlotData(self.ManIndex_meth3, self.ref_priceIndex, manIPct, self.refIndex_pct, 
                            manual_metricName = self.ManIndex_meth3.name, official_metricName = official_metricName)
            
    def export_index_data(self, saveFolder: str):
        self.Export = pd.concat([self.ref_priceIndex,self.refIndex_pct,self.FI_1b_chain,self.FI_1b_pct,self.residual_1b,self.fudged_1b,
                            self.fudged_1b.pct_change()*100], axis = 1)
        saveName = saveFolder+fdel+self.IndexName+".xlsx"
        SeriesInfo= {'Table name': self.TableName, 'units':"index (a.u)", 'units_short': "Fisher price index", 
                     'title': self.title, 'id': self.IndexName, 'Source': "U.S B.E.A"}  
        self.SeriesInfo = pd.Series(SeriesInfo, name="Value")
        self.FI_1b_chain.rename(self.IndexName)

        Categories = pd.Series(self.Final_Catz, name = "PCE categories used for index construction")
        Categories.to_excel(saveName, sheet_name='Index_Component_List') 
        with pd.ExcelWriter(saveName, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:  
            self.Export.to_excel(writer, sheet_name='CustomIndexes')    
            self.SeriesInfo.to_excel(writer, sheet_name='SeriesInfo')     ##These two are for compatibility with my Generic series plotting tool. 
            self.FI_1b_chain.to_excel(writer, sheet_name='Closing_Price')

class PCE_Fig(Figure):

    def __init__(self, metricName:str = "PCE", residual: pd.Series = None, title: str = "Bureau of Economic Analysis data"
                , **kwargs):
        plt.rcParams['font.family'] = 'serif'; plt.rcParams['figure.dpi'] = 175
        
        self.metricName = metricName
        self.residual = residual
        self.Chart_Title = title

        if self.residual is not None:
            gs = GridSpec(3, 1, top = 0.95, bottom=0.06,left=0.06,right=0.94, height_ratios=[4,6,1],hspace=0.02)
            kwargs['figsize']=(9, 5.5)
        else:    
            gs = GridSpec(2, 1, top = 0.94, bottom=0.06,left=0.06,right=0.94, height_ratios=[4,6], hspace=0.02)
            kwargs['figsize']=(9, 4)
        super().__init__(**kwargs)

        self.ax = self.add_subplot(gs[0]); 
        self.ax2 = self.add_subplot(gs[1], sharex = self.ax)
        if self.residual is not None:
            self.ax3 = self.add_subplot(gs[2], sharex = self.ax)
            self.ax3.minorticks_on()
            self.ax3.tick_params(axis = 'y', which = 'major', labelsize = 5)

        self.ax.set_title(self.Chart_Title, fontsize = 10)
        self.ax.tick_params(axis='y',labelsize=6, length = 3)
        self.ax.tick_params(axis='x',labelsize=0, length = 0, width = 0)
        self.ax2.tick_params(axis='y',labelsize=6, length = 3)
        self.ax2.tick_params(axis='x',labelsize=8)

        self.ax.margins(0.01, 0.02); self.ax2.margins(0.01, 0.02)
        self.ax.minorticks_on(); self.ax2.minorticks_on()
        self.ax.grid(visible=True,axis= 'x',which='both',lw=0.35,color='gray',ls=":")
        self.ax2.grid(visible=True,axis= 'x',which='both',lw=0.35,color='gray',ls=":")
        self.ax.grid(visible=True,axis= 'y',which='major',lw=0.35,color='gray',ls=":")
        self.ax2.grid(visible=True,axis= 'y',which='major',lw=0.35,color='gray',ls=":")
       
    def PlotData(self, Man_PCE_chained: pd.Series, Act_PCE_chained: pd.Series = None, Man_pct_change: pd.Series = None, Act_pct_change: pd.Series = None, 
                 manual_metricName: str = None, official_metricName: str = None):

        self.manualIndex = Man_PCE_chained
        self.ref_index = Act_PCE_chained

        if Man_pct_change is not None: 
            self.manI_pct = Man_pct_change
        else:
            self.manI_pct = self.manualIndex.copy().pct_change()*100

        freq = pd.infer_freq(self.manualIndex.index)
        freqs = {'D': "daily",'M': "monthly", 'Q': "quarter", 'A': "annual"}
    
        fStr = freq[0]
        if fStr in freqs.keys():
            Frequency = freqs[fStr]

        metricName1 = 'Manually calculated '+self.metricName; metricName2 = 'Official '+self.metricName
        if manual_metricName is not None:
            metricName1 = manual_metricName
        if official_metricName is not None:
            metricName2 = official_metricName 

        bar_width = round(30000 / len(self.manI_pct))
    
        self.ax.bar(self.manI_pct.index, self.manI_pct, width=bar_width, color='black', label = metricName1)
        if Act_pct_change is not None:
            self.refI_pct = Act_pct_change
            self.ax.bar(self.refI_pct.index, self.refI_pct, width=(round(bar_width/2)), color='orangered', label = metricName2)
        self.ax2.plot(self.manualIndex,color='black', label = metricName1)
        if Act_PCE_chained is not None:
            self.ax2.plot(self.ref_index, color = 'orangered', label = metricName2)

        self.ax2.set_ylabel('Fisher price index', fontsize = 7, fontweight = 'bold')
        self.ax.set_ylabel(r'PoP $\Delta$%', fontsize = 7, fontweight = 'bold')
        self.ax.text(0.01,0.9, "Data frequency: "+Frequency, transform = self.ax.transAxes, horizontalalignment = 'left', fontsize = 7, fontweight = 'bold')
       
        self.ax.set_axisbelow(True); self.ax2.set_axisbelow(True)
        self.ax.legend(loc=1,fontsize=6); self.ax2.legend(loc=4,fontsize=6)
    
        if self.residual is not None:
            self.ax3.plot(self.residual , color='red', label = self.residual.name, lw = 1)
            self.ax3.set_ylabel('Residual (% dev.)', fontsize = 6, fontweight = 'bold')
            self.ax3.grid(visible=True,axis= 'x',which='both',lw=0.35,color='gray',ls=":")
            self.ax3.grid(visible=True,axis= 'y',which='major',lw=0.35,color='gray',ls=":")
            self.ax2.tick_params(axis='x',labelsize=0, length = 0, width = 0)
            self.ax3.tick_params(axis='y',labelsize=6, length = 3)
            self.ax3.legend(loc=1, fontsize=6)
            self.ax3.tick_params(axis='x',labelsize=8)       

class index_comparison(object):

    def __init__(self, customIndex_data: pd.DataFrame = None, ReproducedIndex_data: pd.DataFrame = None, customIndex_loadpath: str = None,
                 ReproducedIndex_loadpath: str = None, customIndexName: str = "Fisher index 1", ReproducedIndexName: str = "Fisher index 2"):
        if customIndex_data is not None: 
            customIndex_df = customIndex_data
        elif customIndex_loadpath is not None:
            customIndex_df = pd.read_excel(customIndex_loadpath, sheet_name="CustomIndexes", index_col=0)
        else:
            print('Please provide customIndex data as a datafrae or path to an excel file containing the data to load from.')
            return None    
        
        if ReproducedIndex_data is not None: 
            ReproducedIndex_df = ReproducedIndex_data
        elif ReproducedIndex_loadpath is not None:
            ReproducedIndex_df = pd.read_excel(ReproducedIndex_loadpath, sheet_name="CustomIndexes", index_col=0)
        else:
            print('Please provide ReproducedIndex data as a dataframe or path to an excel file containing the data to load from.')
            return None  
        
        self.customIndex = customIndex_df['Fisher price index_manual_FI_1b'].rename(customIndexName)
        self.ReproducedIndex = ReproducedIndex_df['Fisher price index_manual_FI_1b'].rename(ReproducedIndexName)
        self.customIndex_pct = customIndex_df['FI_1b_PctChange'].rename(customIndexName+'_pct')
        self.ReproducedIndex_pct = ReproducedIndex_df['FI_1b_PctChange'].rename(ReproducedIndexName+'_pct')
       
        self.customIndex_res = customIndex_df['Residual']
        self.ReproducedIndex_res = ReproducedIndex_df['Residual']
        self.customIndex_resCorr = self.customIndex*((self.ReproducedIndex_res+100)/100)
        self.ReproducedIndex_resCorr = ReproducedIndex_df['Fisher price index_manual_FI_1b residual corrected']
        self.customIndex_resCorr_pct = self.customIndex_resCorr.pct_change()*100
        self.ReproducedIndex_resCorr_pct = self.ReproducedIndex_resCorr.pct_change()*100

    def plot_comparison(self, title: str = 'Manually calulated Fisher indexes...', show_res_corr: bool = False):

        comp_uncorr = plt.figure(FigureClass = PCE_Fig, title = title)
        comp_uncorr.PlotData(self.customIndex, self.ReproducedIndex, self.customIndex_pct, self.ReproducedIndex_pct, 
                             manual_metricName = self.customIndex.name, official_metricName = self.ReproducedIndex.name)
        
        if show_res_corr:
            comp_corr = plt.figure(FigureClass = PCE_Fig, title = title+" residual corrected")
            comp_corr.PlotData(self.customIndex_resCorr, self.ReproducedIndex_resCorr, self.customIndex_resCorr_pct, self.ReproducedIndex_resCorr_pct, 
                                manual_metricName = self.customIndex.name + ' (res. corr)', official_metricName = self.ReproducedIndex.name + ' (res. corr)')

    
if __name__ == "__main__":
       ######### OPTIONAL TABLE CONTAINING CATEGORY NAMES ###############
    
    ##### IMPORTANT GLOBAL PARAMETERS ################################################################
    excludeList = ["Rental of tenant-occupied nonfarm housing (20)",
                    "Imputed rental of owner-occupied nonfarm housing (21)", 
                    "Rental value of farm dwellings (22)", 
                    "Group housing (23)",
                    "Electricity (27)",
                    "Natural gas (28)"]

    ################################ SPECIFY THE PATHS TO THE EXCEL FILES CONTAINING THE DATA FROM BEA ##################################################
    
    PCELoadPath = "/Users/jamesbishop/Documents/Python/TempVenv/Plebs_Macro/MacroBackend/BEA_Data/Datasets/MonthlyData/U20405.xlsx"
    PricesLoadPath = "/Users/jamesbishop/Documents/Python/TempVenv/Plebs_Macro/MacroBackend/BEA_Data/Datasets/MonthlyData/U20404.xlsx"
    QuantisLoadPath = "/Users/jamesbishop/Documents/Python/TempVenv/Plebs_Macro/MacroBackend/BEA_Data/Datasets/MonthlyData/U20403.xlsx"
    Catz_json = '/Users/jamesbishop/Documents/Financial/Investment/MACRO_STUDIES/BEA_Studies/PCE.json'

    pctPricesPath = "/Users/jamesbishop/Documents/Python/TempVenv/Plebs_Macro/MacroBackend/BEA_Data/Datasets/MonthlyData/T20807.xlsx"
    AltPrice_Indexes = "/Users/jamesbishop/Documents/Python/TempVenv/Plebs_Macro/MacroBackend/BEA_Data/Datasets/MonthlyData/T20804.xlsx"
    SavePath = "/Users/jamesbishop/Documents/Financial/Investment/MACRO_STUDIES/BEA_Studies/Series/FinalExportedIndexes"

    # GoodsFromBase = BEA_FisherIndex(PCELoadPath, PricesLoadPath, Catz_json, nearestAggregate="Goods", IndexName="Goods",
    # studyTitle = 'PCE Goods from Base Categories')
    # GoodsFromBase.LoadRefData(pctPricesPath = pctPricesPath)
    # GoodsFromBase.Calculate_FI()
    # GoodsFromBase.PlotIndexSet(title = 'Personal consumption expenditures (PCE) Goods only, manual calculation from base categories')
    # GoodsFromBase.export_index_data(SavePath)

    # Services = BEA_FisherIndex(PCELoadPath, PricesLoadPath, Catz_json, IndexName="Services", nearestAggregate="Services",
    #                            studyTitle = 'PCE Services from Base Categories')
    # Services.LoadRefData(refIndexName="Services", PriceIndexes=GoodsFromBase.Prices_Indexes, pctPrices=GoodsFromBase.PctPrices)
    # Services.Calculate_FI()
    # Services.PlotIndexSet(title="Services from base categories")
    # Services.export_index_data(SavePath)

    # ServExHous = BEA_FisherIndex(PCELoadPath, PricesLoadPath, Catz_json, IndexName="Services_ExHousingExEnergy", nearestAggregate="Services", excludeList=excludeList,
    #                              studyTitle = 'PCE Services excluding Housing & Energy')
    # ServExHous.LoadRefData(refIndexName="PCE services excluding energy and housing", AltPriceIndexesPath=AltPrice_Indexes, pctPricesPath=pctPricesPath)
    # ServExHous.Calculate_FI()
    # ServExHous.PlotIndexSet(title="Services excluding housing & Energy")
    # ServExHous.export_index_data(SavePath)
    customIndexName = 'Services_ExHousingExEnergy'
    ReproducedIndexName = 'Services'

    comp1 = index_comparison(customIndex_loadpath = SavePath+fdel+customIndexName+".xlsx", ReproducedIndex_loadpath = SavePath+fdel+ReproducedIndexName+".xlsx", customIndexName = customIndexName,
                     ReproducedIndexName=ReproducedIndexName)
    comp1.plot_comparison(title = 'Services Excluding Housing & Energy vs Services (manually calculated indexes)')

    plt.show()
