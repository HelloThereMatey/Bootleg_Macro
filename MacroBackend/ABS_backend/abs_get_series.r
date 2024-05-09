library(readabs)

args <- commandArgs(trailingOnly = TRUE)

# The input is expected to be a single string with elements separated by commas
input_args <- strsplit(args[1], split=",")

# Convert the list to a vector
input_vector <- unlist(input_args)

# Example operations on the split components
# Suppose the input string was "5,hello,20"
cat_no <- as.character(input_vector[1])  # Convert first element to string
text <- input_vector[2]  # Capture second element as text
save_path <- as.character(input_vector[2])  # Convert third element to numeric

table <- read_abs_series(series_id = input_vector[1], path = input_vector[2])
table_name <- table[[1, 1]]
print(table_name)