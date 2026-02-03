#!/bin/bash

<<<<<<< HEAD
# Ensure that the cwd is set to ../bootleg_macro/setup
cd "$(dirname "$0")"
echo "Current working directory:"
pwd

# Define the environment name
ENV_NAME="bm"
SCRIPT_DIR="$(dirname "$0")"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Create the Conda environment
echo "Creating the Conda environment bm"
conda create -n $ENV_NAME python=3.12 -y

# Activate the environment
echo "Activating the environment: $ENV_NAME"
source activate $ENV_NAME

# Install Python packages from requirements.txt
echo "Installing python packages from requirements.txt using pip........"
pip install -r "requirements.txt"

echo "Installing additional python packages using mamba........"

mamba install pytables -y
mamba install statsmodels -y

# Install Node packages
echo "Installing node js from conda forge and then node packages using npm........"
mamba install -c conda-forge nodejs -y
npm install -g @mathieuc/tradingview
npm install -g yahoo-finance2
=======
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
install.packages("readrba")
install.packages("jsonlite")

# Check installed packages and print session info for verification
print(installed.packages()[,c("Package", "Version")])
sessionInfo()
EOF

echo "R package installation completed."

echo "Installing python packages from requirements.txt using pip........"
pip install -r requirements.txt
## The package below is in development by the BEA, early version. I made some changes and have included it
## in MacroBacked. We'll have to check for updates with that one now and then... Don't install it here using the line below. 
#pip install "https://github.com/us-bea/beaapiloc/releases/download/v0.0.2/beaapiloc-0.0.2-py3-none-any.whl"

echo "Installing node packages using npm........"
npm install -g @mathieuc/tradingview
npm install -g  yahoo-finance2
>>>>>>> origin/liquidityRevamp

echo "Bootleg_Macro setup complete."

