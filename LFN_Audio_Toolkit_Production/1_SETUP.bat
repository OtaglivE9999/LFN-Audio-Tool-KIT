@echo off
REM ============================================================
REM LFN Audio Toolkit - Setup & Installation
REM ============================================================
REM This script installs all required dependencies
REM ============================================================

echo.
echo ============================================================
echo  LFN Audio Toolkit - Setup and Installation
echo ============================================================
echo.

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found!
    echo Please install Python 3.8 or higher from python.org
    echo.
    pause
    exit /b 1
)

REM Display Python version
echo [INFO] Checking Python version...
python --version
echo.

REM Run setup script
echo [INFO] Running setup script...
echo.
python setup.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo  Setup completed successfully!
    echo ============================================================
    echo.
    echo Next steps:
    echo   1. Install FFmpeg if needed (see README.md)
    echo   2. Run: 2_PREFLIGHT_CHECK.bat
    echo   3. Run: 3_RUN_TESTS.bat
    echo.
) else (
    echo.
    echo [ERROR] Setup failed! Check errors above.
    echo.
)

pause
