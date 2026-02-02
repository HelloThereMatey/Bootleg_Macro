#Ensure that the cwd is set to ..botleg_macro/setup
Set-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Path)
Write-Host "Current working directory:"
pwd

# Define the environment name and the YAML file path
$ENV_NAME = "bm"
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$ROOT_DIR = Split-Path -Parent $SCRIPT_DIR

# Create the Conda environment
Write-Host "Creating the Conda environment bm"
conda create -n $ENV_NAME python=3.12 -y

# Activate the environment
Write-Host "Activating the environment: $ENV_NAME"
conda activate $ENV_NAME

# Install Python packages from requirements.txt
Write-Host "Installing python packages from requirements.txt using pip........"
pip install -r "requirements.txt"

Write-Host "Installing additional python packages using mamba........"

# Install additional packages using mamba including node JS.
mamba install pytables -y
mamba install statsmodels -y
mamba install -c conda-forge nodejs -y

# Install Node packages
Write-Host "Installing node packages using npm........"
npm install -g @mathieuc/tradingview
npm install -g yahoo-finance2

Write-Host "Bootleg_Macro setup complete."