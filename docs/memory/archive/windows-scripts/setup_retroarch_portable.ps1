param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path

$RetroArchVersion = "1.22.2"
$RetroArchUrl = "https://buildbot.libretro.com/stable/1.22.2/windows/x86_64/RetroArch.7z"
$RetroArchSha256 = "B2139B1D0F9D4526DC6B5CE23CBB3EFDC766096FA6F2C3DF016818B486AC6372"

$CoreBaseUrl = "https://buildbot.libretro.com/nightly/windows/x86_64/latest"
$CorePackages = @(
    @{ File = "fceumm_libretro.dll.zip"; Core = "fceumm_libretro.dll"; System = "NES" },
    @{ File = "bsnes_libretro.dll.zip"; Core = "bsnes_libretro.dll"; System = "SNES" },
    @{ File = "blastem_libretro.dll.zip"; Core = "blastem_libretro.dll"; System = "Genesis" },
    @{ File = "mednafen_psx_hw_libretro.dll.zip"; Core = "mednafen_psx_hw_libretro.dll"; System = "PlayStation" }
)

$RuntimeRoot = Join-Path $ProjectRoot "runtime"
$RetroRoot = Join-Path $RuntimeRoot "emulators\retroarch"
$CoreRoot = Join-Path $RetroRoot "cores"
$DownloadRoot = Join-Path $RuntimeRoot "downloads\retroarch"
$ToolRoot = Join-Path $RuntimeRoot "tools"
$DataRoot = Join-Path $ProjectRoot "data\games\retroarch"
$SaveRoot = Join-Path $DataRoot "saves"
$StateRoot = Join-Path $DataRoot "states"
$SystemRoot = Join-Path $DataRoot "system"
$ConfigRoot = Join-Path $DataRoot "config"
$LogRoot = Join-Path $ProjectRoot "logs\games"
$ConfigPath = Join-Path $DataRoot "retroarch.cfg"

foreach ($Path in @(
    $RuntimeRoot,
    $RetroRoot,
    $CoreRoot,
    $DownloadRoot,
    $ToolRoot,
    $DataRoot,
    $SaveRoot,
    $StateRoot,
    $SystemRoot,
    $ConfigRoot,
    $LogRoot
)) {
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
}

function Download-File {
    param(
        [Parameter(Mandatory=$true)][string]$Url,
        [Parameter(Mandatory=$true)][string]$Destination
    )

    if ((Test-Path $Destination) -and -not $Force) {
        return
    }

    Write-Host "Downloading $Url"
    Invoke-WebRequest -UseBasicParsing -Uri $Url -OutFile $Destination
}

function Get-Sha256 {
    param([Parameter(Mandatory=$true)][string]$Path)
    return (Get-FileHash -Algorithm SHA256 -Path $Path).Hash.ToUpperInvariant()
}

function Get-SevenZip {
    $Existing = Get-Command "7z.exe" -ErrorAction SilentlyContinue
    if ($Existing) {
        return $Existing.Source
    }

    $SevenZip = Join-Path $ToolRoot "7zr.exe"
    if (-not (Test-Path $SevenZip)) {
        $SevenZipUrl = "https://github.com/ip7z/7zip/releases/download/26.03/7zr.exe"
        Write-Host "Downloading project-local 7zr.exe extractor"
        Invoke-WebRequest -UseBasicParsing -Uri $SevenZipUrl -OutFile $SevenZip
    }

    return $SevenZip
}

$RetroArchive = Join-Path $DownloadRoot "RetroArch-$RetroArchVersion.7z"
Download-File -Url $RetroArchUrl -Destination $RetroArchive

$ActualRetroSha = Get-Sha256 $RetroArchive
if ($ActualRetroSha -ne $RetroArchSha256) {
    throw "RetroArch archive SHA256 mismatch. Expected $RetroArchSha256, got $ActualRetroSha"
}

$RetroExe = Join-Path $RetroRoot "retroarch.exe"

function Merge-DirectoryContents {
    param(
        [Parameter(Mandatory=$true)][string]$Source,
        [Parameter(Mandatory=$true)][string]$Destination
    )

    New-Item -ItemType Directory -Force -Path $Destination | Out-Null

    foreach ($Item in Get-ChildItem -LiteralPath $Source -Force) {
        $Target = Join-Path $Destination $Item.Name

        if ($Item.PSIsContainer) {
            Merge-DirectoryContents -Source $Item.FullName -Destination $Target
        } else {
            Copy-Item -LiteralPath $Item.FullName -Destination $Target -Force
        }
    }
}

