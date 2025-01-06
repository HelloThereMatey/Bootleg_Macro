import os
fdel = os.path.sep
wd = os.path.dirname(__file__)  ## This gets the working directory which is the folder where you have placed this .py file. 
parent = os.path.dirname(wd); grampa = os.path.dirname(parent)
import shutil

import re
import pandas as pd
import subprocess
import json
from pprint import pprint

# Path to the Rscript executable
# You might need to specify the full path if Rscript is not in the PATH
r_script_path = wd+fdel+'abs_get_series.r'
r_executable_path = 'Rscript'  # Or specify path like '/usr/local/bin/Rscript'
abs_path = grampa+fdel+"User_Data"+fdel+"ABS"+fdel+"LastPull"

# Default input for the R script, here we want series_ID for the ABS series,savePath,
series_id = "A2302476C"

def get_abs_series_r(series_id: str = "A2302476C", abs_path: str = abs_path) -> tuple[pd.Series, pd.Series]:
    input_string = series_id+"," +abs_path

    # Setting up the subprocess to run the R script
    process = subprocess.run([r_executable_path, r_script_path, input_string],
                            capture_output=True, text=True)

    # Capturing the output
    output = process.stdout.strip()
    print(output)
    table_name_match = re.search(r'"(.*?)"', output) 
    if table_name_match:
        table_name = table_name_match.group(1)
    else:
        print("No match found.")

    print(f"The name of the table that was downloaded from ABS and saved to directory: {abs_path}, is: {table_name}.xlsx")
    
    files = [file for file in os.listdir(abs_path) if file.endswith(".xlsx")]
    #Remove all Excel files except the one you're using
    for file in files:
        if file != table_name+'.xlsx':
            os.remove(abs_path+fdel+file)

    ### Now load the data from the Excel file that was saved by the R script. 
    all_data = pd.read_excel(abs_path+fdel+table_name+'.xlsx', sheet_name=None, index_col=0)
    data_sheets = [sheet for sheet in all_data.keys() if "Data" in sheet]
    column_found = False
    for data_sheet in data_sheets:
        data = all_data[data_sheet]
        data.columns = data.columns.str.replace(";", "").str.strip()
        all_data[data_sheet] = data
        findcol = data.columns[data.isin([series_id]).any()]
        if findcol.empty:
            continue
        else:
            column = findcol[0]
            column_found = True
    shutil.copy(abs_path+fdel+table_name+'.xlsx', grampa+fdel+"User_Data"+fdel+"ABS"+fdel+"Full_Sheets"+fdel+table_name+".xlsx")
    
    if not column_found:
        raise ValueError(f"Series ID: {series_id} not found in the data sheets.")
    
    series = data[column]
    SeriesInfo = series.iloc[0:9].squeeze()
    series = series.iloc[9:].squeeze()
    index = pd.to_datetime(series.index).date
    seriesName = column.replace(".", "")
    the_series = pd.Series(series.to_list(), index = pd.DatetimeIndex(index), name = seriesName)

    return the_series, SeriesInfo

def browse_rba_tables_r(searchterm: str = "rate") -> pd.DataFrame:
    input_dict = {
        "function": "browse_tables",
        "searchterm": searchterm
    }
    input_string = json.dumps(input_dict)

    rba_script_path = wd + fdel + "read_rba.r"
    process = subprocess.run([r_executable_path, rba_script_path, input_string],
                             capture_output=True, text=True)

    output = str(process.stdout).strip()
    print("\nOutput from R browse RBA tables:\n", output, "\n\n")

    try:
        json_data = json.loads(output)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to decode JSON: {e}")
    df = pd.DataFrame(json_data)
    print("Columns in the dataframe search result: ", df.columns)
    return df

def browse_rba_series_r(searchterm: str = "rate") -> pd.DataFrame:
    input_dict = {
        "function": "browse_series",
        "searchterm": searchterm
    }
    input_string = json.dumps(input_dict)

    rba_script_path = wd + fdel + "read_rba.r"
    process = subprocess.run([r_executable_path, rba_script_path, input_string],
                             capture_output=True, text=True)

    output = str(process.stdout).strip()
    #print("\nOutput from R browse RBA series:\n", output, "\n\n")
    try:
        json_data = json.loads(output)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to decode JSON: {e}")
    df = pd.DataFrame(json_data).rename(columns={"series_id": "id", "table_title": "title"})
    print("Columns in the dataframe search result: ", df.columns)
    return df

def get_rba_series_r(series_id: str = "FIRMMCRTD", rba_path: str = grampa+fdel+"User_Data"+fdel+"RBA") -> pd.DataFrame:
    input_dict = {
        "function": "get_series",
        "series_id": series_id,
        "rba_path": rba_path}
    
    input_string = json.dumps(input_dict)

    rba_script_path = wd + fdel + "read_rba.r"
    process = subprocess.run([r_executable_path, rba_script_path, input_string],
                             capture_output=True, text=True)

    output = str(process.stdout).strip()
    print("\n\n", output, "\n\n")
    json_data = json.loads(output)
    df = pd.DataFrame(json_data)
    return df

if __name__ == "__main__":
    search = get_rba_series_r()
    print(search)

