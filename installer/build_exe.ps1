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

if (Test-Path "SI5351_Multi_Radio_VFO.spec") {
    Remove-Item "SI5351_Multi_Radio_VFO.spec" -Force
}

# Build EXE
python -m PyInstaller `
    --noconfirm `
    --onefile `
    --windowed `
    --name SI5351_Multi_Radio_VFO `
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