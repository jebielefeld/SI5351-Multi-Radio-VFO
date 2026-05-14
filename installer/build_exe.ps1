# build_exe.ps1
# Builds the SI5351 Multi-Radio VFO Windows EXE package using PyInstaller.

$ErrorActionPreference = "Stop"

Write-Host "Building SI5351 Multi-Radio VFO EXE..." -ForegroundColor Cyan

$RepoRoot = Split-Path -Parent $PSScriptRoot
$SoftwareDir = Join-Path $RepoRoot "pc_software"
$DistDir = Join-Path $SoftwareDir "dist"
$PackageDir = Join-Path $DistDir "SI5351_Multi_Radio_VFO"

Set-Location $SoftwareDir

# Clean old build output
if (Test-Path "build") {
    Remove-Item "build" -Recurse -Force
}

if (Test-Path $PackageDir) {
    Remove-Item $PackageDir -Recurse -Force
}

Get-ChildItem -Path $SoftwareDir -Filter "*.spec" -ErrorAction SilentlyContinue | Remove-Item -Force

python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --paths "." `
    --name SI5351_Multi_Radio_VFO `
    --icon "..\assets\SI5351_Multi_Radio_VFO.ico" `
    --hidden-import=session_manager `
    --hidden-import=output_manager `
    --hidden-import=output_manager_window `
    --hidden-import=profile_manager `
    --hidden-import=radio_window `
    --hidden-import=radio_math `
    --hidden-import=serial_link `
    --hidden-import=cat_radio `
    main.py

# Create clean package folder
New-Item -ItemType Directory -Path $PackageDir | Out-Null

# Move EXE into package folder
Move-Item `
    (Join-Path $DistDir "SI5351_Multi_Radio_VFO.exe") `
    (Join-Path $PackageDir "SI5351_Multi_Radio_VFO.exe") `
    -Force

# Copy required data files
Copy-Item "radio_profiles.json" $PackageDir -Force

if (Test-Path "app_settings.json") {
    Copy-Item "app_settings.json" $PackageDir -Force
}

Write-Host ""
Write-Host "Build complete." -ForegroundColor Green
Write-Host "Package folder:"
Write-Host $PackageDir -ForegroundColor Yellow