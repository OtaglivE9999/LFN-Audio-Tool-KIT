@echo off
REM ============================================================
REM LFN Audio Toolkit - Batch File Analyzer
REM ============================================================
REM Analyze multiple audio files in a directory
REM ============================================================

echo.
echo ============================================================
echo  LFN Audio Toolkit - Batch File Analyzer
echo ============================================================
echo.

REM Check if directory was provided
if "%~1"=="" (
    echo Usage: 4_BATCH_ANALYZER.bat "path\to\audio\files" [options]
    echo.
    echo Options:
    echo   --gpu                  Enable GPU acceleration
    echo   --export-formats       csv json excel
    echo   --lfn-threshold        -20.0  (dB)
    echo   --hf-threshold         -30.0  (dB)
    echo   --no-trends            Disable trend plots
    echo.
    echo Example:
    echo   4_BATCH_ANALYZER.bat "C:\Audio\Files"
    echo   4_BATCH_ANALYZER.bat "C:\Audio\Files" --gpu
    echo.

    REM Prompt for directory
    set /p "AUDIO_DIR=Enter path to audio directory: "

    if "!AUDIO_DIR!"=="" (
        echo [ERROR] No directory specified!
        pause
        exit /b 1
    )

    echo.
    echo [INFO] Analyzing audio files in: !AUDIO_DIR!
    echo.
    python src\lfn_batch_file_analyzer.py "!AUDIO_DIR!"
) else (
    echo [INFO] Analyzing audio files in: %~1
    echo.
    python src\lfn_batch_file_analyzer.py %*
)

echo.
if %ERRORLEVEL% EQU 0 (
    echo ============================================================
    echo  Analysis completed successfully!
    echo ============================================================
    echo.
    echo Results saved to:
    echo   - lfn_analysis_results.csv
    echo   - lfn_analysis_results.json
    echo   - lfn_analysis_results.xlsx
    echo   - spectrograms\ folder
    echo   - trends\ folder
    echo.
) else (
    echo ============================================================
    echo  Analysis failed!
    echo ============================================================
    echo.
    echo See errors above or check TROUBLESHOOTING.md
    echo.
)

pause
