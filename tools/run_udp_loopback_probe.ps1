param(
    [int]$DurationSeconds = 10,
    [int]$Port = 48121,
    [string]$Label = "A_android_loopback",
    [ValidateSet("default", "audio", "urgent_audio")]
    [string]$SenderPriority = "urgent_audio",
    [ValidateSet("default", "audio", "urgent_audio")]
    [string]$ReceiverPriority = "default"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$AndroidProject = Join-Path $ProjectRoot "PrivyHub"
$Package = "com.safeiot.privyhub"
$Activity = ".diagnostics.UdpLoopbackProbeActivity"

if ($DurationSeconds -lt 5 -or $DurationSeconds -gt 300) {
    throw "DurationSeconds must be between 5 and 300."
}
if ($Port -lt 1024 -or $Port -gt 65535) {
    throw "Port must be between 1024 and 65535."
}

function Resolve-LocalPropertiesSdk {
    param([string]$LocalPropertiesPath)
    if (-not (Test-Path $LocalPropertiesPath)) { return $null }
    $SdkLine = Get-Content $LocalPropertiesPath |
        Where-Object { $_ -match '^\s*sdk\.dir\s*=' } |
        Select-Object -First 1
    if (-not $SdkLine) { return $null }
    $SdkDir = ($SdkLine -split '=', 2)[1].Trim()
    $SdkDir = $SdkDir -replace '\\:', ':'
    $SdkDir = $SdkDir -replace '\\\\', '\'
    return $SdkDir
}

function Find-Adb {
    $Command = Get-Command adb.exe -ErrorAction SilentlyContinue
    if (-not $Command) { $Command = Get-Command adb -ErrorAction SilentlyContinue }
    if ($Command) { return $Command.Source }

    $SdkRoots = @()
    if ($env:ANDROID_SDK_ROOT) { $SdkRoots += $env:ANDROID_SDK_ROOT }
    if ($env:ANDROID_HOME) { $SdkRoots += $env:ANDROID_HOME }
    $LocalSdk = Resolve-LocalPropertiesSdk (Join-Path $AndroidProject "local.properties")
    if ($LocalSdk) { $SdkRoots += $LocalSdk }

    foreach ($SdkRoot in ($SdkRoots | Select-Object -Unique)) {
        $Candidate = Join-Path $SdkRoot "platform-tools\adb.exe"
        if (Test-Path $Candidate) { return $Candidate }
    }
    throw "ADB could not be found."
}

function Find-OnnTarget {
    param([string]$Adb)
    $DeviceLines = & $Adb devices
    $OnlineDevices = @(
        $DeviceLines |
            Select-Object -Skip 1 |
            ForEach-Object {
                $Line = $_.Trim()
                if ($Line -match '^(\S+)\s+device$') { $matches[1] }
            }
    )
    $Candidates = @(
        $OnlineDevices |
            Where-Object {
                $_ -ne "emulator-5554" -and
                ($_ -match '^adb-.*\._adb-tls-connect\._tcp$' -or $_ -match '^\d{1,3}(\.\d{1,3}){3}:\d+$')
            }
    )
    if ($Candidates.Count -eq 0) { throw "No physical ONN ADB target is online." }
    if ($Candidates.Count -eq 1) { return $Candidates[0] }
    $Mdns = @($Candidates | Where-Object { $_ -match '^adb-.*\._adb-tls-connect\._tcp$' }) | Select-Object -First 1
    if ($Mdns) { return $Mdns }
    throw "Multiple physical ADB targets are online; disconnect the extra target and rerun."
}

function Test-RunAsFile {
    param([string]$Adb, [string]$Device, [string]$RemotePath)
    & $Adb -s $Device shell run-as $Package ls $RemotePath 1>$null 2>$null
    return ($LASTEXITCODE -eq 0)
}

function Wait-RunAsFile {
    param([string]$Adb, [string]$Device, [string]$RemotePath, [int]$TimeoutSeconds = 5)
    $Deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    do {
        if (Test-RunAsFile -Adb $Adb -Device $Device -RemotePath $RemotePath) { return $true }
        Start-Sleep -Milliseconds 250
    } while ([DateTime]::UtcNow -lt $Deadline)
    return $false
}

function Save-RunAsTextFile {
    param([string]$Adb, [string]$Device, [string]$RemotePath, [string]$LocalPath)
    if (-not (Test-RunAsFile -Adb $Adb -Device $Device -RemotePath $RemotePath)) {
        throw "Android loopback probe file does not exist: $RemotePath"
    }
    $Output = & $Adb -s $Device exec-out run-as $Package cat $RemotePath 2>&1
    $Joined = $Output -join "`n"
    if ($LASTEXITCODE -ne 0 -or $Joined -match '^cat: .*No such file' -or $Joined -match '^run-as:') {
        throw "Could not retrieve Android loopback probe file: $RemotePath`n$Joined"
    }
    $Output | Out-File -FilePath $LocalPath -Encoding utf8
}

function Capture-AndroidDiagnostics {
    param([string]$Adb, [string]$Device, [string]$SessionDir)
    (& $Adb -s $Device logcat -d -v threadtime 2>&1) |
        Out-File -FilePath (Join-Path $SessionDir "android_logcat.txt") -Encoding utf8
    (& $Adb -s $Device shell dumpsys activity activities 2>&1) |
        Out-File -FilePath (Join-Path $SessionDir "android_activity_state.txt") -Encoding utf8
}

$Adb = Find-Adb
$Onn = Find-OnnTarget -Adb $Adb
$SafeLabel = ($Label -replace '[^A-Za-z0-9_.-]+', '_')
if ([string]::IsNullOrWhiteSpace($SafeLabel)) { $SafeLabel = "A_android_loopback" }
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$SessionDir = Join-Path $ProjectRoot "logs\transport_loopback\${SafeLabel}_${Stamp}"
New-Item -ItemType Directory -Force -Path $SessionDir | Out-Null

Write-Host ""
Write-Host "PrivyHub Android-local UDP loopback probe"
Write-Host "Label:             $SafeLabel"
Write-Host "Duration:          $DurationSeconds s"
Write-Host "Packet interval:   5 ms"
Write-Host "Synthetic payload: 960 bytes"
Write-Host "Packet bytes:      1000"
Write-Host "Destination:       127.0.0.1:$Port"
Write-Host "Sender priority:   $SenderPriority"
Write-Host "Receiver priority: $ReceiverPriority"
Write-Host ""
Write-Host "This run bypasses Windows, Wi-Fi, GL-iNet, and the physical LAN path."
Write-Host ""

$SdkLevel = [int]((& $Adb -s $Onn shell getprop ro.build.version.sdk).Trim())
if ($SdkLevel -lt 31) { throw "Android-local kernel timestamp probe requires API 31+. Device reports API $SdkLevel." }

& $Adb -s $Onn shell run-as $Package rm -f `
    files/transport_loopback/latest_sender.csv `
    files/transport_loopback/latest_packets.csv `
    files/transport_loopback/latest_summary.json 2>$null | Out-Null
& $Adb -s $Onn logcat -c 2>$null | Out-Null

$LaunchOutput = & $Adb -s $Onn shell am start -n "$Package/$Activity" `
    --ei udp_port $Port `
    --ei duration_seconds $DurationSeconds `
    --es label $SafeLabel `
    --es sender_priority $SenderPriority `
    --es receiver_priority $ReceiverPriority

if ($LASTEXITCODE -ne 0 -or ($LaunchOutput -join "`n") -match 'Error type|Activity class.*does not exist|Permission Denial') {
    throw "Could not launch UdpLoopbackProbeActivity. Rebuild/install PrivyHub after applying v0.3.0."
}

Start-Sleep -Seconds ($DurationSeconds + 2)
Capture-AndroidDiagnostics -Adb $Adb -Device $Onn -SessionDir $SessionDir

$RemoteSummary = "files/transport_loopback/latest_summary.json"
$RemoteSender = "files/transport_loopback/latest_sender.csv"
$RemotePackets = "files/transport_loopback/latest_packets.csv"

if (-not (Wait-RunAsFile -Adb $Adb -Device $Onn -RemotePath $RemoteSummary -TimeoutSeconds 5)) {
    throw @"
Android loopback probe summary was not written.
Inspect:
  $(Join-Path $SessionDir "android_logcat.txt")
  $(Join-Path $SessionDir "android_activity_state.txt")
"@
}

$LocalSummary = Join-Path $SessionDir "loopback_summary.json"
Save-RunAsTextFile -Adb $Adb -Device $Onn -RemotePath $RemoteSummary -LocalPath $LocalSummary

$SummaryText = Get-Content -Raw $LocalSummary
try { $SummaryJson = $SummaryText | ConvertFrom-Json } catch { throw "Loopback summary is not valid JSON: $LocalSummary" }
if ($null -ne $SummaryJson.error) {
    throw @"
Android loopback diagnostic reported a runtime failure:
$($SummaryJson.error)

Inspect:
  $LocalSummary
  $(Join-Path $SessionDir "android_logcat.txt")
"@
}

if (-not (Wait-RunAsFile -Adb $Adb -Device $Onn -RemotePath $RemoteSender -TimeoutSeconds 2)) {
    throw "Loopback summary exists but sender CSV was not written."
}
if (-not (Wait-RunAsFile -Adb $Adb -Device $Onn -RemotePath $RemotePackets -TimeoutSeconds 2)) {
    throw "Loopback summary exists but packet CSV was not written."
}

Save-RunAsTextFile -Adb $Adb -Device $Onn -RemotePath $RemoteSender -LocalPath (Join-Path $SessionDir "loopback_sender.csv")
Save-RunAsTextFile -Adb $Adb -Device $Onn -RemotePath $RemotePackets -LocalPath (Join-Path $SessionDir "loopback_packets.csv")

$Stats = $SummaryJson.stats
$Text = @"
PrivyHub Android-local UDP loopback summary

Sender successes/errors: $($Stats.sender_successes) / $($Stats.sender_errors)
Unique arrivals: $($Stats.unique_packets)
Missing: $($Stats.missing_packets)
Duplicates: $($Stats.duplicate_packets)
Kernel timestamp missing: $($SummaryJson.kernel_timestamp_missing_packets)

Sender interval avg/max ms: $($Stats.sender_intervals.avg_ms) / $($Stats.sender_intervals.max_ms)
Kernel interval avg/max ms: $($Stats.kernel_arrival_intervals.avg_ms) / $($Stats.kernel_arrival_intervals.max_ms)
App interval avg/max ms: $($Stats.app_arrival_intervals.avg_ms) / $($Stats.app_arrival_intervals.max_ms)

Sender 4-6 ms -> kernel <2 ms: $($Stats.sender_4_to_6_ms_but_kernel_lt_2_ms)
Sender 4-6 ms -> kernel >=20 ms: $($Stats.sender_4_to_6_ms_but_kernel_ge_20_ms)
Kernel-minus-sender interval abs p95/p99/max ms: $($Stats.kernel_minus_sender_interval_ms.abs_p95_ms) / $($Stats.kernel_minus_sender_interval_ms.abs_p99_ms) / $($Stats.kernel_minus_sender_interval_ms.max_abs_ms)
App-minus-kernel interval abs p95/p99/max ms: $($Stats.app_minus_kernel_interval_ms.abs_p95_ms) / $($Stats.app_minus_kernel_interval_ms.abs_p99_ms) / $($Stats.app_minus_kernel_interval_ms.max_abs_ms)
"@
$Text | Out-File -FilePath (Join-Path $SessionDir "loopback_summary.txt") -Encoding utf8
Write-Host $Text
Write-Host "Probe logs: $SessionDir"
