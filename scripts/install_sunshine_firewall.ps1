$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$SunshineExe = Join-Path $ProjectRoot "runtime\streaming\sunshine\sunshine.exe"

if (-not (Test-Path $SunshineExe)) {
    throw "Sunshine runtime not found. Run setup_sunshine_portable.ps1 first."
}

$Identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$Principal = New-Object Security.Principal.WindowsPrincipal($Identity)

if (-not $Principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw "This firewall step requires an elevated PowerShell window."
}

$TcpRule = "PrivyHub Sunshine TCP"
$UdpRule = "PrivyHub Sunshine UDP"

Get-NetFirewallRule -DisplayName $TcpRule -ErrorAction SilentlyContinue |
    Remove-NetFirewallRule

Get-NetFirewallRule -DisplayName $UdpRule -ErrorAction SilentlyContinue |
    Remove-NetFirewallRule

New-NetFirewallRule `
    -DisplayName $TcpRule `
    -Direction Inbound `
    -Action Allow `
    -Profile Private `
    -Program $SunshineExe `
    -Protocol TCP `
    -LocalPort 47984,47989,48010 |
    Out-Null

New-NetFirewallRule `
    -DisplayName $UdpRule `
    -Direction Inbound `
    -Action Allow `
    -Profile Private `
    -Program $SunshineExe `
    -Protocol UDP `
    -LocalPort 47998,47999,48000,48002,48010 |
    Out-Null

Write-Host ""
Write-Host "PrivyHub Sunshine firewall rules installed."
Write-Host ""
Write-Host "Allowed on Windows Private profile only:"
Write-Host "  TCP: 47984, 47989, 48010"
Write-Host "  UDP: 47998, 47999, 48000, 48002, 48010"
Write-Host ""
Write-Host "Not opened:"
Write-Host "  TCP 47990 (Sunshine web UI remains local to the PC)"
Write-Host "  UDP 5353 (automatic discovery is not required)"
Write-Host ""
Write-Host "The GL-iNet boundary must permit the same stream ports from the"
Write-Host "isolated onn network to the companion, just as it already permits"
Write-Host "PrivyHub's existing companion/media ports."
