@echo off
REM ============================================================
REM LFN Audio Toolkit - Health Impact Assessment
REM ============================================================
REM Analyze health impacts of LFN exposure
REM ============================================================

echo.
echo ============================================================
echo  LFN Audio Toolkit - Health Impact Assessment
echo ============================================================
echo.

REM Check for arguments
if "%~1"=="" (
    echo This tool analyzes LFN exposure health impacts.
    echo.
    echo Options:
    echo   --auto-find            Auto-find CSV results files
    echo   --spectrograms         Analyze spectrograms directly
    echo   path\to\file.csv       Analyze specific CSV file
    echo   path\to\directory      Analyze directory
    echo.

    choice /C AF /N /M "Choose mode: [A]uto-find results, or [F]ile/directory path: "

    if errorlevel 2 (
        set /p "ANALYSIS_PATH=Enter path to CSV file or directory: "
        if "!ANALYSIS_PATH!"=="" (
            echo [ERROR] No path specified!
            pause
            exit /b 1
        )
        echo.
        echo [INFO] Analyzing: !ANALYSIS_PATH!
        echo.
        python src\lfn_health_assessment.py "!ANALYSIS_PATH!"
    ) else (
        echo.
        echo [INFO] Auto-finding analysis results...
        echo.
        python src\lfn_health_assessment.py --auto-find
    )
) else (
    echo [INFO] Running health assessment with: %*
    echo.
    python src\lfn_health_assessment.py %*
)

echo.
if %ERRORLEVEL% EQU 0 (
    echo ============================================================
    echo  Health assessment completed!
    echo ============================================================
    echo.
    echo Report saved with timestamp.
    echo Check the detailed JSON report for complete analysis.
    echo.
) else (
    echo ============================================================
    echo  Health assessment failed!
    echo ============================================================
    echo.
    echo See errors above or check TROUBLESHOOTING.md
    echo.
)

pause
