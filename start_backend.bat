@echo off
chcp 65001 > nul
title Smart Closet - Backend Server

echo ========================================
echo   Smart Closet Backend Server 시작
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] 가상환경 활성화 중...
call .venv309\Scripts\activate.bat
if errorlevel 1 (
    echo.
    echo 오류: 가상환경을 찾을 수 없습니다.
    echo    .venv309 폴더가 있는지 확인하세요.
    echo.
    pause
    exit /b 1
)
echo ✓ 가상환경 활성화 완료
echo.

echo [2/3] 백엔드 디렉토리로 이동...
cd back
if errorlevel 1 (
    echo.
    echo 오류: back 폴더를 찾을 수 없습니다.
    echo.
    pause
    exit /b 1
)
echo ✓ 디렉토리 이동 완료
echo.

echo [3/3] Flask 서버 시작 중...
echo.
echo ========================================
echo 백엔드 서버가 시작됩니다.
echo.
echo 주소: https://localhost:5000
echo.
echo 종료하려면 Ctrl+C를 누르세요.
echo ========================================
echo.

python server.py

if errorlevel 1 (
    echo.
    echo 오류: 서버 시작에 실패했습니다.
    echo.
    pause
)
