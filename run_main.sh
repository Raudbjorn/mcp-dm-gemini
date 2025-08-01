#!/bin/bash
# TTRPG Assistant Main Server
# This script runs the main.py FastMCP server directly

set -e

# Change to the script's directory
cd "$(dirname "$0")"

# Check if we're in the right directory
if [ ! -f "config/config.yaml" ]; then
    echo "ERROR: config/config.yaml not found!" >&2
    echo "Make sure you're running this script from the project root directory." >&2
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found! Please install Python 3.10 or later." >&2
    exit 1
fi

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

echo "Starting TTRPG Assistant Main Server..."
echo "This runs the FastMCP server for direct testing and development."
echo "For Claude Desktop integration, use mcp_stdio.sh instead."
echo ""

# Run the main server
exec python3 main.py