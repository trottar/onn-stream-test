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


$DeviceLines = & $Adb devices


$OnlineDevices = @(
    $DeviceLines |
    Select-Object -Skip 1 |
    ForEach-Object {
        $Line = $_.Trim()

        # PRIVYHUB_A7_PATCH_11_A7_4_SOFTPATCH_MODS_ADB_FIX
        # ADB mDNS instance names can contain spaces (for example a Windows
        # duplicate service suffix). Parse the tab before the status field.
        if ($Line -match '^(.*)\tdevice$') {
            $matches[1]
        }
    }
)


if ($OnlineDevices.Count -eq 0) {
    throw @"
No online ADB devices found.

Enable Wireless debugging on the ONN and reconnect if needed.
"@
}


$OnnCandidates = @(
    $OnlineDevices |
    Where-Object {
        $_ -ne "emulator-5554" -and
        (
            $_ -match '^adb-.*\._adb-tls-connect\._tcp$' -or
            $_ -match '^\d{1,3}(\.\d{1,3}){3}:\d+$'
        )
    }
)


if ($OnnCandidates.Count -eq 0) {
    Write-Host ""
    Write-Host "Online ADB devices:"

    $OnlineDevices |
        ForEach-Object {
            Write-Host "  $_"
        }

    throw "Could not identify the physical ONN automatically."
}


if ($OnnCandidates.Count -gt 1) {
    $MdnsCandidate = @(
        $OnnCandidates |
        Where-Object {
            $_ -match '^adb-.*\._adb-tls-connect\._tcp$'
        }
    ) | Select-Object -First 1


    if ($MdnsCandidate) {
        $Onn = $MdnsCandidate
    }
    else {
        Write-Host ""
        Write-Host "Multiple possible physical devices were found:"

        $OnnCandidates |
            ForEach-Object {
                Write-Host "  $_"
            }

        throw @"
More than one physical ADB target is online.
Disconnect the extra target and rerun this script.
"@
    }
}
else {
    $Onn = $OnnCandidates[0]
}


$Model = (
    & $Adb -s $Onn shell getprop ro.product.model
).Trim()


Write-Host "ADB target: $Onn"
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
Write-Host "  $Onn"
Write-Host ""
