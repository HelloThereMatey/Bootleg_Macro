#!/bin/bash

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

echo "Bootleg_Macro setup complete."

