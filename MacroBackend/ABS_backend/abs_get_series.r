library(readabs)
<<<<<<< HEAD
library(readxl)
=======
>>>>>>> origin/liquidityRevamp

args <- commandArgs(trailingOnly = TRUE)

# Parse input
<<<<<<< HEAD
input_vector <- strsplit(args[1], split=",")[[1]]

series_id <- trimws(input_vector[1])
save_path <- trimws(input_vector[2])

# Create save directory if it doesn't exist
dir.create(save_path, showWarnings = FALSE, recursive = TRUE)

tryCatch({
  # Use read_abs with series_id parameter
  # read_abs will download and return the data as a tibble, and save files to disk
  result_data <- read_abs(series_id = series_id, path = save_path)
  
  # Find the first Excel file that was saved in the directory
  files <- list.files(save_path, pattern = "\\.xlsx$", full.names = TRUE)
  
  if (length(files) > 0) {
    # Get the most recently modified file
    file_info <- file.info(files)
    newest_file <- rownames(file_info)[which.max(file_info$mtime)]
    cat(newest_file)
  } else {
    cat("ERROR: No Excel files were saved")
  }
}, error = function(e) {
  cat("ERROR:", conditionMessage(e))
})
=======
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
>>>>>>> origin/liquidityRevamp
