#!/bin/bash

# Define the environment name and the YAML file path
ENV_NAME="bm"
# Path to the YAML file - make sure to edit this according to your actual path
YAML_PATH="bootleg_env.yaml"

# Create the Conda environment
echo "Creating the Conda environment from $YAML_FILE"
conda env create -n $ENV_NAME  -f bootleg_env.yaml

# Activate the environment
echo "Activating the environment: $ENV_NAME"
source activate $ENV_NAME  # Or `conda activate $ENV_NAME` depending on your conda setup

# Run R script to install packages
echo "Installing R packages from CRAN"
R --vanilla <<EOF
options(repos='http://cran.rstudio.com/')

# Installing specific packages
install.packages('tidyverse')
install.packages('dplyr')
install.packages('readabs')
install.packages('ggplot2')

# Check installed packages and print session info for verification
print(installed.packages()[,c("Package", "Version")])
sessionInfo()
EOF

echo "R package installation completed."

echo "Installing python packages from requirements.txt using pip........"
pip install -r requirements.txt

