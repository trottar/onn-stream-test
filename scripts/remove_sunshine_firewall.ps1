$ErrorActionPreference = "Stop"

$Identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$Principal = New-Object Security.Principal.WindowsPrincipal($Identity)

if (-not $Principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw "This firewall step requires an elevated PowerShell window."
}

"PrivyHub Sunshine TCP", "PrivyHub Sunshine UDP" |
    ForEach-Object {
        Get-NetFirewallRule `
            -DisplayName $_ `
            -ErrorAction SilentlyContinue |
            Remove-NetFirewallRule
    }

Write-Host "PrivyHub Sunshine firewall rules removed."
