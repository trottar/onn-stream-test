param(
    [ValidateSet("GameSmear", "CollectLatest", "TransportHistory", "AudioHistory")]
    [string]$Mode = "GameSmear"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Bundler = Join-Path $PSScriptRoot "privyhub_debug_bundle.py"
$AudioHistory = Join-Path $PSScriptRoot "privyhub_audio_history.py"
$GameCollector = Join-Path $PSScriptRoot "collect_game_session_diagnostics.py"

function Find-Python {
    $Command = Get-Command python.exe -ErrorAction SilentlyContinue
    if (-not $Command) {
        $Command = Get-Command python -ErrorAction SilentlyContinue
    }
    if (-not $Command) {
        throw "Python could not be found."
    }
    return $Command.Source
}

function Assert-ProjectLayout {
    $Required = @(
        $Bundler,
        $AudioHistory,
        $GameCollector,
        (Join-Path $ProjectRoot "logs\games")
    )
    foreach ($Path in $Required) {
        if (-not (Test-Path $Path)) {
            throw "Required PrivyHub path is missing: $Path"
        }
    }
}

function Invoke-GameCollector {
    param([string]$Python)
    & $Python $GameCollector --root $ProjectRoot
    if ($LASTEXITCODE -ne 0) {
        throw "Existing game diagnostic collector failed with exit code $LASTEXITCODE."
    }
}

function Invoke-Bundler {
    param(
        [string]$Python,
        [string]$BundleMode,
        [string]$SinceUtc = ""
    )

    $Args = @(
        $Bundler,
        "--root", $ProjectRoot,
        "--mode", $BundleMode
    )
    if (-not [string]::IsNullOrWhiteSpace($SinceUtc)) {
        $Args += @("--since-utc", $SinceUtc)
    }

    & $Python @Args
    if ($LASTEXITCODE -ne 0) {
        throw "PrivyHub debug bundler failed with exit code $LASTEXITCODE."
    }
}

Assert-ProjectLayout
$Python = Find-Python

Write-Host ""
Write-Host "PrivyHub diagnostic harness"
Write-Host "Mode: $Mode"
Write-Host ""
Write-Host "Privacy:"
Write-Host "  - This harness does not ask you to paste an IP address."
Write-Host "  - SHARE_ME bundles redact IP/MAC-like addresses from text/JSON evidence."
Write-Host "  - Raw PktMon text/ETL files are never placed in SHARE_ME.zip."
Write-Host ""

switch ($Mode) {
    "GameSmear" {
        $StartUtc = [DateTime]::UtcNow.ToString("o")

        Write-Host "Use the normal PrivyHub app now."
        Write-Host "Launch the game that shows the problem, reproduce it for 30-60 seconds,"
        Write-Host "then end/exit the game normally."
        Write-Host ""
        [void](Read-Host "Press ENTER here after the reproduction is complete")

        Invoke-GameCollector -Python $Python
        Invoke-Bundler -Python $Python -BundleMode "game-smear" -SinceUtc $StartUtc
    }

    "CollectLatest" {
        Invoke-GameCollector -Python $Python
        Invoke-Bundler -Python $Python -BundleMode "latest"
    }

    "TransportHistory" {
        Invoke-Bundler -Python $Python -BundleMode "transport-history"
    }

    "AudioHistory" {
        & $Python $AudioHistory --root $ProjectRoot
        if ($LASTEXITCODE -ne 0) {
            throw "PrivyHub audio-history diagnostic failed with exit code $LASTEXITCODE."
        }
    }
}
