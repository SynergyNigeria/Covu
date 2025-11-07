@echo off
REM Quick launcher for COVU development
REM Just double-click this file to start everything!

echo.
echo ========================================
echo    COVU Development Environment
echo ========================================
echo.

REM Check if PowerShell script exists
if not exist "start-dev.ps1" (
    echo ERROR: start-dev.ps1 not found!
    echo Please run this from the Backend directory.
    pause
    exit /b 1
)

echo Starting COVU services...
echo.

REM Run PowerShell script
powershell -ExecutionPolicy Bypass -File "start-dev.ps1"

echo.
pause
