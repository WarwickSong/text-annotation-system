$ErrorActionPreference = "Stop"

$ProjectDir = Resolve-Path (Join-Path $PSScriptRoot "..")
$FrontendDir = Join-Path $ProjectDir "frontend"
$DistRoot = Join-Path $ProjectDir "dist"
$DistDir = Join-Path $DistRoot "TextAnnotationSystem"
$ZipPath = Join-Path $DistRoot "TextAnnotationSystem-windows.zip"

$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "npm not found. Please install Node.js LTS and reopen PowerShell."
}
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "python not found. Please activate the Python environment or add Python to PATH."
}

$AsyncLibDir = Join-Path (Split-Path $ProjectDir -Parent) "async_batch_inference"
if (-not (Test-Path $AsyncLibDir)) {
    throw "async_batch_inference core library not found at: $AsyncLibDir`nPlease place async_batch_inference alongside the project directory.`nExpected: <parent>/text_annotation_system and <parent>/async_batch_inference"
}

Write-Host "Stopping existing TextAnnotationSystem processes..."
Get-Process TextAnnotationSystem,python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 1

Write-Host "Building frontend..."
Set-Location $FrontendDir
npm install
npm run build

Write-Host "Installing Python dependencies..."
Set-Location $ProjectDir
python -m pip install -r requirements.txt

Write-Host "Packaging Windows application..."
python -m PyInstaller --clean --noconfirm text_annotation_system.spec

if (-not (Test-Path $DistDir)) {
    throw "Package output not found: $DistDir"
}

Write-Host "Preparing runtime data directory..."
$DataPointer = Join-Path $DistDir "data_dir.txt"
[System.IO.File]::WriteAllText($DataPointer, "data", [System.Text.UTF8Encoding]::new($false))
New-Item -ItemType Directory -Force -Path (Join-Path $DistDir "data") | Out-Null

$UserGuide = Join-Path $DistRoot "使用说明.txt"
if (Test-Path $UserGuide) {
    Copy-Item $UserGuide $DistDir -Force
}

Write-Host "Creating distributable zip..."
if (Test-Path $ZipPath) {
    Remove-Item -Force $ZipPath
}

$zipCreated = $false
for ($i = 1; $i -le 5; $i++) {
    try {
        Start-Sleep -Seconds 2
        Compress-Archive -Path $DistDir -DestinationPath $ZipPath -Force
        $zipCreated = $true
        break
    } catch {
        if ($i -eq 5) {
            throw
        }
        Write-Host "Zip failed because files are still locked. Retrying ($i/5)..."
    }
}

if (-not $zipCreated) {
    throw "Zip package was not created."
}

Write-Host "Build complete."
Write-Host "Folder: $DistDir"
Write-Host "Zip:    $ZipPath"
Write-Host "Send the zip to users. They unzip it and run TextAnnotationSystem.exe."
