#!/bin/bash

# Configuration
APP_DIR="/home/seal/nt/revenue-report-web"
VENV_DIR="$APP_DIR/venv"
PORT=8501 # Default Streamlit port, adjust if needed

echo "=========================================="
echo "Stopping existing Streamlit process..."
echo "=========================================="

# Find PID of streamlit running app.py
PID=$(pgrep -f "streamlit run app.py")

if [ -n "$PID" ]; then
    echo "Found Streamlit process with PID: $PID"
    kill $PID
    echo "Sent kill signal to $PID"
    
    # Wait for process to exit
    sleep 2
    
    # Force kill if still running
    if ps -p $PID > /dev/null; then
        echo "Process still running, forcing kill..."
        kill -9 $PID
    fi
    echo "Process stopped."
else
    echo "No running Streamlit process found."
fi

echo ""
echo "=========================================="
echo "Starting Streamlit..."
echo "=========================================="

cd $APP_DIR

# Check if venv exists
if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"
    echo "Activated virtual environment."
else
    echo "Error: Virtual environment not found at $VENV_DIR"
    exit 1
fi

# Run in background with nohup
nohup streamlit run app.py > streamlit.log 2>&1 &
NEW_PID=$!

echo "Streamlit started with PID: $NEW_PID"
echo "Log file: $APP_DIR/streamlit.log"
echo "You can check usage with: tail -f streamlit.log"
