# UniBoard build script (Windows PowerShell 5.1+)
# Usage:  .\build.ps1          -> builds dist\UniBoard
#         .\build.ps1 -Installer -> also compiles UniBoard_Setup.exe via Inno Setup

param(
    [switch]$Installer,
    [string]$InnoSetupCompiler = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
)

$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# Step 1: PyInstaller bundle
# ---------------------------------------------------------------------------
Write-Host "==> Running PyInstaller..." -ForegroundColor Cyan
python -m PyInstaller build.spec --noconfirm
if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller failed." -ForegroundColor Red
    exit $LASTEXITCODE
}

$dist = Join-Path $PSScriptRoot "dist"

# ---------------------------------------------------------------------------
# Step 2: Strip non-English Qt locale files (~40 MB saved)
# ---------------------------------------------------------------------------
Write-Host "==> Stripping non-English locale data..." -ForegroundColor Cyan

# Qt .qm translation catalogs (keep *_en / *_en_US only)
Get-ChildItem -Path $dist -Recurse -Filter "*.qm" -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -notmatch '(^|_)en(_[A-Za-z]{2})?\.qm$' } |
    Remove-Item -Force -ErrorAction SilentlyContinue

# Chromium locale packs for WebEngine (keep en-US.pak)
Get-ChildItem -Path $dist -Recurse -Filter "*.pak" -ErrorAction SilentlyContinue |
    Where-Object { $_.Directory.Name -eq "qtwebengine_locales" -and $_.Name -ne "en-US.pak" } |
    Remove-Item -Force -ErrorAction SilentlyContinue

# ---------------------------------------------------------------------------
# Step 3: Optional Inno Setup installer
# ---------------------------------------------------------------------------
if ($Installer) {
    Write-Host "==> Building installer with Inno Setup..." -ForegroundColor Cyan
    if (-not (Test-Path $InnoSetupCompiler)) {
        # Try the 64-bit install location as a fallback
        $alt = "${env:ProgramFiles}\Inno Setup 6\ISCC.exe"
        if (Test-Path $alt) { $InnoSetupCompiler = $alt }
    }
    if (Test-Path $InnoSetupCompiler) {
        & $InnoSetupCompiler (Join-Path $PSScriptRoot "installer.iss")
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Inno Setup failed." -ForegroundColor Red
            exit $LASTEXITCODE
        }
    } else {
        Write-Warning "ISCC.exe not found at '$InnoSetupCompiler'. Skipping installer step."
        Write-Warning "Install Inno Setup 6 or pass -InnoSetupCompiler <path>."
    }
}

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
$size = (Get-ChildItem (Join-Path $dist "UniBoard") -Recurse -File |
         Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host ("==> Bundle ready: dist\UniBoard  ({0:N0} MB)" -f $size) -ForegroundColor Green
if ($Installer) {
    Write-Host "==> Installer ready: installer_output\" -ForegroundColor Green
}
