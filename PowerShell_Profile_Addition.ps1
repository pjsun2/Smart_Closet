# PowerShell 프로필 설정
# Smart_Closet 폴더 진입 시 자동으로 가상환경 활성화

# 현재 위치가 Smart_Closet 폴더인지 확인하는 함수
function Enable-SmartClosetVenv {
    $currentPath = Get-Location
    $smartClosetPath = "C:\Users\parkj\Desktop\Smart_Closet"
    
    # Smart_Closet 폴더 또는 하위 폴더인 경우
    if ($currentPath.Path -like "$smartClosetPath*") {
        $venvPath = Join-Path $smartClosetPath ".venv309\Scripts\Activate.ps1"
        
        # 가상환경이 이미 활성화되어 있는지 확인
        if (-not $env:VIRTUAL_ENV) {
            if (Test-Path $venvPath) {
                Write-Host ""
                Write-Host "🐍 Smart Closet 가상환경 활성화 중..." -ForegroundColor Cyan
                & $venvPath
                Write-Host "✓ .venv309 가상환경이 활성화되었습니다." -ForegroundColor Green
                Write-Host "📍 Python: " -NoNewline
                python --version
                Write-Host ""
            }
        }
    }
}

# cd 명령어 오버라이드 (폴더 이동 시 자동 체크)
function cd {
    param([string]$Path)
    
    if ($Path) {
        Set-Location $Path
    }
    
    Enable-SmartClosetVenv
}

# PowerShell 시작 시 자동 체크
Enable-SmartClosetVenv
