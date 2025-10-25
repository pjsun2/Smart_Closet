@echo off
title Smart Closet - 가상환경 활성화된 터미널

echo ========================================
echo   Smart Closet 개발 환경
echo ========================================
echo.

cd /d "%~dp0"

echo 가상환경 활성화 중...
call .venv309\Scripts\activate.bat

if errorlevel 1 (
    echo.
    echo 오류: 가상환경을 찾을 수 없습니다.
    echo    .venv309 폴더가 있는지 확인하세요.
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo 가상환경이 활성화되었습니다!
echo.
echo Python 버전:
python --version
echo.
echo 설치된 패키지 확인: pip list
echo 백엔드 실행: cd back ^& python server.py
echo 프론트엔드 실행: cd front ^& npm start
echo ========================================
echo.

cmd /k
