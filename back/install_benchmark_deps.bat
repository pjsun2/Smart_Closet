@echo off
chcp 65001 > nul
echo ========================================
echo Installing Benchmark Dependencies
echo ========================================
echo.

cd /d "%~dp0"

echo Installing matplotlib...
pip install matplotlib

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Now you can run:
echo   run_benchmark.bat
echo.
pause
