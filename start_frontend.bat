@echo off
chcp 65001 > nul
title Smart Closet - Frontend Server

echo ========================================
echo  Smart Closet Frontend Server 시작
echo ========================================
echo.

cd /d "%~dp0"

echo [1/2] 프론트엔드 디렉토리로 이동...
cd front
if errorlevel 1 (
    echo.
    echo 오류: front 폴더를 찾을 수 없습니다.
    echo.
    pause
    exit /b 1
)
echo ✓ 디렉토리 이동 완료
echo.

echo [2/2] React 개발 서버 시작 중...
echo.
echo ========================================
echo 프론트엔드 서버가 시작됩니다.
echo.
echo 주소: https://localhost:3000
echo 자동으로 브라우저가 열립니다.
echo.
echo 종료하려면 Ctrl+C를 누르세요.
echo ========================================
echo.

npm start

if errorlevel 1 (
    echo.
    echo 오류: 서버 시작에 실패했습니다.
    echo.
    echo 해결 방법:
    echo    1. Node.js가 설치되어 있는지 확인
    echo    2. npm install 실행 필요 여부 확인
    echo.
    pause
)
