# The credential prompt avoids putting a password into code or shell history.
param([Parameter(Mandatory=$true)][string]$LinuxServerIP)
$Credential = Get-Credential -UserName 'media' -Message 'Linux Samba credential'
New-SmbMapping -LocalPath 'Z:' -RemotePath "\\$LinuxServerIP\media" -UserName $Credential.UserName -Password $Credential.GetNetworkCredential().Password -Persistent $true -SaveCredentials
'Windows-to-Linux round trip' | Set-Content 'Z:\windows-check.txt'
Get-Content 'Z:\windows-check.txt'
Get-SmbConnection | Select-Object ServerName,ShareName,Dialect,Encrypted
