@echo off
REM ============================================================
REM LFN Audio Toolkit - Long Duration Recorder
REM ============================================================
REM Record audio for extended periods (8+ hours)
REM ============================================================

echo.
echo ============================================================
echo  LFN Audio Toolkit - Long Duration Recorder
echo ============================================================
echo.
echo This tool records audio for extended periods using
echo memory-efficient segmentation.
echo.

REM Prompt for recording duration
set /p "DURATION_HOURS=Enter recording duration in hours (e.g., 8): "

if "%DURATION_HOURS%"=="" (
    echo [ERROR] No duration specified!
    pause
    exit /b 1
)

REM Prompt for output directory
set /p "OUTPUT_DIR=Enter output directory name (default: recording_%date:~-4,4%%date:~-10,2%%date:~-7,2%): "

if "%OUTPUT_DIR%"=="" (
    set "OUTPUT_DIR=recording_%date:~-4,4%%date:~-10,2%%date:~-7,2%"
)

echo.
echo ============================================================
echo  Recording Configuration
echo ============================================================
echo   Duration: %DURATION_HOURS% hours
echo   Output:   %OUTPUT_DIR%\
echo   Segments: 30 minutes each
echo   Format:   48kHz stereo WAV
echo ============================================================
echo.

choice /C YN /M "Start recording with these settings?"

if errorlevel 2 (
    echo.
    echo Recording cancelled.
    pause
    exit /b 0
)

echo.
echo [INFO] Starting long duration recording...
echo [INFO] Press Ctrl+C to stop early
echo.

REM Create Python script call
python -c "from src.long_duration_recorder import LongDurationRecorder; recorder = LongDurationRecorder(sample_rate=48000, channels=2, segment_duration=1800); recorder.record_long_session(%DURATION_HOURS%, '%OUTPUT_DIR%')"

echo.
if %ERRORLEVEL% EQU 0 (
    echo ============================================================
    echo  Recording completed successfully!
    echo ============================================================
    echo.
    echo Segments saved to: %OUTPUT_DIR%\
    echo.
    echo Next steps:
    echo   - Run batch analyzer on recorded segments
    echo   - Run health assessment on results
    echo.
) else (
    echo ============================================================
    echo  Recording stopped or failed!
    echo ============================================================
    echo.
    echo Check the errors above.
    echo Partial recording may be saved in: %OUTPUT_DIR%\
    echo.
)

pause
