@echo off
REM ============================================================
REM LFN Audio Toolkit - Test Suite
REM ============================================================
REM This script runs comprehensive tests to verify functionality
REM ============================================================

echo.
echo ============================================================
echo  LFN Audio Toolkit - Test Suite
echo ============================================================
echo.
echo Running comprehensive tests...
echo.

python run_tests.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo  All tests PASSED!
    echo ============================================================
    echo.
) else (
    echo.
    echo ============================================================
    echo  Some tests FAILED
    echo ============================================================
    echo.
    echo Please check the errors above.
    echo See TROUBLESHOOTING.md for solutions.
    echo.
)

pause
