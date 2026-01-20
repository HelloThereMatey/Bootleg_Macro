library(readabs)
library(readxl)

args <- commandArgs(trailingOnly = TRUE)

# Parse input
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