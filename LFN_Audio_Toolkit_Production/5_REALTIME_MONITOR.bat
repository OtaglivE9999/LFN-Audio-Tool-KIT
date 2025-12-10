@echo off
REM ============================================================
REM LFN Audio Toolkit - Real-time Monitor
REM ============================================================
REM Monitor live audio input with real-time analysis
REM ============================================================

echo.
echo ============================================================
echo  LFN Audio Toolkit - Real-time Monitor
echo ============================================================
echo.

REM Check for arguments
if "%~1"=="" (
    echo Starting real-time monitor...
    echo.
    echo Available options:
    echo   --gpu                  Enable GPU acceleration
    echo   --device N             Use specific audio device
    echo   --lfn-threshold 45.0   LFN alert threshold (dB)
    echo   --hf-threshold 50.0    Ultrasonic threshold (dB)
    echo   --auto-start           Start monitoring automatically
    echo   --duration N           Auto-stop after N seconds
    echo.
    echo Press ENTER to start with default settings...
    echo Or press Ctrl+C to cancel and add options
    echo.
    pause
    echo.
    python src\lfn_realtime_monitor.py
) else (
    echo Starting real-time monitor with options: %*
    echo.
    python src\lfn_realtime_monitor.py %*
)

echo.
if %ERRORLEVEL% EQU 0 (
    echo ============================================================
    echo  Monitoring session ended
    echo ============================================================
    echo.
    echo Check outputs:
    echo   - spectrograms\ folder for saved spectrograms
    echo   - lfn_live_log.db for recorded data
    echo   - alerts_log.json for alert history
    echo.
) else (
    echo ============================================================
    echo  Monitoring failed!
    echo ============================================================
    echo.
    echo See errors above or check TROUBLESHOOTING.md
    echo.
)

pause
