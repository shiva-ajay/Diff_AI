@echo off
echo.
echo ========================================
echo   P&ID Diff Finder Web Application
echo ========================================
echo.

REM Check if poetry is installed
poetry --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Poetry not found. Please install Poetry first.
    echo Visit: https://python-poetry.org/docs/#installation
    pause
    exit /b 1
)

echo Installing dependencies...
poetry install
if %errorlevel% neq 0 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Starting web server...
echo Server will be available at: http://localhost:8000
echo Press Ctrl+C to stop the server
echo.

REM Start the server
poetry run python app.py

pause
