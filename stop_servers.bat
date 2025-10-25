@echo off
chcp 65001 > nul
title Smart Closet - 서버 종료

echo.
echo ========================================
echo      Smart Closet 서버 종료 중...
echo ========================================
echo.

echo 실행 중인 서버 확인 중...
echo.

echo [1/2] Flask 백엔드 서버 종료 중...
taskkill /F /FI "WINDOWTITLE eq Smart Closet Backend*" 2>nul
if errorlevel 1 (
    echo   ⚠ 실행 중인 백엔드 서버가 없습니다.
) else (
    echo   ✓ 백엔드 서버 종료 완료
)

echo.
echo [2/2] React 프론트엔드 서버 종료 중...
taskkill /F /FI "WINDOWTITLE eq Smart Closet Frontend*" 2>nul
if errorlevel 1 (
    echo   ⚠ 실행 중인 프론트엔드 서버가 없습니다.
) else (
    echo   ✓ 프론트엔드 서버 종료 완료
)

echo.
echo 잔여 프로세스 정리 중...
:: Node.js 프로세스 강제 종료 (혹시 모를 잔여 프로세스)
taskkill /F /IM node.exe 2>nul
if not errorlevel 1 (
    echo   ✓ Node.js 프로세스 정리 완료
)

:: Python 서버 프로세스 강제 종료
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *server.py*" 2>nul

echo.
echo ========================================
echo      ✓ 모든 서버가 종료되었습니다.
echo ========================================
echo.
timeout /t 2 > nul
