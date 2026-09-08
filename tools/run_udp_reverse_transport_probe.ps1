param(
    [Parameter(Mandatory = $true)]
    [string]$PcIp,

    [int]$DurationSeconds = 20,
    [int]$Port = 48102,
    [string]$Label = "B_reverse_idle",
    [ValidateSet("default", "audio", "urgent_audio")]
    [string]$SenderPriority = "urgent_audio",
    [int]$ReceiveBufferBytes = 1048576,
    [switch]$PktMonCapture,
    [ValidateSet("all", "nics")]
    [string]$PktMonComponents = "all"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ReverseScript = Join-Path $ProjectRoot "companion\diagnostics\udp_reverse_transport_probe.py"
$AndroidProject = Join-Path $ProjectRoot "PrivyHub"
$Package = "com.safeiot.privyhub"
$Activity = ".diagnostics.UdpReverseTransportProbeActivity"

if ($PcIp -eq "PC_IP" -or [string]::IsNullOrWhiteSpace($PcIp)) {
    throw "Replace PC_IP locally when invoking the probe. Do not share it with ChatGPT."
}
if ($DurationSeconds -lt 5 -or $DurationSeconds -gt 300) {
    throw "DurationSeconds must be between 5 and 300."
}
if ($Port -lt 1024 -or $Port -gt 65535) {
    throw "Port must be between 1024 and 65535."
}
if (-not (Test-Path $ReverseScript)) {
    throw "Reverse probe script not found: $ReverseScript"
}

# The reverse target must be an IPv4 address assigned to this Windows host.
# Validate that locally without printing or persisting the supplied address.
try {
    $ParsedPcIp = [System.Net.IPAddress]::Parse($PcIp)
} catch {
    throw "PcIp must be a local IPv4 address assigned to this Windows PC."
}
if ($ParsedPcIp.AddressFamily -ne [System.Net.Sockets.AddressFamily]::InterNetwork) {
    throw "PcIp must be a local IPv4 address assigned to this Windows PC."
}
try {
    $LocalIpv4 = @(Get-NetIPAddress -AddressFamily IPv4 -ErrorAction Stop | Select-Object -ExpandProperty IPAddress)
    $PcIpIsLocal = ($LocalIpv4 -contains $PcIp)
} catch {
    throw "Could not validate the supplied PC target address against local Windows adapters."
}
if (-not $PcIpIsLocal) {
    throw "The supplied PC target address is not assigned to this Windows PC. Use the IPv4 address of the PC adapter reachable from the onn; the address is checked locally and is not logged."
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

function Find-Python {
    $Command = Get-Command python.exe -ErrorAction SilentlyContinue
    if (-not $Command) { $Command = Get-Command python -ErrorAction SilentlyContinue }
    if (-not $Command) { throw "Python could not be found." }
    return $Command.Source
}


function Find-PktMon {
    $Command = Get-Command pktmon.exe -ErrorAction SilentlyContinue
    if (-not $Command) { $Command = Get-Command pktmon -ErrorAction SilentlyContinue }
    if (-not $Command) { throw "PktMon could not be found." }
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

function Invoke-NativeQuietExitCode {
    param([string]$FilePath, [string[]]$Arguments)
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
    finally { $Process.Dispose() }
}


function Start-PktMonReverseCapture {
    param([string]$PktMon, [string]$SessionDir, [int]$UdpPort, [string]$Components)
    if (-not (Test-IsAdministrator)) {
        throw "-PktMonCapture requires an Administrator PowerShell session."
    }
    $EtlPath = Join-Path $SessionDir "pktmon.etl"
    [void](Invoke-NativeQuietExitCode -FilePath $PktMon -Arguments @("stop"))
    $ExitCode = Invoke-NativeQuietExitCode -FilePath $PktMon -Arguments @("filter", "remove")
    if ($ExitCode -ne 0) { throw "PktMon could not remove previous filters (exit $ExitCode)." }
    $ExitCode = Invoke-NativeQuietExitCode -FilePath $PktMon -Arguments @(
        "filter", "add", "PrivyHubReverseUDP", "-t", "UDP", "-p", "$UdpPort"
    )
    if ($ExitCode -ne 0) { throw "PktMon could not install the reverse UDP filter (exit $ExitCode)." }
    $ExitCode = Invoke-NativeQuietExitCode -FilePath $PktMon -Arguments @(
        "start", "--capture", "--comp", $Components, "--pkt-size", "128", "--file-name", $EtlPath
    )
    if ($ExitCode -ne 0) {
        [void](Invoke-NativeQuietExitCode -FilePath $PktMon -Arguments @("filter", "remove"))
        throw "PktMon could not start reverse capture (exit $ExitCode)."
    }
    return $EtlPath
}

function Stop-And-SummarizePktMonReverseCapture {
    param(
        [string]$PktMon,
        [string]$Python,
        [string]$ReverseScript,
        [string]$SessionDir,
        [string]$EtlPath
    )
    $StopExit = Invoke-NativeQuietExitCode -FilePath $PktMon -Arguments @("stop")
    [void](Invoke-NativeQuietExitCode -FilePath $PktMon -Arguments @("filter", "remove"))
    if ($StopExit -ne 0) { throw "PktMon stop failed with exit code $StopExit." }
    if (-not (Test-Path $EtlPath) -or (Get-Item $EtlPath).Length -le 0) {
        throw "PktMon did not create a usable ETL capture."
    }

    $FullTxt = Join-Path $SessionDir "pktmon_full.txt"
    $ExitCode = Invoke-NativeQuietExitCode -FilePath $PktMon -Arguments @(
        "etl2txt", $EtlPath, "--out", $FullTxt, "--verbose", "2"
    )
    if ($ExitCode -ne 0) { throw "PktMon full-text export failed with exit code $ExitCode." }
    if (-not (Test-Path $FullTxt)) {
        throw "PktMon full-text export did not create the expected output file."
    }

    & $Python $ReverseScript pktmon-presence `
        --input $FullTxt `
        --output-dir $SessionDir
    if ($LASTEXITCODE -ne 0) {
        throw "PktMon privacy-safe presence summarizer failed with exit code $LASTEXITCODE."
    }

    $SummaryJson = Join-Path $SessionDir "pktmon_presence_summary.json"
    $SummaryText = Join-Path $SessionDir "pktmon_presence_summary.txt"
    if (-not (Test-Path $SummaryJson) -or -not (Test-Path $SummaryText)) {
        throw "PktMon presence summarizer did not create its expected summary files."
    }

    return [PSCustomObject]@{
        Etl = $EtlPath
        FullText = $FullTxt
        SummaryJson = $SummaryJson
        SummaryText = $SummaryText
    }
}

function Test-RunAsFile {
    param([string]$Adb, [string]$Device, [string]$RemotePath)
    $ExitCode = Invoke-NativeQuietExitCode -FilePath $Adb -Arguments @(
        "-s", $Device, "shell", "run-as", $Package, "ls", $RemotePath
    )
    return ($ExitCode -eq 0)
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
        throw "Android reverse-probe file does not exist: $RemotePath"
    }
    $Output = & $Adb -s $Device exec-out run-as $Package cat $RemotePath 2>&1
    $Joined = $Output -join "`n"
    if ($LASTEXITCODE -ne 0 -or $Joined -match '^cat: .*No such file' -or $Joined -match '^run-as:') {
        throw "Could not retrieve Android reverse-probe file: $RemotePath`n$Joined"
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
$Python = Find-Python
$Onn = Find-OnnTarget -Adb $Adb
$PktMon = $null
if ($PktMonCapture) { $PktMon = Find-PktMon }

$SafeLabel = ($Label -replace '[^A-Za-z0-9_.-]+', '_')
if ([string]::IsNullOrWhiteSpace($SafeLabel)) { $SafeLabel = "reverse_probe" }
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$SessionDir = Join-Path $ProjectRoot "logs\transport_reverse\${SafeLabel}_${Stamp}"
New-Item -ItemType Directory -Force -Path $SessionDir | Out-Null

Write-Host ""
Write-Host "PrivyHub reverse UDP transport probe"
Write-Host "Direction:          Android -> Windows"
Write-Host "Label:              $SafeLabel"
Write-Host "Duration:           $DurationSeconds s"
Write-Host "Packet interval:    5 ms"
Write-Host "Synthetic payload:  960 bytes"
Write-Host "UDP port:           $Port"
Write-Host "Android priority:   $SenderPriority"
Write-Host "PC target address:  supplied locally (not logged)"
Write-Host "PktMon capture:      $([bool]$PktMonCapture)"
if ($PktMonCapture) { Write-Host "PktMon components:   $PktMonComponents" }
Write-Host ""

$PktMonStarted = $false
$PktMonEtl = $null
$PktMonExport = $null

if ($PktMonCapture) {
    $PktMonEtl = Start-PktMonReverseCapture -PktMon $PktMon -SessionDir $SessionDir -UdpPort $Port -Components $PktMonComponents
    $PktMonStarted = $true
    Write-Host "PktMon ETL:          $PktMonEtl"
    Write-Host ""
}

try {

# Clean the PrivyHub task so this run starts with a single diagnostic Activity.
[void](Invoke-NativeQuietExitCode -FilePath $Adb -Arguments @("-s", $Onn, "shell", "am", "force-stop", $Package))
Start-Sleep -Milliseconds 500

# Remove only prior reverse-probe app-private outputs. Other diagnostics are preserved.
[void](Invoke-NativeQuietExitCode -FilePath $Adb -Arguments @(
    "-s", $Onn, "shell", "run-as", $Package, "rm", "-f",
    "files/transport_reverse/latest_sender.csv", "files/transport_reverse/latest_summary.json", "files/transport_reverse/latest_progress.json"
))
[void](Invoke-NativeQuietExitCode -FilePath $Adb -Arguments @("-s", $Onn, "logcat", "-c"))

$ExpectedPackets = $DurationSeconds * 200
$ReceiverDuration = $DurationSeconds + 20
$ReceiverStdout = Join-Path $SessionDir "windows_receiver_stdout.txt"
$ReceiverStderr = Join-Path $SessionDir "windows_receiver_stderr.txt"
$ReceiveArgs = @(
    $ReverseScript,
    "receive",
    "--bind", "0.0.0.0",
    "--port", "$Port",
    "--duration-seconds", "$ReceiverDuration",
    "--expected-packets", "$ExpectedPackets",
    "--receive-buffer-bytes", "$ReceiveBufferBytes",
    "--output-dir", $SessionDir
)

$ReceiverProcess = Start-Process `
    -FilePath $Python `
    -ArgumentList $ReceiveArgs `
    -PassThru `
    -NoNewWindow `
    -RedirectStandardOutput $ReceiverStdout `
    -RedirectStandardError $ReceiverStderr

Start-Sleep -Milliseconds 600
if ($ReceiverProcess.HasExited) {
    $Detail = if (Test-Path $ReceiverStderr) { Get-Content -Raw $ReceiverStderr } else { "" }
    throw "Windows reverse receiver exited before Android started. Port $Port may already be in use.`n$Detail"
}

$LaunchOutput = & $Adb -s $Onn shell am start -n "$Package/$Activity" `
    --es target_ip $PcIp `
    --ei udp_port $Port `
    --ei duration_seconds $DurationSeconds `
    --es label $SafeLabel `
    --es sender_priority $SenderPriority

if ($LASTEXITCODE -ne 0 -or ($LaunchOutput -join "`n") -match 'Error type|Activity class.*does not exist|Permission Denial') {
    try { $ReceiverProcess.Kill() } catch {}
    throw "Could not launch UdpReverseTransportProbeActivity. Rebuild/install PrivyHub after applying v0.5.0."
}

$WaitMs = ($ReceiverDuration + 4) * 1000
$ReceiverExitedInTime = $ReceiverProcess.WaitForExit($WaitMs)
if (-not $ReceiverExitedInTime) {
    try { $ReceiverProcess.Kill() } catch {}
    try { $ReceiverProcess.WaitForExit() } catch {}
    throw "Windows reverse receiver did not terminate within the expected diagnostic window."
}

# A final blocking wait drains redirected stdout/stderr. Do not use
# Process.ExitCode here: Windows PowerShell 5.1 can leave that property unset
# for Start-Process -PassThru processes even after WaitForExit(). The receiver's
# atomic success contract is the pair of files it writes only after its receive
# loop completes successfully.
$ReceiverProcess.WaitForExit()

$HostCsv = Join-Path $SessionDir "host_packets.csv"
$HostSummary = Join-Path $SessionDir "host_summary.json"
if (-not (Test-Path $HostCsv) -or -not (Test-Path $HostSummary)) {
    $Detail = if (Test-Path $ReceiverStderr) { Get-Content -Raw $ReceiverStderr } else { "" }
    throw ("Windows reverse receiver exited without producing its completion files.`n" +
        "Expected:`n  $HostCsv`n  $HostSummary`n" +
        "Receiver stderr:`n$Detail")
}

if ($PktMonStarted) {
    $PktMonExport = Stop-And-SummarizePktMonReverseCapture -PktMon $PktMon -Python $Python -ReverseScript $ReverseScript -SessionDir $SessionDir -EtlPath $PktMonEtl
    $PktMonStarted = $false
}

Start-Sleep -Milliseconds 500
Capture-AndroidDiagnostics -Adb $Adb -Device $Onn -SessionDir $SessionDir

$RemoteSender = "files/transport_reverse/latest_sender.csv"
$RemoteSummary = "files/transport_reverse/latest_summary.json"
$AndroidSender = Join-Path $SessionDir "android_sender.csv"
$AndroidSummary = Join-Path $SessionDir "android_summary.json"

if (-not (Wait-RunAsFile -Adb $Adb -Device $Onn -RemotePath $RemoteSummary -TimeoutSeconds 10)) {
    $RemoteProgress = "files/transport_reverse/latest_progress.json"
    $LocalProgress = Join-Path $SessionDir "android_progress.json"
    $ProgressNote = ""
    if (Test-RunAsFile -Adb $Adb -Device $Onn -RemotePath $RemoteProgress) {
        try {
            Save-RunAsTextFile -Adb $Adb -Device $Onn -RemotePath $RemoteProgress -LocalPath $LocalProgress
            $ProgressNote = "`nProgress snapshot:`n  $LocalProgress"
        } catch {}
    }
    throw ("Android reverse-probe summary was not written after the extended diagnostic window." + $ProgressNote + "`nInspect:`n  " +
        (Join-Path $SessionDir "android_logcat.txt") + "`n  " +
        (Join-Path $SessionDir "android_activity_state.txt"))
}
Save-RunAsTextFile -Adb $Adb -Device $Onn -RemotePath $RemoteSummary -LocalPath $AndroidSummary

$SummaryText = Get-Content -Raw $AndroidSummary
try { $SummaryJson = $SummaryText | ConvertFrom-Json }
catch { throw "Android reverse summary is not valid JSON: $AndroidSummary" }
if ($null -ne $SummaryJson.error) {
    throw "Android reverse diagnostic failed: $($SummaryJson.error)"
}
if (-not (Wait-RunAsFile -Adb $Adb -Device $Onn -RemotePath $RemoteSender -TimeoutSeconds 2)) {
    throw "Android reverse summary exists but sender CSV was not written."
}
Save-RunAsTextFile -Adb $Adb -Device $Onn -RemotePath $RemoteSender -LocalPath $AndroidSender

& $Python $ReverseScript compare `
    --sender-csv $AndroidSender `
    --host-csv $HostCsv `
    --output-dir $SessionDir
if ($LASTEXITCODE -ne 0) {
    throw "Reverse probe comparison failed with exit code $LASTEXITCODE"
}

Write-Host ""
Write-Host "Reverse probe logs: $SessionDir"
Write-Host "Use combined_summary.txt for the Android-send / Windows-receive timing comparison."
if ($PktMonExport) {
    Write-Host "PktMon sanitized summary: $($PktMonExport.SummaryText)"
    Write-Host "Upload pktmon_presence_summary.txt/json; raw pktmon_full.txt stays local unless specifically needed."
}
}
finally {
    if ($PktMonStarted -and $PktMon) {
        [void](Invoke-NativeQuietExitCode -FilePath $PktMon -Arguments @("stop"))
        [void](Invoke-NativeQuietExitCode -FilePath $PktMon -Arguments @("filter", "remove"))
    }
}
