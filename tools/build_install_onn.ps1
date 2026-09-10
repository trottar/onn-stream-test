# PrivyHub - Build, install, and launch on a physical ONN device.
# This file can live under <project root>\tools.
# Project paths are derived from $PSScriptRoot; ADB is discovered.

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$AndroidProject = Join-Path $ProjectRoot "PrivyHub"

$Apk = Join-Path `
    $AndroidProject `
    "app\build\outputs\apk\debug\app-debug.apk"

$Package = "com.safeiot.privyhub"
$Activity = ".MainActivity"


function Resolve-LocalPropertiesSdk {
    param(
        [string]$LocalPropertiesPath
    )

    if (-not (Test-Path $LocalPropertiesPath)) {
        return $null
    }

    $SdkLine = Get-Content $LocalPropertiesPath |
        Where-Object { $_ -match '^\s*sdk\.dir\s*=' } |
        Select-Object -First 1

    if (-not $SdkLine) {
        return $null
    }

    $SdkDir = ($SdkLine -split '=', 2)[1].Trim()

    # Android local.properties escapes Windows path separators/colon.
    $SdkDir = $SdkDir -replace '\\:', ':'
    $SdkDir = $SdkDir -replace '\\\\', '\'

    if ($SdkDir) {
        return $SdkDir
    }

    return $null
}