function Normalize-RetroArchLayout {
    if (Test-Path $RetroExe) {
        return $true
    }

    $NestedExe = Get-ChildItem `
        -Path $RetroRoot `
        -Recurse `
        -File `
        -Filter "retroarch.exe" `
        -ErrorAction SilentlyContinue |
        Where-Object {
            $_.FullName -ne $RetroExe
        } |
        Select-Object -First 1

    if (-not $NestedExe) {
        return $false
    }

    $NestedRoot = $NestedExe.Directory.FullName

    Write-Host (
        "Normalizing RetroArch archive layout from " +
        "$NestedRoot into $RetroRoot"
    )

    Merge-DirectoryContents `
        -Source $NestedRoot `
        -Destination $RetroRoot

    return (Test-Path $RetroExe)
}

# Reuse a successful prior extraction if it only failed because the official
# archive added its RetroArch-Win64 top-level directory.
$LayoutReady = Normalize-RetroArchLayout

if ($Force -or -not $LayoutReady) {
    Write-Host "Extracting RetroArch $RetroArchVersion into project runtime..."

    $SevenZip = Get-SevenZip
    $ExtractRoot = Join-Path $DownloadRoot "extract-retroarch-$RetroArchVersion"

    if (Test-Path $ExtractRoot) {
        Remove-Item -Recurse -Force $ExtractRoot
    }

    New-Item -ItemType Directory -Force -Path $ExtractRoot | Out-Null

    & $SevenZip x $RetroArchive "-o$ExtractRoot" -y | Out-Null

    if ($LASTEXITCODE -ne 0) {
        throw "7-Zip extraction failed with exit code $LASTEXITCODE"
    }

    $ExtractedExe = Get-ChildItem `
        -Path $ExtractRoot `
        -Recurse `
        -File `
        -Filter "retroarch.exe" `
        -ErrorAction SilentlyContinue |
        Select-Object -First 1

    if (-not $ExtractedExe) {
        throw (
            "RetroArch archive extracted successfully, but no " +
            "retroarch.exe was found inside the archive."
        )
    }

    Merge-DirectoryContents `
        -Source $ExtractedExe.Directory.FullName `
        -Destination $RetroRoot

    Remove-Item -Recurse -Force $ExtractRoot
}

if (-not (Test-Path $RetroExe)) {
    throw (
        "RetroArch extraction/normalization completed but retroarch.exe " +
        "was not found at $RetroExe"
    )
}

$InstalledCores = @()

foreach ($Package in $CorePackages) {
    $PackagePath = Join-Path $DownloadRoot $Package.File
    $CorePath = Join-Path $CoreRoot $Package.Core
    $CoreUrl = "$CoreBaseUrl/$($Package.File)"

    if ($Force -or -not (Test-Path $CorePath)) {
        Download-File -Url $CoreUrl -Destination $PackagePath
        $TempCore = Join-Path $DownloadRoot ("extract-" + [IO.Path]::GetFileNameWithoutExtension($Package.File))
        if (Test-Path $TempCore) {
            Remove-Item -Recurse -Force $TempCore
        }
        New-Item -ItemType Directory -Force -Path $TempCore | Out-Null
        Expand-Archive -Force -Path $PackagePath -DestinationPath $TempCore

        $Found = Get-ChildItem -Path $TempCore -Recurse -File -Filter $Package.Core | Select-Object -First 1
        if (-not $Found) {
            throw "Core archive did not contain $($Package.Core)"
        }
        Copy-Item -Force $Found.FullName $CorePath
        Remove-Item -Recurse -Force $TempCore
    }

    if (-not (Test-Path $CorePath)) {
        throw "Core installation failed: $($Package.Core)"
    }

    $InstalledCores += [ordered]@{
        system = $Package.System
        file = $Package.Core
        source = $CoreUrl
        sha256 = Get-Sha256 $CorePath
    }
}

function Config-Path([string]$Path) {
    return $Path.Replace("\", "/")
}

$Cfg = @(
    '# PrivyHub-managed RetroArch configuration',
    '# Generated by scripts/setup_retroarch_portable.ps1',
    'config_save_on_exit = "false"',
    ('libretro_directory = "' + (Config-Path $CoreRoot) + '"'),
    ('savefile_directory = "' + (Config-Path $SaveRoot) + '"'),
    ('savestate_directory = "' + (Config-Path $StateRoot) + '"'),
    ('system_directory = "' + (Config-Path $SystemRoot) + '"'),
    ('log_dir = "' + (Config-Path $LogRoot) + '"'),
    'video_fullscreen = "false"',
    'video_windowed_fullscreen = "false"',
    'audio_sync = "true"',
    'video_vsync = "true"'
)

Set-Content -Encoding UTF8 -Path $ConfigPath -Value $Cfg

$Manifest = [ordered]@{
    schema = 1
    installed_at = (Get-Date).ToString("o")
    project_root = $ProjectRoot
    retroarch = [ordered]@{
        version = $RetroArchVersion
        source = $RetroArchUrl
        archive_sha256 = $ActualRetroSha
        executable = "runtime/emulators/retroarch/retroarch.exe"
        archive_layout = "normalized from official RetroArch-Win64 package root"
    }
    cores = $InstalledCores
    persistent_data = [ordered]@{
        config = "data/games/retroarch/retroarch.cfg"
        saves = "data/games/retroarch/saves"
        states = "data/games/retroarch/states"
        system = "data/games/retroarch/system"
    }
}

$ManifestPath = Join-Path $RetroRoot "privyhub-install-manifest.json"
$Manifest | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -Path $ManifestPath

Write-Host ""
Write-Host "PrivyHub portable emulator runtime is ready."
Write-Host "RetroArch: runtime\emulators\retroarch"
Write-Host "Persistent game data: data\games\retroarch"
Write-Host "Logs: logs\games"
Write-Host ""
Write-Host "No system-wide RetroArch installation was performed."
Write-Host "No BIOS or copyrighted game content was downloaded."
