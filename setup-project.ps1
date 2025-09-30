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

# Specify the required Python version for PaddleOCR
$requiredPaddlePython = "3.10"

# Function to find python3.10 executable (robust, avoids hanging)
function Get-Python310 {
    $candidates = @(
        @{Name="python3.10"; Args=""},
        @{Name="python310"; Args=""},
        @{Name="py"; Args="-3.10"},
        @{Name="C:/Python310/python.exe"; Args=""}
    )
    foreach ($c in $candidates) {
        $exists = $false
        if ($c.Name -eq "py") {
            # py launcher is usually available on Windows
            $exists = (Get-Command py -ErrorAction SilentlyContinue) -ne $null
        } else {
            $exists = (Get-Command $c.Name -ErrorAction SilentlyContinue) -ne $null
        }
        if ($exists) {
            try {
                if ($c.Args) {
                    $ver = & $c.Name $c.Args -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
                } else {
                    $ver = & $c.Name -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
                }
                if ($ver -eq $requiredPaddlePython) {
                    if ($c.Args) {
                        return "$($c.Name) $($c.Args)"
                    } else {
                        return $c.Name
                    }
                }
            } catch {}
        }
    }
    return $null
}

function Remove-Dir($path) {
    if (Test-Path $path) {
        Remove-Item -Recurse -Force $path
    }
}

if ($Clean) {
    Write-Host "Cleaning up virtual environments..."
    Remove-Dir $mainVenv
    Remove-Dir $paddleVenv
    Write-Host "Cleaning up node_modules and package-lock.json..."
    Remove-Dir $nodeModules
    $packageLock = "$frontendDir/package-lock.json"
    if (Test-Path $packageLock) {
        Remove-Item -Force $packageLock
    }
    Write-Host "Clean complete."
    exit 0
}



if (-not $FrontendOnly) {
    # Check Python version for main service
    $pyVersion = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    if ([version]$pyVersion -lt [version]'3.10') {
        Write-Error "Python 3.10+ is required for main service. Found: $pyVersion"
        exit 1
    }

    # Setup main service venv
    if (!(Test-Path $mainVenv)) {
        Write-Host "Creating main service venv..."
        python -m venv $mainVenv
        Write-Host "Upgrading pip in main service venv..."
        & "$mainVenv/Scripts/Activate.ps1"; python -m pip install --upgrade pip
    }
    Write-Host "Installing main service dependencies..."
    & "$mainVenv/Scripts/Activate.ps1"; pip install -r $mainReq

    Write-Host "Searching for Python 3.10 for PaddleOCR venv..."
    $python310 = Get-Python310
    if (-not $python310) {
        Write-Error "Python 3.10 is required for PaddleOCR. Please install Python 3.10 and ensure it is available as 'python3.10', 'python310', or via 'py -3.10'."
        exit 1
    }
    Write-Host "Found Python 3.10 executable: $python310"
    if (!(Test-Path $paddleVenv)) {
        Write-Host "Creating PaddleOCR venv with Python 3.10..."
        if ($python310 -like '* *') {
            $parts = $python310.Split(' ', 2)
            & $parts[0] $parts[1] -m venv $paddleVenv
        } else {
            & $python310 -m venv $paddleVenv
        }
        Write-Host "Upgrading pip in PaddleOCR venv..."
        & "$paddleVenv/Scripts/Activate.ps1"; python -m pip install --upgrade pip
    }
    Write-Host "Installing PaddlePaddle (using Python 3.10 venv)..."
    & "$paddleVenv/Scripts/Activate.ps1"; python -m pip install paddlepaddle-gpu==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/

    Write-Host "Installing PaddleOCR dependencies (using Python 3.10 venv)..."
    & "$paddleVenv/Scripts/Activate.ps1"; pip install -r $paddleReq
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
# Deactivate any activated virtual environments
if ($env:VIRTUAL_ENV) {
    & deactivate
}

Write-Host "Project setup complete."