function Find-Adb {
    $Command = Get-Command adb.exe -ErrorAction SilentlyContinue

    if (-not $Command) {
        $Command = Get-Command adb -ErrorAction SilentlyContinue
    }

    if ($Command) {
        return $Command.Source
    }


    $SdkRoots = @()

    if ($env:ANDROID_SDK_ROOT) {
        $SdkRoots += $env:ANDROID_SDK_ROOT
    }

    if ($env:ANDROID_HOME) {
        $SdkRoots += $env:ANDROID_HOME
    }

    $LocalSdk = Resolve-LocalPropertiesSdk `
        (Join-Path $AndroidProject "local.properties")

    if ($LocalSdk) {
        $SdkRoots += $LocalSdk
    }


    foreach ($SdkRoot in ($SdkRoots | Select-Object -Unique)) {
        $Candidate = Join-Path $SdkRoot "platform-tools\adb.exe"

        if (Test-Path $Candidate) {
            return $Candidate
        }
    }


    throw @"
ADB could not be found.

Put adb in PATH, set ANDROID_SDK_ROOT/ANDROID_HOME,
or ensure PrivyHub\local.properties contains a valid sdk.dir.
"@
}


if (-not (Test-Path $AndroidProject)) {
    throw "PrivyHub Android project not found: $AndroidProject"
}


$Adb = Find-Adb


Set-Location $AndroidProject


Write-Host ""
Write-Host "========================================"
Write-Host " PrivyHub - Build / Install / Launch"
Write-Host "========================================"
Write-Host ""
Write-Host "Project root:    $ProjectRoot"
Write-Host "Android project: $AndroidProject"
Write-Host "ADB:             $Adb"
Write-Host ""


Write-Host "[1/4] Building debug APK..."

& .\gradlew.bat assembleDebug

if ($LASTEXITCODE -ne 0) {
    throw "Gradle build failed with exit code $LASTEXITCODE"
}


if (-not (Test-Path $Apk)) {
    throw "Build reported success, but APK was not found: $Apk"
}


Write-Host ""
Write-Host "[2/4] Finding physical ONN ADB target..."


# PRIVYHUB_ADB_WIRELESS_RECOVERY_01
# A paired Wireless debugging target can temporarily disappear from
# `adb devices` and mDNS. Cache only the last successful target privately
# outside the repository and never print it.
$AdbPrivateRoot = Join-Path $env:LOCALAPPDATA "PrivyHub\adb"
$AdbTargetCache = Join-Path $AdbPrivateRoot "last_wireless_target.txt"


function Get-OnlineAdbDevices {
    $Lines = & $Adb devices

    return @(
        $Lines |
        Select-Object -Skip 1 |
        ForEach-Object {
            $Line = $_.Trim()
            if ($Line -match '^(.*)\tdevice$') {
                $matches[1]
            }
        }
    )
}


function Get-PhysicalOnnCandidates {
    param([string[]]$OnlineDevices)

    return @(
        $OnlineDevices |
        Where-Object {
            $_ -ne "emulator-5554" -and
            (
                $_ -match '^adb-.*\._adb-tls-connect\._tcp$' -or
                $_ -match '^\d{1,3}(\.\d{1,3}){3}:\d+$'
            )
        }
    )
}


function Test-AdbTargetOnline {
    param([string]$Target)

    if ([string]::IsNullOrWhiteSpace($Target)) {
        return $false
    }

    $State = (
        & $Adb -s $Target get-state 2>$null |
        Out-String
    ).Trim()

    return ($LASTEXITCODE -eq 0 -and $State -eq "device")
}


function Try-AdbConnectTarget {
    param([string]$Target)

    if ([string]::IsNullOrWhiteSpace($Target)) {
        return $false
    }

    & $Adb connect $Target *> $null
    Start-Sleep -Milliseconds 750

    return Test-AdbTargetOnline $Target
}


function Read-CachedAdbTarget {
    if (-not (Test-Path -LiteralPath $AdbTargetCache -PathType Leaf)) {
        return $null
    }

    try {
        $Value = (Get-Content -LiteralPath $AdbTargetCache -Raw).Trim()
    }
    catch {
        return $null
    }

    if (
        $Value -match '^adb-.*\._adb-tls-connect\._tcp$' -or
        $Value -match '^\d{1,3}(\.\d{1,3}){3}:\d+$'
    ) {
        return $Value
    }

    return $null
}


function Save-CachedAdbTarget {
    param([string]$Target)

    if ([string]::IsNullOrWhiteSpace($Target)) {
        return
    }

    try {
        New-Item -ItemType Directory -Path $AdbPrivateRoot -Force |
            Out-Null

        Set-Content `
            -LiteralPath $AdbTargetCache `
            -Value $Target `
            -NoNewline `
            -Encoding UTF8
    }
    catch {
        # Cache failure must never block a valid build/install.
    }
}


function Get-MdnsConnectTargets {
    $Lines = & $Adb mdns services 2>$null

    if ($LASTEXITCODE -ne 0) {
        return @()
    }

    return @(
        $Lines |
        ForEach-Object {
            $Line = $_.Trim()

            if ($Line -match '^(.*)\t(_adb-tls-connect\._tcp)\t(.+)$') {
                $Instance = $matches[1].Trim()
                $Service = $matches[2].Trim()

                if ($Instance) {
                    "$Instance.$Service"
                }
            }
        } |
        Where-Object { $_ } |
        Select-Object -Unique
    )
}


function Resolve-OnlineOnn {
    $OnlineDevices = Get-OnlineAdbDevices
    $Candidates = Get-PhysicalOnnCandidates $OnlineDevices

    if ($Candidates.Count -eq 1) {
        return $Candidates[0]
    }

    if ($Candidates.Count -gt 1) {
        $MdnsCandidates = @(
            $Candidates |
            Where-Object {
                $_ -match '^adb-.*\._adb-tls-connect\._tcp$'
            }
        )

        if ($MdnsCandidates.Count -eq 1) {
            return $MdnsCandidates[0]
        }
    }

    return $null
}


function Resolve-OnnWithRecovery {
    $Cached = Read-CachedAdbTarget

    if ($Cached) {
        if (
            (Test-AdbTargetOnline $Cached) -or
            (Try-AdbConnectTarget $Cached)
        ) {
            return @{
                Target = $Cached
                Source = "cached"
            }
        }
    }

    $Online = Resolve-OnlineOnn
    if ($Online) {
        return @{ Target = $Online; Source = "online" }
    }

    for ($Attempt = 1; $Attempt -le 3; $Attempt++) {
        foreach ($Target in (Get-MdnsConnectTargets)) {
            if (Try-AdbConnectTarget $Target) {
                return @{ Target = $Target; Source = "mdns" }
            }
        }

        $Online = Resolve-OnlineOnn
        if ($Online) {
            return @{ Target = $Online; Source = "online" }
        }

        if ($Attempt -lt 3) {
            Start-Sleep -Seconds 2
        }
    }

    & $Adb reconnect offline *> $null
    Start-Sleep -Seconds 1

    $Online = Resolve-OnlineOnn
    if ($Online) {
        return @{ Target = $Online; Source = "reconnect" }
    }

    & $Adb kill-server *> $null
    Start-Sleep -Milliseconds 750
    & $Adb start-server *> $null
    Start-Sleep -Seconds 2

    if ($Cached -and (Try-AdbConnectTarget $Cached)) {
        return @{ Target = $Cached; Source = "cached-after-server-restart" }
    }

    for ($Attempt = 1; $Attempt -le 3; $Attempt++) {
        $Online = Resolve-OnlineOnn
        if ($Online) {
            return @{ Target = $Online; Source = "online-after-server-restart" }
        }

        foreach ($Target in (Get-MdnsConnectTargets)) {
            if (Try-AdbConnectTarget $Target) {
                return @{
                    Target = $Target
                    Source = "mdns-after-server-restart"
                }
            }
        }

        if ($Attempt -lt 3) {
            Start-Sleep -Seconds 2
        }
    }

    return $null
}


$Resolved = Resolve-OnnWithRecovery


if (-not $Resolved) {
    Write-Host ""
    Write-Host "The paired ONN is not currently discoverable."
    Write-Host "On the ONN, toggle Wireless debugging Off, then On."
    Write-Host "Do not remove or recreate the pairing."
    Read-Host "After Wireless debugging is back On, press Enter to retry"

    for ($Attempt = 1; $Attempt -le 5; $Attempt++) {
        $Resolved = Resolve-OnnWithRecovery

        if ($Resolved) {
            break
        }

        if ($Attempt -lt 5) {
            Start-Sleep -Seconds 2
        }
    }
}


if (-not $Resolved) {
    throw @"
No online physical ONN ADB target could be recovered.

Leave the existing pairing intact, confirm Wireless debugging is On,
and rerun this command.
"@
}


$Onn = [string]$Resolved.Target
$TargetSource = [string]$Resolved.Source

$Model = (
    & $Adb -s $Onn shell getprop ro.product.model
).Trim()

if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($Model)) {
    throw "Recovered ADB target did not respond as a physical Android device."
}

Save-CachedAdbTarget $Onn

Write-Host "ADB target: physical ONN ($TargetSource)"
Write-Host "Model:      $Model"


Write-Host ""
Write-Host "[3/4] Installing PrivyHub..."

& $Adb -s $Onn install -r $Apk

if ($LASTEXITCODE -ne 0) {
    throw "ADB install failed with exit code $LASTEXITCODE"
}


Write-Host ""
Write-Host "[4/4] Launching PrivyHub..."

& $Adb -s $Onn shell am start -n "$Package/$Activity"

if ($LASTEXITCODE -ne 0) {
    throw "PrivyHub launch failed with exit code $LASTEXITCODE"
}


Write-Host ""
Write-Host "Done."
Write-Host "PrivyHub was built, installed, and launched on:"
Write-Host "  $Model"
Write-Host "  physical ONN"
Write-Host ""
