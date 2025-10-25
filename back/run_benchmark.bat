@echo off
chcp 65001 > nul
echo ========================================
echo Virtual Fitting Performance Benchmark
echo ========================================
echo.
echo Starting benchmark...
echo This may take 5-10 minutes.
echo.

cd /d "%~dp0"

python benchmark_virtual_fitting.py

echo.
echo ========================================
echo Benchmark Complete!
echo Check benchmark_results folder
echo ========================================
echo.
pause
