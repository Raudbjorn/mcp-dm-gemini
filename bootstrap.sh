#!/bin/bash

# bootstrap.sh
# This script initializes the TTRPG Assistant MCP Server environment.

# --- Configuration ---
VENV_DIR=".venv"
REQUIREMENTS_FILE="requirements.txt"
MCP_SERVER_FILE="mcp_server.py"

# --- Helper Functions ---
print_info() {
    echo "[INFO] $1"
}

print_error() {
    echo "[ERROR] $1" >&2
}

# --- Main Script ---

# 1. Create Python Virtual Environment
if [ ! -d "$VENV_DIR" ]; then
    print_info "Creating Python virtual environment in '$VENV_DIR'..."
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        print_error "Failed to create virtual environment. Please ensure python3 and venv are installed."
        exit 1
    fi
else
    print_info "Virtual environment already exists."
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"
print_info "Virtual environment activated."

# 2. Install Dependencies
if [ -f "$REQUIREMENTS_FILE" ]; then
    print_info "Installing dependencies from '$REQUIREMENTS_FILE'..."
    pip install -r "$REQUIREMENTS_FILE"
    if [ $? -ne 0 ]; then
        print_error "Failed to install dependencies. Please check '$REQUIREMENTS_FILE'."
        exit 1
    fi
else
    print_info "No '$REQUIREMENTS_FILE' found. Skipping dependency installation."
fi

# 3. Check for Redis
print_info "Checking for Redis..."
if ! command -v redis-server &> /dev/null; then
    print_error "Redis is not installed. Please install Redis and ensure 'redis-server' is in your PATH."
    exit 1
fi

# Check if Redis is running
if ! redis-cli ping &> /dev/null; then
    print_info "Redis is not running. Starting Redis server..."
    redis-server --daemonize yes
    if [ $? -ne 0 ]; then
        print_error "Failed to start Redis server."
        exit 1
    fi
    print_info "Redis server started."
else
    print_info "Redis is already running."
fi

# 4. Start MCP Server
if [ -f "$MCP_SERVER_FILE" ]; then
    print_info "Starting MCP Server..."
    python "$MCP_SERVER_FILE"
else
    print_error "'$MCP_SERVER_FILE' not found. Cannot start the server."
    exit 1
fi

print_info "TTRPG Assistant MCP Server is running."
