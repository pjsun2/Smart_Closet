@echo off
chcp 65001 > nul
title Smart Closet - 통합 실행

:menu
cls
echo ========================================
echo        Smart Closet 서버 관리
echo ========================================
echo.
echo  1. 서버 시작 (백엔드 + 프론트엔드)
echo  2. 백엔드만 시작
echo  3. 프론트엔드만 시작
echo  4. 서버 종료
echo  5. 프로그램 종료
echo.
echo ========================================
echo.

set /p choice="선택 (1-5 또는 start/stop): "

if "%choice%"=="1" goto start_all
if "%choice%"=="2" goto start_backend
if "%choice%"=="3" goto start_frontend
if "%choice%"=="4" goto stop_servers
if "%choice%"=="5" goto exit
if /i "%choice%"=="start" goto start_all
if /i "%choice%"=="stop" goto stop_servers

echo.
echo 잘못된 선택입니다. 1-5 사이의 숫자 또는 'start', 'stop'을 입력하세요.
timeout /t 2 > nul
goto menu

:start_all
cls
echo ========================================
echo Smart Closet 통합 서버 시작
echo ========================================
echo.

cd /d "%~dp0"

echo 백엔드와 프론트엔드 서버를 동시에 시작합니다...
echo.

:: 백엔드 서버를 새 창에서 실행
start "Smart Closet Backend" cmd /k "%~dp0start_backend.bat"

:: 2초 대기 (백엔드가 먼저 시작되도록)
timeout /t 2 /nobreak > nul

:: 프론트엔드 서버를 새 창에서 실행
start "Smart Closet Frontend" cmd /k "%~dp0start_frontend.bat"

echo.
echo ========================================
echo ✓ 서버가 시작되었습니다!
echo.
echo 백엔드: https://localhost:5000
echo 프론트엔드: https://localhost:3000
echo.
echo 각 서버는 별도 창에서 실행됩니다.
echo ========================================
echo.
pause
goto menu

:start_backend
cls
echo ========================================
echo 백엔드 서버 시작
echo ========================================
echo.

cd /d "%~dp0"
start "Smart Closet Backend" cmd /k "%~dp0start_backend.bat"

echo.
echo ✓ 백엔드 서버가 새 창에서 시작되었습니다.
echo   주소: https://localhost:5000
echo.
pause
goto menu

:start_frontend
cls
echo ========================================
echo 프론트엔드 서버 시작
echo ========================================
echo.

cd /d "%~dp0"
start "Smart Closet Frontend" cmd /k "%~dp0start_frontend.bat"

echo.
echo ✓ 프론트엔드 서버가 새 창에서 시작되었습니다.
echo   주소: https://localhost:3000
echo.
pause
goto menu

:stop_servers
cls
echo ========================================
echo 서버 중지
echo ========================================
echo.

cd /d "%~dp0"
call "%~dp0stop_servers.bat"

echo.
echo 백엔드 및 프론트엔드 창을 종료합니다...
echo.

:: 백엔드 및 프론트엔드 창만 강제 종료 (메인 창은 유지)
taskkill /F /FI "WINDOWTITLE eq Smart Closet Backend*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Smart Closet Frontend*" >nul 2>&1

echo ✓ 서버 창이 종료되었습니다.
echo.
pause
goto menu

:exit
cls
echo ========================================
echo Smart Closet 서버 관리를 종료합니다.
echo ========================================
echo.
echo 실행 중인 모든 서버를 종료합니다...
echo.

:: 서버 종료 스크립트 실행
call "%~dp0stop_servers.bat"

echo.
echo ✓ 모든 서버가 종료되었습니다.
echo.
timeout /t 2 > nul

:: 백엔드 및 프론트엔드 창 강제 종료
taskkill /F /FI "WINDOWTITLE eq Smart Closet Backend*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Smart Closet Frontend*" >nul 2>&1

exit /b 0
