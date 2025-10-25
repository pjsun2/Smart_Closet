# Smart Closet Virtual Environment Auto-Activation Setup Script
# This script adds auto-activation configuration to your PowerShell profile

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Smart Closet Auto Venv Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# PowerShell profile path
$profilePath = $PROFILE

Write-Host "PowerShell Profile Path: " -ForegroundColor Yellow
Write-Host "   $profilePath" -ForegroundColor Gray
Write-Host ""

# Create profile file if it doesn't exist
if (-not (Test-Path $profilePath)) {
    Write-Host "Profile file not found. Creating new one..." -ForegroundColor Yellow
    New-Item -Path $profilePath -Type File -Force | Out-Null
    Write-Host "Profile file created successfully" -ForegroundColor Green
    Write-Host ""
}

# Code to add
$codeToAdd = @'

# ============================================
# Smart Closet Virtual Environment Auto-Activation
# ============================================
function Enable-SmartClosetVenv {
    $currentPath = Get-Location
    $smartClosetPath = "C:\Users\parkj\Desktop\Smart_Closet"
    
    # Check if current path is Smart_Closet or its subdirectory
    if ($currentPath.Path -like "$smartClosetPath*") {
        $venvPath = Join-Path $smartClosetPath ".venv309\Scripts\Activate.ps1"
        
        # Check if virtual environment is already activated
        if (-not $env:VIRTUAL_ENV) {
            if (Test-Path $venvPath) {
                Write-Host ""
                Write-Host "Activating Smart Closet virtual environment..." -ForegroundColor Cyan
                & $venvPath
                Write-Host "Virtual environment activated: .venv309" -ForegroundColor Green
                Write-Host "Python version: " -NoNewline
                python --version 2>$null
                Write-Host ""
            }
        }
    }
}

# Override cd command to auto-check on directory change
function cd {
    param([string]$Path)
    
    if ($Path) {
        Set-Location $Path
    }
    
    Enable-SmartClosetVenv
}

# Auto-check when PowerShell starts
Enable-SmartClosetVenv
# ============================================

'@

# Read current profile content
$currentContent = ""
if (Test-Path $profilePath) {
    $currentContent = Get-Content $profilePath -Raw -ErrorAction SilentlyContinue
    if ($null -eq $currentContent) {
        $currentContent = ""
    }
}

# Check if already configured
if ($currentContent -like "*Enable-SmartClosetVenv*") {
    Write-Host "Configuration already exists in profile." -ForegroundColor Yellow
    Write-Host ""
    
    $response = Read-Host "Do you want to reconfigure? (y/N)"
    if ($response -ne 'y' -and $response -ne 'Y') {
        Write-Host ""
        Write-Host "Keeping existing configuration." -ForegroundColor Green
        Write-Host ""
        pause
        exit
    }
    
    # Remove existing configuration
    $pattern = '(?s)# ============================================\s*# Smart Closet Virtual Environment Auto-Activation.*?# ============================================\s*'
    $currentContent = $currentContent -replace $pattern, ''
}

# Add new configuration
if ($currentContent) {
    $newContent = $currentContent.TrimEnd() + $codeToAdd
} else {
    $newContent = $codeToAdd
}

# Save to profile
try {
    Set-Content -Path $profilePath -Value $newContent -Encoding UTF8
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Configuration completed successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Virtual environment will auto-activate when you" -ForegroundColor Cyan
    Write-Host "enter the Smart_Closet folder." -ForegroundColor Cyan
    Write-Host ""
    Write-Host "How to test:" -ForegroundColor Yellow
    Write-Host "  1. Open a new PowerShell window" -ForegroundColor Gray
    Write-Host "  2. cd C:\Users\parkj\Desktop\Smart_Closet" -ForegroundColor Gray
    Write-Host "  3. Check for (.venv309) in prompt" -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host ""
    Write-Host "Error: Failed to save configuration" -ForegroundColor Red
    Write-Host "   $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Solution:" -ForegroundColor Yellow
    Write-Host "   1. Run PowerShell as Administrator" -ForegroundColor Gray
    Write-Host "   2. Run this script again" -ForegroundColor Gray
    Write-Host ""
}

# Check execution policy
$executionPolicy = Get-ExecutionPolicy
Write-Host "Current Execution Policy: $executionPolicy" -ForegroundColor Yellow

if ($executionPolicy -eq "Restricted" -or $executionPolicy -eq "AllSigned") {
    Write-Host ""
    Write-Host "Warning: Current policy may prevent script execution." -ForegroundColor Yellow
    Write-Host ""
    
    $response = Read-Host "Change execution policy? (y/N)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        try {
            Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
            Write-Host "Execution policy changed successfully." -ForegroundColor Green
        } catch {
            Write-Host "Failed to change execution policy. Administrator rights may be required." -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "Setup complete! Open a new PowerShell window to test." -ForegroundColor Green
Write-Host ""
pause
