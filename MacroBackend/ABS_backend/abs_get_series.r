library(readabs)

args <- commandArgs(trailingOnly = TRUE)

# Parse input
input_args <- strsplit(args[1], split=",")
input_vector <- unlist(input_args)

series_id <- input_vector[1]
save_path <- input_vector[2]

# Download the series
table <- read_abs_series(series_id = series_id, path = save_path)

# Extract table_name from the returned data (assuming it's in table[[1,1]])
table_name <- table[[1, 1]]

# Construct the full file path (adjust if readabs uses a different naming convention)
file_path <- file.path(save_path, paste0(table_name, ".xlsx"))

# Check if the file was saved successfully
if (file.exists(file_path)) {
  # Print the full file path for Python to capture
  cat(file_path)
} else {
  # Print an error message if the file wasn't saved
  cat("ERROR: File not saved at", file_path)
}