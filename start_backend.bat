@echo off
chcp 65001 > nul
title Smart Closet - Backend Server

echo ========================================
echo   Smart Closet Backend Server Start
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] Activating virtual environment...
call .venv309\Scripts\activate.bat
if errorlevel 1 (
    echo.
    echo ERROR: Virtual environment not found.
    echo        Please check if .venv309 folder exists.
    echo.
    pause
    exit /b 1
)
echo [OK] Virtual environment activated
echo.

echo [2/3] Moving to backend directory...
cd back
if errorlevel 1 (
    echo.
    echo ERROR: back folder not found.
    echo.
    pause
    exit /b 1
)
echo [OK] Directory changed
echo.

echo [3/3] Starting Flask server...
echo.
echo ========================================
echo Backend server is starting.
echo.
echo URL: https://localhost:5000
echo.
echo Press Ctrl+C to stop.
echo ========================================
echo.

python server.py

if errorlevel 1 (
    echo.
    echo ERROR: Server failed to start.
    echo.
    pause
)
