@echo off
chcp 65001 > nul
title Smart Closet - Integrated Launcher

:menu
cls
echo ========================================
echo        Smart Closet Server Manager
echo ========================================
echo.
echo  1. Start Servers (Backend + Frontend)
echo  2. Start Backend Only
echo  3. Start Frontend Only
echo  4. Stop Servers
echo  5. Exit
echo.
echo ========================================
echo.

set /p choice="Select (1-5 or start/stop): "

if "%choice%"=="1" goto start_all
if "%choice%"=="2" goto start_backend
if "%choice%"=="3" goto start_frontend
if "%choice%"=="4" goto stop_servers
if "%choice%"=="5" goto exit
if /i "%choice%"=="start" goto start_all
if /i "%choice%"=="stop" goto stop_servers

echo.
echo Invalid choice. Please enter 1-5 or 'start'/'stop'.
timeout /t 2 > nul
goto menu

:start_all
cls
echo ========================================
echo Smart Closet Integrated Server Start
echo ========================================
echo.

cd /d "%~dp0"

echo Starting backend and frontend servers...
echo.

:: Start backend server in new window
start "Smart Closet Backend" cmd /k "%~dp0start_backend.bat"

:: Wait 2 seconds (backend starts first)
timeout /t 2 /nobreak > nul

:: Start frontend server in new window
start "Smart Closet Frontend" cmd /k "%~dp0start_frontend.bat"

echo.
echo ========================================
echo [OK] Servers started!
echo.
echo Backend: https://localhost:5000
echo Frontend: https://localhost:3000
echo.
echo Each server runs in a separate window.
echo ========================================
echo.
pause
goto menu

:start_backend
cls
echo ========================================
echo Starting Backend Server
echo ========================================
echo.

cd /d "%~dp0"
start "Smart Closet Backend" cmd /k "%~dp0start_backend.bat"

echo.
echo [OK] Backend server started in new window.
echo   URL: https://localhost:5000
echo.
pause
goto menu

:start_frontend
cls
echo ========================================
echo Starting Frontend Server
echo ========================================
echo.

cd /d "%~dp0"
start "Smart Closet Frontend" cmd /k "%~dp0start_frontend.bat"

echo.
echo [OK] Frontend server started in new window.
echo   URL: https://localhost:3000
echo.
pause
goto menu

:stop_servers
cls
echo ========================================
echo Stopping Servers
echo ========================================
echo.

cd /d "%~dp0"
call "%~dp0stop_servers.bat"

echo.
echo Closing backend and frontend windows...
echo.

:: Force close backend and frontend windows only (keep main window)
taskkill /F /FI "WINDOWTITLE eq Smart Closet Backend*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Smart Closet Frontend*" >nul 2>&1

echo [OK] Server windows closed.
echo.
pause
goto menu

:exit
cls
echo ========================================
echo Exiting Smart Closet Server Manager.
echo ========================================
echo.
echo Stopping all running servers...
echo.

:: Execute stop script
call "%~dp0stop_servers.bat"

echo.
echo [OK] All servers stopped.
echo.
timeout /t 2 > nul

:: Force close backend and frontend windows
taskkill /F /FI "WINDOWTITLE eq Smart Closet Backend*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Smart Closet Frontend*" >nul 2>&1

exit /b 0
