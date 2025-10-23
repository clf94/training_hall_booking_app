#!/bin/bash

APP_DIR="/home/clf94/file/flask_app_raspPi/flask_training_hall_app"
cd "$APP_DIR" || { echo "Failed to cd into $APP_DIR"; exit 1; }

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv || { echo "Failed to create virtual environment"; exit 1; }
fi

# Activate virtual environment
source venv/bin/activate || { echo "Failed to activate virtual environment"; exit 1; }

# Upgrade pip and install dependencies
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "requirements.txt not found!"
    deactivate
    exit 1
fi

# Run the Python script
echo "Running app.py..."
python app.py || { 
    echo "Failed to run app.py."
    deactivate
    exit 1
}

# Deactivate virtual environment
deactivate
