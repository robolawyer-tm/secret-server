#!/bin/bash

# This is a simple shortcut to start your server.
# It will create and activate a Python virtualenv 'venv' if one is not present.

echo "Starting Secret Server..."
if [ ! -d "venv" ]; then
    echo "Creating Python virtualenv 'venv' and installing requirements..."
    python -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    if [ -f requirements.txt ]; then
        pip install -r requirements.txt || echo "Warning: failed to install some requirements; please run 'pip install -r requirements.txt' manually inside the venv"
    fi
else
    source venv/bin/activate
fi

python3 web_server.py
