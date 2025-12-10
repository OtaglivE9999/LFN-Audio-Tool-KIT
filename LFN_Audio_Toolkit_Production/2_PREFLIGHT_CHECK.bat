@echo off
REM ============================================================
REM LFN Audio Toolkit - Pre-flight System Check
REM ============================================================
REM This script verifies your system is ready to run the toolkit
REM ============================================================

echo.
echo ============================================================
echo  LFN Audio Toolkit - Pre-flight Check
echo ============================================================
echo.
echo This will verify:
echo   - Python version
echo   - Required packages
echo   - FFmpeg installation
echo   - Audio devices
echo   - GPU support (optional)
echo   - Disk space
echo   - File permissions
echo.

python preflight_check.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo  System is READY!
    echo ============================================================
    echo.
    echo You can now run the toolkit scripts:
    echo   - 4_BATCH_ANALYZER.bat
    echo   - 5_REALTIME_MONITOR.bat
    echo   - 6_HEALTH_ASSESSMENT.bat
    echo.
) else (
    echo.
    echo ============================================================
    echo  System is NOT READY
    echo ============================================================
    echo.
    echo Please fix the issues above before continuing.
    echo See TROUBLESHOOTING.md for help.
    echo.
)

pause
