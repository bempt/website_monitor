#!/bin/bash

# Set absolute paths
export HOME="/home/bennett"
export PATH="/home/bennett/anaconda3/bin:$PATH"
export CONDA_EXE="/home/bennett/anaconda3/bin/conda"

# Initialize conda
eval "$(/home/bennett/anaconda3/bin/conda shell.bash hook)"

# Activate environment and run python directly from the environment
cd "$(dirname "$0")"
/home/bennett/anaconda3/envs/website_monitor/bin/python monitor.py

# If the script exits, restart it after a delay
sleep 5
exec "$0"