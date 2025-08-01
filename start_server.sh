#!/bin/bash

echo "Starting TTRPG Assistant MCP Server..."
echo

# Check if we're in the right directory
if [ ! -f "config/config.yaml" ]; then
    echo "ERROR: config/config.yaml not found!"
    echo "Make sure you're running this script from the project root directory."
    echo
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found! Please install Python 3.10 or later."
    echo
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install/upgrade dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Start the server
echo
echo "Starting server at http://localhost:8000"
echo "Web UI will be available at http://localhost:8000/ui"
echo "Press Ctrl+C to stop the server"
echo

python3 mcp_server.py