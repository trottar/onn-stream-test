param(
    [string]$Serial = ""
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$DownloadRoot = Join-Path $ProjectRoot "runtime\downloads\moonlight"
$Apk = Join-Path $DownloadRoot "moonlight-android-v12.1.apk"
$Url = "https://github.com/moonlight-stream/moonlight-android/releases/download/v12.1/app-nonRoot-release.apk"

New-Item -ItemType Directory -Force -Path $DownloadRoot | Out-Null

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

    $AndroidProject = Join-Path $ProjectRoot "PrivyHub"

    $LocalSdk = Resolve-LocalPropertiesSdk `
        (Join-Path $AndroidProject "local.properties")

    if ($LocalSdk) {
        $SdkRoots += $LocalSdk
    }

    if ($env:LOCALAPPDATA) {
        $SdkRoots += (
            Join-Path $env:LOCALAPPDATA "Android\Sdk"
        )
        $SdkRoots += (
            Join-Path $env:LOCALAPPDATA "Sdk"
        )
    }

    foreach ($SdkRoot in ($SdkRoots | Select-Object -Unique)) {
        if (-not $SdkRoot) {
            continue
        }

        $Candidate = Join-Path $SdkRoot "platform-tools\adb.exe"

        if (Test-Path $Candidate) {
            return (Resolve-Path $Candidate).Path
        }
    }

    throw @"
ADB could not be found.

This script now uses the same discovery sources as PrivyHub's
tools\build_install_onn.ps1:
- PATH
- ANDROID_SDK_ROOT / ANDROID_HOME
- PrivyHub\local.properties sdk.dir
- common LOCALAPPDATA SDK roots
"@
}

$Adb = Find-Adb
Write-Host "ADB: $Adb"

if (-not (Test-Path $Apk)) {
    Write-Host "Downloading official Moonlight Android v12.1 APK"
    Invoke-WebRequest `
        -Uri $Url `
        -OutFile $Apk `
        -UseBasicParsing
}

if (-not $Serial) {
    $DeviceLines = & $Adb devices

    $OnlineDevices = @(
        $DeviceLines |
        Select-Object -Skip 1 |
        ForEach-Object {
            $Line = $_.Trim()

            if ($Line -match '^(\S+)\s+device$') {
                $matches[1]
            }
        }
    )

    if ($OnlineDevices.Count -eq 0) {
        throw @"
No online ADB devices found.

Enable Wireless debugging on the onn and reconnect if needed.
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

        throw "Could not identify the physical onn automatically."
    }

    if ($OnnCandidates.Count -gt 1) {
        $MdnsCandidate = @(
            $OnnCandidates |
            Where-Object {
                $_ -match '^adb-.*\._adb-tls-connect\._tcp$'
            }
        ) | Select-Object -First 1

        if ($MdnsCandidate) {
            $Serial = $MdnsCandidate
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
        $Serial = $OnnCandidates[0]
    }
}

$Model = (
    & $Adb -s $Serial shell getprop ro.product.model
).Trim()

Write-Host "ADB target: $Serial"
Write-Host "Model:      $Model"
Write-Host ""
Write-Host "Installing Moonlight Android v12.1 on the selected onn target..."

& $Adb `
    -s $Serial `
    install `
    -r `
    $Apk

if ($LASTEXITCODE -ne 0) {
    throw "Moonlight APK installation failed with exit code $LASTEXITCODE"
}

$Hash = (
    Get-FileHash `
        -Algorithm SHA256 `
        -LiteralPath $Apk
).Hash.ToLowerInvariant()

Write-Host ""
Write-Host "Moonlight installed."
Write-Host "Package: com.limelight"
Write-Host "Downloaded APK SHA-256: $Hash"
Write-Host ""
Write-Host "PrivyHub will use Moonlight only as the temporary streaming transport."
