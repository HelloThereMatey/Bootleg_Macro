from operator import index
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

def find_header_end(index) -> int:
    for i, val in enumerate(index):
        if pd.to_datetime(val, errors='coerce') is not pd.NaT:
            return i
    return 9  # Fallback to original if no date found

# Path to the Rscript executable
# You might need to specify the full path if Rscript is not in the PATH
r_script_path = wd+fdel+'abs_get_series.r'
r_executable_path = 'Rscript'  # Or specify path like '/usr/local/bin/Rscript'
abs_path = grampa+fdel+"User_Data"+fdel+"ABS"+fdel+"LastPull"

# Default input for the R script, here we want series_ID for the ABS series,savePath,
series_id = "A2302476C"

def get_abs_series_r(series_id: str = "A2302476C", abs_path: str = abs_path) -> tuple[pd.Series, pd.Series]:
    input_string = series_id + "," + abs_path

    # Run the R script
    process = subprocess.run([r_executable_path, r_script_path, input_string],
                             capture_output=True, text=True)

    # Capture the output (now the full file path)
    output = process.stdout.strip()
    print("R output:", output)

    # Check for errors in R output
    if output.startswith("ERROR"):
        raise ValueError(f"R script error: {output}")

    # Use the full file path directly (no need for table_name or regex)
    excel_file_path = output

    # Verify the file exists
    if not os.path.isfile(excel_file_path):
        raise FileNotFoundError(f"Excel file not found at: {excel_file_path}")

    # Load the data (rest of your code remains similar)
    all_data = pd.read_excel(excel_file_path, sheet_name=None, index_col=0)
    data_sheets = [sheet for sheet in all_data.keys() if "Data" in sheet]
    column_found = False

    for data_sheet in data_sheets:
        data = all_data[data_sheet]
        #data.columns = data.columns.str.replace(";", "").str.strip()  # Clean semicolons and spaces as before
        all_data[data_sheet] = data
        
        # Find columns containing the series_id (existing logic)
        findcol = data.columns[data.isin([series_id]).any()]
        if findcol.empty:
            continue
        else:
            # Get the string name of the first matching column (for logging/debugging)
            column = findcol[0]
            
            # NEW: Get the integer index (iloc) of the column for reliable selection
            try:
                column_index = data.columns.get_loc(column)  # This gives the positional index
                column_found = True
                print(f"Series ID '{series_id}' found in column at index {column_index} (name: '{column}')")
                break  # Stop after finding the first match
            except KeyError as e:
                print(f"Warning: Could not get location for column '{column}' due to: {e}. Skipping sheet.")
                continue

    if not column_found or column_index is None:
        raise ValueError(f"Series ID: {series_id} not found in any data sheets.")

    # MODIFIED: Use iloc to select the column by index instead of string name
    series = data.iloc[:, column_index]

    # When copying the file, use the full path
    shutil.copy(excel_file_path, grampa + fdel + "User_Data" + fdel + "ABS" + fdel + "Full_Sheets" + fdel + os.path.basename(excel_file_path))
    # NEW: Clean up the "LastPull" directory - delete all files except the current one
    try:
        last_pull_dir = abs_path  # This is the "LastPull" directory
        current_file = os.path.basename(excel_file_path)  # Name of the newly downloaded file
        
        if os.path.exists(last_pull_dir):
            for file_name in os.listdir(last_pull_dir):
                file_path = os.path.join(last_pull_dir, file_name)
                # Only delete if it's a file and not the current one
                if os.path.isfile(file_path) and file_name != current_file:
                    os.remove(file_path)
                    print(f"Deleted old file from LastPull: {file_name}")
        else:
            print(f"Warning: LastPull directory does not exist: {last_pull_dir}")
    except Exception as e:
        print(f"Warning: Could not clean up LastPull directory: {e}")

    # Use the new function to find where the header ends
    start_index = find_header_end(series.index)
    SeriesInfo = series.iloc[:start_index]
    series = series.iloc[start_index:]
    index = pd.to_datetime(series.index).date
    
    # Enhanced series name handling - use the actual column title as the series name
    seriesName = column.replace(".", "")  # Clean up the name but preserve the descriptive title
    the_series = pd.Series(series.to_list(), index = pd.DatetimeIndex(index), name = seriesName)
    
    # Enhanced SeriesInfo to include the proper title and ensure object dtype
    SeriesInfo = SeriesInfo.copy().astype('object')  # Ensure object dtype
    SeriesInfo.name = series_id  # Ensure SeriesInfo has the series_id as its name
    if 'title' not in SeriesInfo.index:
        SeriesInfo['title'] = seriesName  # Add the descriptive title to SeriesInfo
    else:
        # Update existing title if it's less descriptive than the column name
        if len(str(SeriesInfo['title'])) < len(seriesName):
            SeriesInfo['title'] = seriesName
    
    print(f"ABS series created with name: {seriesName}")

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

