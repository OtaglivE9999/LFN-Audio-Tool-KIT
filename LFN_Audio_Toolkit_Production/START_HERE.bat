@echo off
REM ============================================================
REM LFN Audio Toolkit - Main Menu
REM ============================================================
REM Quick access to all toolkit functions
REM ============================================================

:MENU
cls
echo.
echo ============================================================
echo           LFN Audio Analysis Toolkit v2.0.0
echo ============================================================
echo.
echo  SETUP AND TESTING:
echo    [1] Setup and Install Dependencies
echo    [2] Pre-flight System Check
echo    [3] Run Test Suite
echo.
echo  ANALYSIS TOOLS:
echo    [4] Batch File Analyzer (analyze audio files)
echo    [5] Real-time Monitor (live audio monitoring)
echo    [6] Health Impact Assessment
echo    [7] Long Duration Recorder (8+ hours)
echo.
echo  DOCUMENTATION:
echo    [8] Open README
echo    [9] Open Troubleshooting Guide
echo.
echo    [0] Exit
echo.
echo ============================================================
echo.

choice /C 1234567890 /N /M "Select option (1-9, or 0 to exit): "

if errorlevel 10 goto EXIT
if errorlevel 9 goto TROUBLESHOOTING
if errorlevel 8 goto README
if errorlevel 7 goto LONG_RECORDER
if errorlevel 6 goto HEALTH
if errorlevel 5 goto REALTIME
if errorlevel 4 goto BATCH
if errorlevel 3 goto TESTS
if errorlevel 2 goto PREFLIGHT
if errorlevel 1 goto SETUP

:SETUP
cls
call 1_SETUP.bat
goto MENU

:PREFLIGHT
cls
call 2_PREFLIGHT_CHECK.bat
goto MENU

:TESTS
cls
call 3_RUN_TESTS.bat
goto MENU

:BATCH
cls
call 4_BATCH_ANALYZER.bat
goto MENU

:REALTIME
cls
call 5_REALTIME_MONITOR.bat
goto MENU

:HEALTH
cls
call 6_HEALTH_ASSESSMENT.bat
goto MENU

:LONG_RECORDER
cls
call 7_LONG_DURATION_RECORDER.bat
goto MENU

:README
cls
echo.
echo Opening README.md...
echo.
if exist README.md (
    start README.md
) else (
    echo [ERROR] README.md not found!
    pause
)
goto MENU

:TROUBLESHOOTING
cls
echo.
echo Opening TROUBLESHOOTING.md...
echo.
if exist TROUBLESHOOTING.md (
    start TROUBLESHOOTING.md
) else (
    echo [ERROR] TROUBLESHOOTING.md not found!
    pause
)
goto MENU

:EXIT
cls
echo.
echo ============================================================
echo  Thank you for using LFN Audio Toolkit!
echo ============================================================
echo.
echo For support, see:
echo   - README.md
echo   - TROUBLESHOOTING.md
echo   - DEPLOYMENT_CHECKLIST.md
echo.
timeout /t 3
exit /b 0
