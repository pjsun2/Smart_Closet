@echo off
title Smart Closet - Virtual Environment Terminal

echo ========================================
echo   Smart Closet Development Environment
echo ========================================
echo.

cd /d "%~dp0"

echo Activating virtual environment...
call .venv309\Scripts\activate.bat

if errorlevel 1 (
    echo.
    echo ERROR: Virtual environment not found.
    echo        Please check if .venv309 folder exists.
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Virtual environment activated!
echo.
echo Python version:
python --version
echo.
echo Check installed packages: pip list
echo Run backend: cd back ^& python server.py
echo Run frontend: cd front ^& npm start
echo ========================================
echo.

cmd /k
