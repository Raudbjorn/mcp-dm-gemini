#!/bin/bash

# bootstrap.sh
# This script initializes the TTRPG Assistant MCP Server environment.
# Updated for ChromaDB-based architecture with enhanced search capabilities.

# --- Configuration ---
VENV_DIR=".venv"
REQUIREMENTS_FILE="requirements.txt"
MCP_SERVER_FILE="mcp_server.py"
HOST="0.0.0.0"
PORT="8000"

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

# 2. Install/Update Dependencies
if [ -f "$REQUIREMENTS_FILE" ]; then
    print_info "Installing/updating dependencies from '$REQUIREMENTS_FILE'..."
    pip install -r "$REQUIREMENTS_FILE"
    if [ $? -ne 0 ]; then
        print_error "Failed to install dependencies. Please check '$REQUIREMENTS_FILE'."
        exit 1
    fi
else
    print_info "No '$REQUIREMENTS_FILE' found. Skipping dependency installation."
fi

# 3. Initialize ChromaDB directory
print_info "Initializing ChromaDB directory..."
mkdir -p ./chroma_db
mkdir -p ./pattern_cache

# 4. Create config file if it doesn't exist
if [ ! -f "config/config.yaml" ]; then
    print_info "Creating default configuration..."
    mkdir -p config
    cat > config/config.yaml << 'EOF'
chromadb:
  persist_directory: "./chroma_db"
  anonymized_telemetry: true

embedding:
  model: "all-MiniLM-L6-v2"
  batch_size: 32
  cache_embeddings: true

pdf_processing:
  max_file_size_mb: 100
  enable_adaptive_learning: true
  pattern_cache_dir: "./pattern_cache"

search:
  default_max_results: 5
  similarity_threshold: 0.7
  enable_keyword_fallback: true
  enable_hybrid_search: true

mcp:
  server_name: "ttrpg-assistant"
  version: "1.0.0"

discord:
  token: "YOUR_DISCORD_BOT_TOKEN"
EOF
fi

# 5. Display usage options
print_info "TTRPG Assistant setup complete!"
print_info ""
print_info "Usage options:"
print_info "1. For Claude Desktop integration: ./mcp_stdio.sh"
print_info "2. For direct FastMCP testing: ./run_main.sh"
print_info "3. For web UI server: python $MCP_SERVER_FILE"
print_info ""
print_info "The system now uses ChromaDB for vector storage and enhanced search."
print_info "Configuration is stored in config/config.yaml"