library(readrba)
library(jsonlite)

args <- commandArgs(trailingOnly = TRUE)
input_json <- args[1]
# input_json <- '{"func": "get_series", "searchterm": "rate", "series_id": "FIRMMCRTD",
# "rba_path": "/Users/jamesbishop/Documents/Python/Bootleg_Macro/User_Data/RBA"}'
input_list <- fromJSON(input_json)
#print(input_list)

# The function to be called put it in input as something like: 
# {"func": "get_series", "series_id": "ABS_C16", "rba_path": "path/to/save"}
function_name <- input_list$func
cur_hist = c("current", "historical")

if (function_name == "get_series") {
    series_id <- input_list$series_id
    save_path <- input_list$rba_path
    results <- read_rba(series_id = series_id, path = save_path)
    table_name <- results[[1, 1]]
    output_json <- toJSON(results)
    cat(output_json)
} else if (function_name == "browse_tables") {
    searchterm <- input_list$searchterm
    results <- browse_rba_tables(searchterm)
    output_json <- toJSON(results, pretty = FALSE)
    cat(output_json)
} else if (function_name == "browse_series") {
    searchterm <- input_list$searchterm
    results <- browse_rba_series(searchterm)
    output_json <- toJSON(results)
    cat(output_json)
} else if (function_name == "get_table") {
    table_no <- input_list$table_no
    save_path <- input_list$rba_path
    results <- read_rba(table_no = table_no, cur_hist = cur_hist, path = save_path)
    output_json <- toJSON(results)
    cat(output_json)
} else {
    stop("Unknown function name")
}