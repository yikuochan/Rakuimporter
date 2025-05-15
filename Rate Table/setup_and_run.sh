#!/bin/bash

# This script sets up the Python virtual environment, installs required packages,
# and runs the selected script

echo "Setting up Python virtual environment..."

# Activate the virtual environment
source venv/bin/activate

# Install required packages
echo "Installing required packages..."
pip install pandas openpyxl

# Ask which script to run
echo ""
echo "Which script would you like to run?"
echo "1. Basic demo (demo_exchange_rate.py)"
echo "2. Comprehensive example (example_usage.py)"
echo "3. List available currencies (list_currencies.py)"
echo "4. Exit without running any script"
read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo "Running the basic demo script..."
        python demo_exchange_rate.py
        ;;
    2)
        echo "Running the comprehensive example script..."
        python example_usage.py
        ;;
    3)
        echo "Listing available currencies..."
        python list_currencies.py
        ;;
    4)
        echo "Exiting without running any script."
        ;;
    *)
        echo "Invalid choice. Exiting."
        ;;
esac

# Deactivate the virtual environment when done
deactivate

echo "Done!"
