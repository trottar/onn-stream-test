param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$ProjectRoot = Split-Path -Parent $PSScriptRoot

$Version = "v2026.516.143833"
$Asset = "Sunshine-Windows-AMD64-portable.zip"
$Url = "https://github.com/LizardByte/Sunshine/releases/download/$Version/$Asset"
$ExpectedSha256 = "0a3af3dde43b8f2c94ffe04b850ad736d6e1be2b75906779d7094a5ad9d4783b"

$DownloadRoot = Join-Path $ProjectRoot "runtime\downloads\sunshine"
$Archive = Join-Path $DownloadRoot $Asset
$RuntimeRoot = Join-Path $ProjectRoot "runtime\streaming\sunshine"
$DataRoot = Join-Path $ProjectRoot "data\games\sunshine"
$LogRoot = Join-Path $ProjectRoot "logs\games"

$ConfigPath = Join-Path $DataRoot "sunshine.conf"
$AppsPath = Join-Path $DataRoot "apps.json"
$StatePath = Join-Path $DataRoot "sunshine_state.json"
$PKeyPath = Join-Path $DataRoot "cakey.pem"
$CertPath = Join-Path $DataRoot "cacert.pem"
$SunshineLog = Join-Path $LogRoot "sunshine.log"
$ManifestPath = Join-Path $RuntimeRoot "privyhub-install-manifest.json"

New-Item -ItemType Directory -Force -Path $DownloadRoot | Out-Null
New-Item -ItemType Directory -Force -Path $RuntimeRoot | Out-Null
New-Item -ItemType Directory -Force -Path $DataRoot | Out-Null
New-Item -ItemType Directory -Force -Path $LogRoot | Out-Null

function Get-FileSha256 {
    param([Parameter(Mandatory=$true)][string]$Path)

    return (
        Get-FileHash `
            -Algorithm SHA256 `
            -LiteralPath $Path
    ).Hash.ToLowerInvariant()
}

function Merge-DirectoryContents {
    param(
        [Parameter(Mandatory=$true)][string]$Source,
        [Parameter(Mandatory=$true)][string]$Destination
    )

    New-Item -ItemType Directory -Force -Path $Destination | Out-Null

    foreach ($Item in Get-ChildItem -LiteralPath $Source -Force) {
        $Target = Join-Path $Destination $Item.Name

        if ($Item.PSIsContainer) {
            Merge-DirectoryContents `
                -Source $Item.FullName `
                -Destination $Target
        } else {
            Copy-Item `
                -LiteralPath $Item.FullName `
                -Destination $Target `
                -Force
        }
    }
}

if (
    $Force -or
    -not (Test-Path $Archive) -or
    (Get-FileSha256 -Path $Archive) -ne $ExpectedSha256
) {
    Write-Host "Downloading official Sunshine portable host $Version"
    Write-Host $Url

    Invoke-WebRequest `
        -Uri $Url `
        -OutFile $Archive `
        -UseBasicParsing
}

$ActualSha256 = Get-FileSha256 -Path $Archive

if ($ActualSha256 -ne $ExpectedSha256) {
    throw (
        "Sunshine archive SHA-256 mismatch. Expected $ExpectedSha256 " +
        "but received $ActualSha256. Runtime was not installed."
    )
}

$SunshineExe = Join-Path $RuntimeRoot "sunshine.exe"

if ($Force -or -not (Test-Path $SunshineExe)) {
    $ExtractRoot = Join-Path $DownloadRoot "extract-$Version"

    if (Test-Path $ExtractRoot) {
        Remove-Item -Recurse -Force $ExtractRoot
    }

    New-Item -ItemType Directory -Force -Path $ExtractRoot | Out-Null

    Write-Host "Extracting Sunshine into project runtime..."

    Expand-Archive `
        -LiteralPath $Archive `
        -DestinationPath $ExtractRoot `
        -Force

    $ExtractedExe = Get-ChildItem `
        -Path $ExtractRoot `
        -Recurse `
        -File `
        -Filter "sunshine.exe" |
        Select-Object -First 1

    if (-not $ExtractedExe) {
        throw "Portable archive did not contain sunshine.exe"
    }

    Merge-DirectoryContents `
        -Source $ExtractedExe.Directory.FullName `
        -Destination $RuntimeRoot

    Remove-Item -Recurse -Force $ExtractRoot
}

if (-not (Test-Path $SunshineExe)) {
    throw "Sunshine runtime normalization failed: $SunshineExe was not found"
}

# Sunshine remains transport-only. PrivyHub already owns game launch/stop.
$Apps = @{
    env = @{}
    apps = @(
        @{
            name = "PrivyHub Game Session"
            "image-path" = "desktop.png"
        }
    )
}

$Apps |
    ConvertTo-Json -Depth 8 |
    Set-Content `
        -LiteralPath $AppsPath `
        -Encoding UTF8

# Use absolute paths because the companion deliberately passes an explicit
# project-owned config file instead of Sunshine's machine-global defaults.
$ConfigLines = @(
    "sunshine_name = PrivyHub Companion"
    "file_apps = $AppsPath"
    "file_state = $StatePath"
    "credentials_file = $StatePath"
    "pkey = $PKeyPath"
    "cert = $CertPath"
    "log_path = $SunshineLog"
    "upnp = disabled"
    "address_family = ipv4"
    "origin_web_ui_allowed = pc"
    "lan_encryption_mode = 2"
    "wan_encryption_mode = 2"
    "max_bitrate = 20000"
    "controller = disabled"
    "keyboard = enabled"
    "mouse = enabled"
)

$ConfigLines |
    Set-Content `
        -LiteralPath $ConfigPath `
        -Encoding UTF8

$Manifest = @{
    product = "Sunshine"
    role = "PrivyHub game-stream transport host"
    version = $Version
    source = $Url
    asset = $Asset
    sha256 = $ExpectedSha256
    executable = "runtime/streaming/sunshine/sunshine.exe"
    config = "data/games/sunshine/sunshine.conf"
    installed_utc = [DateTime]::UtcNow.ToString("o")
    service_installed = $false
    upnp_enabled = $false
    controller_driver_installed_by_privyhub = $false
}

$Manifest |
    ConvertTo-Json -Depth 8 |
    Set-Content `
        -LiteralPath $ManifestPath `
        -Encoding UTF8

Write-Host ""
Write-Host "PrivyHub Sunshine transport runtime is ready."
Write-Host "Sunshine: runtime\streaming\sunshine"
Write-Host "Persistent config: data\games\sunshine"
Write-Host "Logs: logs\games"
Write-Host ""
Write-Host "Security defaults:"
Write-Host "  UPnP: disabled"
Write-Host "  Web UI: localhost only"
Write-Host "  LAN stream encryption: mandatory"
Write-Host "  Controller forwarding: disabled for first proof"
Write-Host "  Windows service: not installed"
Write-Host ""
Write-Host "No system-wide Sunshine installation was performed."
Write-Host ""
Write-Host "Next: run scripts\install_sunshine_firewall.ps1 from an elevated PowerShell."
