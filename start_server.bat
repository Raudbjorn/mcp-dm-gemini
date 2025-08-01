@echo off
echo Starting TTRPG Assistant MCP Server...
echo.

:: Check if we're in the right directory
if not exist "config\config.yaml" (
    echo ERROR: config\config.yaml not found!
    echo Make sure you're running this script from the project root directory.
    echo.
    pause
    exit /b 1
)

:: Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found! Please install Python 3.10 or later.
    echo.
    pause
    exit /b 1
)

:: Install dependencies if needed
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Install/upgrade dependencies
echo Installing dependencies...
pip install -r requirements.txt

:: Start the server
echo.
echo Starting server at http://localhost:8000
echo Web UI will be available at http://localhost:8000/ui
echo Press Ctrl+C to stop the server
echo.

python mcp_server.py

pause