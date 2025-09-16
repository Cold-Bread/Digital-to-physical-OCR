# PowerShell script to replace Makefile for full project setup (backend + frontend)
# Usage: Open PowerShell, navigate to project root, and run: .\setup-project.ps1 [-Clean] [-BackendOnly] [-FrontendOnly] [-Dev]

param(
    [switch]$Clean,
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [switch]$Dev
)

$ErrorActionPreference = 'Stop'

$mainVenv = "backend/main_app/venvMain"
$paddleVenv = "backend/ocr_paddle_service/venvPaddle310"
$mainReq = "backend/main_app/requirements.txt"
$paddleReq = "backend/ocr_paddle_service/requirements.txt"
$frontendDir = "frontend"
$nodeModules = "$frontendDir/node_modules"

function Remove-Dir($path) {
    if (Test-Path $path) {
        Remove-Item -Recurse -Force $path
    }
}

if ($Clean) {
    Write-Host "Cleaning up virtual environments..."
    Remove-Dir $mainVenv
    Remove-Dir $paddleVenv
    Write-Host "Cleaning up node_modules..."
    Remove-Dir $nodeModules
    Write-Host "Clean complete."
    exit 0
}

if (-not $FrontendOnly) {
    # Check Python version
    $pyVersion = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    if ([version]$pyVersion -lt [version]'3.10') {
        Write-Error "Python 3.10+ is required. Found: $pyVersion"
        exit 1
    }

    # Setup main service venv
    if (!(Test-Path $mainVenv)) {
        Write-Host "Creating main service venv..."
        python -m venv $mainVenv
    }
    Write-Host "Installing main service dependencies..."
    & "$mainVenv/Scripts/Activate.ps1"; pip install -r $mainReq

    # Setup paddle service venv
    if (!(Test-Path $paddleVenv)) {
        Write-Host "Creating PaddleOCR venv..."
        python -m venv $paddleVenv
    }
    Write-Host "Installing PaddleOCR dependencies..."
    & "$paddleVenv/Scripts/Activate.ps1"; pip install -r $paddleReq
    Write-Host "Installing PaddlePaddle..."
    & "$paddleVenv/Scripts/Activate.ps1"; pip install paddlepaddle-gpu>=3.1.0 -i https://mirror.baidu.com/pypi/simple
}

if (-not $BackendOnly) {
    # Check Node.js
    try {
        $nodeVersion = & node -v
    } catch {
        Write-Error "Node.js is required. Please install Node.js."
        exit 1
    }
    Write-Host "Installing frontend dependencies..."
    Push-Location $frontendDir
    npm install
    if ($Dev) {
        Write-Host "Installing frontend dev dependencies..."
        npm install -D typescript @types/react @types/node
    }
    Pop-Location
    Write-Host "Frontend setup complete."
}

Write-Host "Project setup complete."
