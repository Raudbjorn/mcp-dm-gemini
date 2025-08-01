@echo off
:: TTRPG Assistant MCP Protocol Handler
:: This script runs the MCP protocol over stdin/stdout for Claude Desktop integration
:: No server process is started - communication happens via standard I/O

:: Change to the script's directory
cd /d "%~dp0"

:: Check if we're in the right directory
if not exist "config\config.yaml" (
    echo ERROR: config\config.yaml not found! >&2
    echo Make sure you're running this script from the project root directory. >&2
    exit /b 1
)

:: Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found! Please install Python 3.10 or later. >&2
    exit /b 1
)

:: Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

:: Run the MCP protocol handler (stdio communication)
python mcp_server_standalone.py