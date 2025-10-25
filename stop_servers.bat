@echo off
chcp 65001 > nul
title Smart Closet - Stop Servers

echo.
echo ========================================
echo      Stopping Smart Closet Servers...
echo ========================================
echo.

echo Checking running servers...
echo.

echo [1/2] Stopping Flask backend server...
taskkill /F /FI "WINDOWTITLE eq Smart Closet Backend*" 2>nul
if errorlevel 1 (
    echo   [WARNING] No backend server running.
) else (
    echo   [OK] Backend server stopped
)

echo.
echo [2/2] Stopping React frontend server...
taskkill /F /FI "WINDOWTITLE eq Smart Closet Frontend*" 2>nul
if errorlevel 1 (
    echo   [WARNING] No frontend server running.
) else (
    echo   [OK] Frontend server stopped
)

echo.
echo Cleaning up remaining processes...
:: Kill Node.js processes (just in case)
taskkill /F /IM node.exe 2>nul
if not errorlevel 1 (
    echo   [OK] Node.js processes cleaned
)

:: Kill Python server processes
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *server.py*" 2>nul

echo.
echo ========================================
echo      [OK] All servers stopped.
echo ========================================
echo.
timeout /t 2 > nul
