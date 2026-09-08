param(
    [Parameter(Mandatory = $true)]
    [string]$OnnIp,

    [int]$DurationSeconds = 60,
    [int]$Port = 48120,
    [string]$Label = "A_idle",
    [ValidateSet("default", "audio", "urgent_audio")]
    [string]$ReceiverPriority = "default",
    [ValidateSet("datagram", "kernel_timestamp")]
    [string]$ReceiveMode = "kernel_timestamp",
    [ValidateSet("none", "low_latency")]
    [string]$WifiLockMode = "none",
    [int]$SendBufferBytes = 0,
    [switch]$PktMonCapture,
    [ValidateSet("all", "nics")]
    [string]$PktMonComponents = "all"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ProbeScript = Join-Path $ProjectRoot "companion\diagnostics\udp_transport_probe.py"
$AndroidProject = Join-Path $ProjectRoot "PrivyHub"
$Package = "com.safeiot.privyhub"
$Activity = ".diagnostics.UdpTransportProbeActivity"

if ($OnnIp -eq "ONN_IP" -or [string]::IsNullOrWhiteSpace($OnnIp)) {
    throw "Replace ONN_IP locally when invoking the probe. Do not share it with ChatGPT."
}

if ($DurationSeconds -lt 5 -or $DurationSeconds -gt 3600) {
    throw "DurationSeconds must be between 5 and 3600."
}

if ($Port -lt 1024 -or $Port -gt 65535) {
    throw "Port must be between 1024 and 65535."
}

if (-not (Test-Path $ProbeScript)) {
    throw "Probe script not found: $ProbeScript"
}

function Resolve-LocalPropertiesSdk {
    param([string]$LocalPropertiesPath)

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
    $SdkDir = $SdkDir -replace '\\:', ':'
    $SdkDir = $SdkDir -replace '\\\\', '\'
    return $SdkDir
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
    if ($env:ANDROID_SDK_ROOT) { $SdkRoots += $env:ANDROID_SDK_ROOT }
    if ($env:ANDROID_HOME) { $SdkRoots += $env:ANDROID_HOME }

    $LocalSdk = Resolve-LocalPropertiesSdk (Join-Path $AndroidProject "local.properties")
    if ($LocalSdk) { $SdkRoots += $LocalSdk }

    foreach ($SdkRoot in ($SdkRoots | Select-Object -Unique)) {
        $Candidate = Join-Path $SdkRoot "platform-tools\adb.exe"
        if (Test-Path $Candidate) {
            return $Candidate
        }
    }

    throw "ADB could not be found."
}

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

function Find-PktMon {
    $Command = Get-Command pktmon.exe -ErrorAction SilentlyContinue
    if (-not $Command) {
        $Command = Get-Command pktmon -ErrorAction SilentlyContinue
    }
    if (-not $Command) {
        throw "PktMon could not be found."
    }
    return $Command.Source
}

function Test-IsAdministrator {
    $Identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $Principal = New-Object Security.Principal.WindowsPrincipal($Identity)
    return $Principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Find-OnnTarget {
    param([string]$Adb)

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

    $Candidates = @(
        $OnlineDevices |
            Where-Object {
                $_ -ne "emulator-5554" -and
                (
                    $_ -match '^adb-.*\._adb-tls-connect\._tcp$' -or
                    $_ -match '^\d{1,3}(\.\d{1,3}){3}:\d+$'
                )
            }
    )

    if ($Candidates.Count -eq 0) {
        throw "No physical ONN ADB target is online."
    }

    if ($Candidates.Count -eq 1) {
        return $Candidates[0]
    }

    $Mdns = @($Candidates | Where-Object { $_ -match '^adb-.*\._adb-tls-connect\._tcp$' }) |
        Select-Object -First 1

    if ($Mdns) {
        return $Mdns
    }

    throw "Multiple physical ADB targets are online; disconnect the extra target and rerun."
}

function Invoke-NativeQuietExitCode {
    param(
        [string]$FilePath,
        [string[]]$Arguments
    )

    # Do not invoke expected-failure probes through PowerShell's native-command
    # error pipeline. Newer PowerShell versions can promote a non-zero native
    # exit code to a terminating error when ErrorActionPreference is Stop,
    # even when stderr is redirected. A tiny ProcessStartInfo wrapper gives us
    # the native exit code directly and keeps expected "not ready yet" checks
    # out of PowerShell's error stream.
    $Psi = New-Object System.Diagnostics.ProcessStartInfo
    $Psi.FileName = $FilePath
    $Psi.UseShellExecute = $false
    $Psi.CreateNoWindow = $true
    $Psi.RedirectStandardOutput = $true
    $Psi.RedirectStandardError = $true
    $Psi.Arguments = ($Arguments -join " ")

    $Process = New-Object System.Diagnostics.Process
    $Process.StartInfo = $Psi

    try {
        [void]$Process.Start()
        [void]$Process.StandardOutput.ReadToEnd()
        [void]$Process.StandardError.ReadToEnd()
        $Process.WaitForExit()
        return [int]$Process.ExitCode
    }
    finally {
        $Process.Dispose()
    }
}

function Start-PktMonProbeCapture {
    param(
        [string]$PktMon,
        [string]$SessionDir,
        [int]$UdpPort,
        [string]$Components
    )

    if (-not (Test-IsAdministrator)) {
        throw "-PktMonCapture requires an Administrator PowerShell session."
    }

    $EtlPath = Join-Path $SessionDir "pktmon.etl"

    # Clean stale Packet Monitor state. A non-zero stop simply means there was
    # no active capture and is intentionally ignored.
    [void](Invoke-NativeQuietExitCode -FilePath $PktMon -Arguments @("stop"))

    $ExitCode = Invoke-NativeQuietExitCode -FilePath $PktMon -Arguments @("filter", "remove")
    if ($ExitCode -ne 0) {
        throw "PktMon could not remove previous filters (exit $ExitCode)."
    }

    $ExitCode = Invoke-NativeQuietExitCode -FilePath $PktMon -Arguments @(
        "filter", "add", "PrivyHubUDP", "-t", "UDP", "-p", "$UdpPort"
    )
    if ($ExitCode -ne 0) {
        throw "PktMon could not install the PrivyHub UDP filter (exit $ExitCode)."
    }

    $ExitCode = Invoke-NativeQuietExitCode -FilePath $PktMon -Arguments @(
        "start", "--capture", "--comp", $Components, "--pkt-size", "128", "--file-name", $EtlPath
    )
    if ($ExitCode -ne 0) {
        [void](Invoke-NativeQuietExitCode -FilePath $PktMon -Arguments @("filter", "remove"))
        throw "PktMon could not start capture (exit $ExitCode)."
    }

    return $EtlPath
}

function Stop-And-ExportPktMonProbeCapture {
    param(
        [string]$PktMon,
        [string]$SessionDir,
        [string]$EtlPath
    )

    $StopExit = Invoke-NativeQuietExitCode -FilePath $PktMon -Arguments @("stop")
    [void](Invoke-NativeQuietExitCode -FilePath $PktMon -Arguments @("filter", "remove"))

    if ($StopExit -ne 0) {
        throw "PktMon stop failed with exit code $StopExit."
    }
    if (-not (Test-Path $EtlPath)) {
        throw "PktMon did not create its ETL file: $EtlPath"
    }

    $Etl = Get-Item $EtlPath
    if ($Etl.Length -le 0) {
        throw "PktMon ETL is empty: $EtlPath"
    }

    $FullTxt = Join-Path $SessionDir "pktmon_full.txt"
    $StatsTxt = Join-Path $SessionDir "pktmon_stats.txt"

    $ExitCode = Invoke-NativeQuietExitCode -FilePath $PktMon -Arguments @(
        "etl2txt", $EtlPath, "--out", $FullTxt, "--verbose", "2"
    )
    if ($ExitCode -ne 0) {
        throw "PktMon full-text export failed with exit code $ExitCode."
    }

    # On some Windows/PktMon builds --stats-only writes its report to the
    # process output stream even when --out is supplied. Capture stdout/stderr
    # explicitly and persist that text ourselves instead of assuming --out
    # created a populated file.
    $StatsPsi = New-Object System.Diagnostics.ProcessStartInfo
    $StatsPsi.FileName = $PktMon
    $StatsPsi.UseShellExecute = $false
    $StatsPsi.CreateNoWindow = $true
    $StatsPsi.RedirectStandardOutput = $true
    $StatsPsi.RedirectStandardError = $true
    $StatsPsi.Arguments = "etl2txt `"$EtlPath`" --stats-only"

    $StatsProcess = New-Object System.Diagnostics.Process
    $StatsProcess.StartInfo = $StatsPsi
    try {
        [void]$StatsProcess.Start()
        $StatsStdout = $StatsProcess.StandardOutput.ReadToEnd()
        $StatsStderr = $StatsProcess.StandardError.ReadToEnd()
        $StatsProcess.WaitForExit()
        $StatsExit = [int]$StatsProcess.ExitCode
    }
    finally {
        $StatsProcess.Dispose()
    }

    if ($StatsExit -ne 0) {
        throw "PktMon stats export failed with exit code $StatsExit. $StatsStderr"
    }

    $StatsText = $StatsStdout
    if (-not [string]::IsNullOrWhiteSpace($StatsStderr)) {
        if (-not [string]::IsNullOrWhiteSpace($StatsText)) {
            $StatsText += "`r`n"
        }
        $StatsText += $StatsStderr
    }
    if ([string]::IsNullOrWhiteSpace($StatsText)) {
        $StatsText = "PktMon --stats-only returned no printable statistics on this Windows build. The verbose packet capture remains valid."
    }
    [System.IO.File]::WriteAllText($StatsTxt, $StatsText, [System.Text.Encoding]::UTF8)

    if (-not (Test-Path $FullTxt) -or (Get-Item $FullTxt).Length -le 4) {
        throw "PktMon captured no printable packet records. Inspect $EtlPath and rerun with -PktMonComponents all if needed."
    }
    if (-not (Test-Path $StatsTxt) -or (Get-Item $StatsTxt).Length -le 4) {
        throw "PktMon stats text could not be persisted: $StatsTxt"
    }

    return [PSCustomObject]@{
        Etl = $EtlPath
        FullText = $FullTxt
        Stats = $StatsTxt
    }
}

function Test-RunAsFile {
    param(
        [string]$Adb,
        [string]$Device,
        [string]$RemotePath
    )

    # The summary does not exist while the receiver is still finishing. That is
    # a normal polling state, not an error. Query it outside PowerShell's native
    # error pipeline so a non-zero `ls` result simply returns $false.
    $ExitCode = Invoke-NativeQuietExitCode `
        -FilePath $Adb `
        -Arguments @("-s", $Device, "shell", "run-as", $Package, "ls", $RemotePath)

    return ($ExitCode -eq 0)
}

function Wait-RunAsFile {
    param(
        [string]$Adb,
        [string]$Device,
        [string]$RemotePath,
        [int]$TimeoutSeconds = 5
    )

    $Deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    do {
        if (Test-RunAsFile -Adb $Adb -Device $Device -RemotePath $RemotePath) {
            return $true
        }
        Start-Sleep -Milliseconds 250
    } while ([DateTime]::UtcNow -lt $Deadline)

    return $false
}

function Save-RunAsTextFile {
    param(
        [string]$Adb,
        [string]$Device,
        [string]$RemotePath,
        [string]$LocalPath
    )

    if (-not (Test-RunAsFile -Adb $Adb -Device $Device -RemotePath $RemotePath)) {
        throw "Android probe file does not exist: $RemotePath"
    }

    $Output = & $Adb -s $Device exec-out run-as $Package cat $RemotePath 2>&1
    $Joined = $Output -join "`n"
    if ($LASTEXITCODE -ne 0 -or $Joined -match '^cat: .*No such file' -or $Joined -match '^run-as:') {
        throw "Could not retrieve Android probe file: $RemotePath`n$Joined"
    }
    $Output | Out-File -FilePath $LocalPath -Encoding utf8
}

function Capture-AndroidDiagnostics {
    param(
        [string]$Adb,
        [string]$Device,
        [string]$SessionDir
    )

    $LogcatPath = Join-Path $SessionDir "android_logcat.txt"
    $ActivityPath = Join-Path $SessionDir "android_activity_state.txt"

    (& $Adb -s $Device logcat -d -v threadtime 2>&1) |
        Out-File -FilePath $LogcatPath -Encoding utf8

    (& $Adb -s $Device shell dumpsys activity activities 2>&1) |
        Out-File -FilePath $ActivityPath -Encoding utf8
}

$Adb = Find-Adb
$Python = Find-Python
$Onn = Find-OnnTarget -Adb $Adb
$PktMon = $null
if ($PktMonCapture) {
    $PktMon = Find-PktMon
}

$SafeLabel = ($Label -replace '[^A-Za-z0-9_.-]+', '_')
if ([string]::IsNullOrWhiteSpace($SafeLabel)) { $SafeLabel = "probe" }
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$SessionDir = Join-Path $ProjectRoot "logs\transport_probe\${SafeLabel}_${Stamp}"
New-Item -ItemType Directory -Force -Path $SessionDir | Out-Null

Write-Host ""
Write-Host "PrivyHub standalone UDP transport probe"
Write-Host "Label:             $SafeLabel"
Write-Host "Duration:          $DurationSeconds s"
Write-Host "Packet interval:   5 ms"
Write-Host "Synthetic payload: 960 bytes"
Write-Host "UDP port:          $Port"
Write-Host "Receiver priority: $ReceiverPriority"
Write-Host "Receive mode:       $ReceiveMode"
Write-Host "Wi-Fi lock mode:    $WifiLockMode"
Write-Host "PktMon capture:      $([bool]$PktMonCapture)"
if ($PktMonCapture) {
    Write-Host "PktMon components:   $PktMonComponents"
}
Write-Host ""

$PktMonStarted = $false
$PktMonEtl = $null
$PktMonExportError = $null
$PktMonExport = $null

try {
    if ($PktMonCapture) {
        $PktMonEtl = Start-PktMonProbeCapture `
            -PktMon $PktMon `
            -SessionDir $SessionDir `
            -UdpPort $Port `
            -Components $PktMonComponents
        $PktMonStarted = $true
        Write-Host "PktMon ETL:          $PktMonEtl"
        Write-Host ""
    }

    # Remove only prior probe outputs inside the app sandbox; game/media diagnostics are untouched here.
    & $Adb -s $Onn shell run-as $Package rm -f files/transport_probe/latest_packets.csv files/transport_probe/latest_summary.json 2>$null | Out-Null

    # Clear Android logcat so any runtime failure from this diagnostic run is unambiguous.
    & $Adb -s $Onn logcat -c 2>$null | Out-Null

    $SdkLevel = [int]((& $Adb -s $Onn shell getprop ro.build.version.sdk).Trim())
    if ($ReceiveMode -eq "kernel_timestamp" -and $SdkLevel -lt 31) {
        throw "kernel_timestamp receive mode requires Android API 31+. Device reports API $SdkLevel."
    }

    $ReceiverDuration = $DurationSeconds + 3
    $LaunchOutput = & $Adb -s $Onn shell am start -n "$Package/$Activity" `
        --ei udp_port $Port `
        --ei duration_seconds $ReceiverDuration `
        --es label $SafeLabel `
        --es receiver_priority $ReceiverPriority `
        --es receive_mode $ReceiveMode `
        --es wifi_lock_mode $WifiLockMode

    if ($LASTEXITCODE -ne 0 -or ($LaunchOutput -join "`n") -match 'Error type|Activity class.*does not exist|Permission Denial') {
        throw "Could not launch the diagnostic Activity. Rebuild/install PrivyHub after applying the patch."
    }

    Start-Sleep -Milliseconds 750

    $SendArgs = @(
        $ProbeScript,
        "send",
        "--target", $OnnIp,
        "--port", $Port,
        "--duration-seconds", $DurationSeconds,
        "--interval-ms", "5",
        "--send-buffer-bytes", $SendBufferBytes,
        "--output-dir", $SessionDir
    )

    & $Python @SendArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Host probe sender failed with exit code $LASTEXITCODE"
    }

    # Receiver runs three seconds longer than the sender so its final summary is written after the last datagram.
    Start-Sleep -Seconds 3

    # Always capture Android diagnostics before retrieving app-private output. If the Activity
    # crashed or exited without writing a summary, these files contain the actual failure.
    Capture-AndroidDiagnostics -Adb $Adb -Device $Onn -SessionDir $SessionDir

    $RemotePackets = "files/transport_probe/latest_packets.csv"
    $RemoteSummary = "files/transport_probe/latest_summary.json"
    $AndroidPackets = Join-Path $SessionDir "android_packets.csv"
    $AndroidSummary = Join-Path $SessionDir "android_summary.json"

    if (-not (Wait-RunAsFile -Adb $Adb -Device $Onn -RemotePath $RemoteSummary -TimeoutSeconds 5)) {
        throw ("Android probe summary was not written.`n" +
            "No comparison was generated because that would incorrectly classify every host send as lost.`n" +
            "Inspect:`n  $(Join-Path $SessionDir 'android_logcat.txt')`n  $(Join-Path $SessionDir 'android_activity_state.txt')")
    }

    Save-RunAsTextFile -Adb $Adb -Device $Onn -RemotePath $RemoteSummary -LocalPath $AndroidSummary

    $SummaryText = Get-Content -Raw $AndroidSummary
    try {
        $SummaryJson = $SummaryText | ConvertFrom-Json
    } catch {
        throw "Android summary is not valid JSON: $AndroidSummary"
    }

    if ($null -ne $SummaryJson.error) {
        throw ("Android diagnostic Activity reported a runtime failure:`n$($SummaryJson.error)`n`n" +
            "Inspect:`n  $AndroidSummary`n  $(Join-Path $SessionDir 'android_logcat.txt')")
    }

    if ($WifiLockMode -eq "low_latency" -and -not [bool]$SummaryJson.wifi_lock_acquired) {
        throw "Android diagnostic completed without holding the requested low-latency Wi-Fi lock: $AndroidSummary"
    }

    if (-not (Wait-RunAsFile -Adb $Adb -Device $Onn -RemotePath $RemotePackets -TimeoutSeconds 2)) {
        throw "Android probe summary exists but packet CSV was not written: $RemotePackets"
    }
    Save-RunAsTextFile -Adb $Adb -Device $Onn -RemotePath $RemotePackets -LocalPath $AndroidPackets

    & $Python $ProbeScript compare `
        --host-csv (Join-Path $SessionDir "host_packets.csv") `
        --android-csv $AndroidPackets `
        --output-dir $SessionDir

    if ($LASTEXITCODE -ne 0) {
        throw "Probe comparison failed with exit code $LASTEXITCODE"
    }

    Write-Host ""
    Write-Host "Probe logs: $SessionDir"
    Write-Host "Use combined_summary.txt for the host/app/kernel timing comparison."

}
finally {
    if ($PktMonStarted) {
        try {
            $PktMonExport = Stop-And-ExportPktMonProbeCapture `
                -PktMon $PktMon `
                -SessionDir $SessionDir `
                -EtlPath $PktMonEtl
        }
        catch {
            $PktMonExportError = $_
        }
    }
}

if ($null -ne $PktMonExportError) {
    throw "PktMon capture/export failed after the UDP probe: $($PktMonExportError.Exception.Message)"
}

if ($null -ne $PktMonExport) {
    Write-Host "PktMon full text: $($PktMonExport.FullText)"
    Write-Host "PktMon stats:     $($PktMonExport.Stats)"
}
