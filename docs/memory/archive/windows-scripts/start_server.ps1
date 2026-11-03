# PrivyHub media server launcher
# Resolves every path from this script's location.

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$RangeServer = Join-Path $ProjectRoot "companion\range_server.py"
$MediaRoot = Join-Path $ProjectRoot "media"

if (-not (Test-Path $RangeServer)) {
    throw "Range server not found: $RangeServer"
}

if (-not (Test-Path $MediaRoot)) {
    throw "Media directory not found: $MediaRoot"
}

$PythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue

if (-not $PythonCommand) {
    $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
}

if (-not $PythonCommand) {
    throw "Python was not found in PATH."
}

Write-Host "PrivyHub media server"
Write-Host "Project root: $ProjectRoot"
Write-Host "Media root:   $MediaRoot"
Write-Host ""

& $PythonCommand.Source `
    $RangeServer `
    --root $MediaRoot `
    --host 0.0.0.0 `
    --port 8000

exit $LASTEXITCODE
