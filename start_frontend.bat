@echo off
chcp 65001 > nul
title Smart Closet - Frontend Server

echo ========================================
echo  Smart Closet Frontend Server Start
echo ========================================
echo.

cd /d "%~dp0"

echo [1/2] Moving to frontend directory...
cd front
if errorlevel 1 (
    echo.
    echo ERROR: front folder not found.
    echo.
    pause
    exit /b 1
)
echo [OK] Directory changed
echo.

echo [2/2] Starting React dev server...
echo.
echo ========================================
echo Frontend server is starting.
echo.
echo URL: https://localhost:3000
echo Browser will open automatically.
echo.
echo Press Ctrl+C to stop.
echo ========================================
echo.

npm start

if errorlevel 1 (
    echo.
    echo ERROR: Server failed to start.
    echo.
    echo Solutions:
    echo    1. Check if Node.js is installed
    echo    2. Run npm install if needed
    echo.
    pause
)
