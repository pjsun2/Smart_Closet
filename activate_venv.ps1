# PowerShell 자동 활성화 스크립트
# Smart_Closet 폴더 진입 시 .venv309 가상환경 자동 활성화

$venvPath = Join-Path $PSScriptRoot ".venv309\Scripts\Activate.ps1"

if (Test-Path $venvPath) {
    Write-Host "🐍 Smart Closet 가상환경 활성화 중..." -ForegroundColor Cyan
    & $venvPath
    Write-Host "✓ .venv309 가상환경이 활성화되었습니다." -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "⚠ 경고: .venv309 가상환경을 찾을 수 없습니다." -ForegroundColor Yellow
    Write-Host "   경로: $venvPath" -ForegroundColor Yellow
}
