# Run on a Windows host in an elevated PowerShell session. Not executed on macOS.
param([string]$LinuxClientIP, [string]$SharePath = 'C:\BroadcastMedia')
$ErrorActionPreference = 'Stop'
if (-not $LinuxClientIP) { throw 'Supply the Linux client IP for the firewall rule.' }
$Password = Read-Host 'Password for dedicated media account' -AsSecureString
if (-not (Get-LocalUser -Name 'media' -ErrorAction SilentlyContinue)) {
    New-LocalUser -Name 'media' -Password $Password -Description 'Assessment SMB user'
}
New-Item -ItemType Directory -Path $SharePath -Force | Out-Null
$Principal = "$env:COMPUTERNAME\media"
icacls $SharePath /grant "${Principal}:(OI)(CI)M"
if (-not (Get-SmbShare -Name 'media' -ErrorAction SilentlyContinue)) {
    New-SmbShare -Name 'media' -Path $SharePath -ChangeAccess $Principal -EncryptData $true
}
Set-SmbServerConfiguration -EnableSMB1Protocol $false -Force
New-NetFirewallRule -DisplayName 'Assessment SMB from Linux' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 445 -RemoteAddress $LinuxClientIP
Get-SmbShare -Name 'media'
