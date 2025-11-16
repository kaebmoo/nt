#!/bin/bash

# Revenue ETL System - Run Script
# ================================
# Script สำหรับรันระบบ Revenue ETL แบบง่าย

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    color=$1
    message=$2
    echo -e "${color}${message}${NC}"
}

# Header
print_color "$GREEN" "======================================"
print_color "$GREEN" "    Revenue ETL System v2.0"
print_color "$GREEN" "======================================"
echo

# Check Python
if ! command -v python3 &> /dev/null
then
    print_color "$RED" "Error: Python 3 is not installed"
    exit 1
fi

# Display menu
print_color "$YELLOW" "Please select an option:"
echo "1) Run All Modules (FI + ETL)"
echo "2) Run FI Module Only"
echo "3) Run ETL Module Only"
echo "4) Run Web Application"
echo "5) Install Dependencies"
echo "6) Run Tests"
echo "7) Exit"
echo

read -p "Enter your choice [1-7]: " choice

case $choice in
    1)
        print_color "$GREEN" "Running All Modules..."
        python3 main.py --module all
        ;;
    2)
        print_color "$GREEN" "Running FI Module..."
        python3 main.py --module fi
        ;;
    3)
        print_color "$GREEN" "Running ETL Module..."
        python3 main.py --module etl
        ;;
    4)
        print_color "$GREEN" "Starting Web Application..."
        print_color "$YELLOW" "Open browser at: http://localhost:8501"
        streamlit run web_app.py
        ;;
    5)
        print_color "$GREEN" "Installing Dependencies..."
        pip install -r requirements.txt
        ;;
    6)
        print_color "$GREEN" "Running Tests..."
        python3 -m pytest tests/
        ;;
    7)
        print_color "$YELLOW" "Exiting..."
        exit 0
        ;;
    *)
        print_color "$RED" "Invalid option!"
        exit 1
        ;;
esac

# Check exit status
if [ $? -eq 0 ]; then
    print_color "$GREEN" "✅ Process completed successfully!"
else
    print_color "$RED" "❌ Process failed!"
    exit 1
fi