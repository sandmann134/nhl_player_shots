#!/bin/bash

# Initialize pyenv
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"

# Activate the virtual environment if you are using one
source /Users/alexmann/Documents/Code_Learning/nhl_fromscratch/myenv/bin/activate

# Ensure the logs directory exists
mkdir -p /Users/alexmann/Documents/Code_Learning/nhl_fromscratch/logs

# Run the Python script and log output and errors
/Users/alexmann/.pyenv/versions/3.9.16/bin/python3 /Users/alexmann/Documents/Code_Learning/nhl_fromscratch/main.py >> /Users/alexmann/Documents/Code_Learning/nhl_fromscratch/logs/dailyUpdate_$(date +\%Y-\%m-\%d).log 2>&1