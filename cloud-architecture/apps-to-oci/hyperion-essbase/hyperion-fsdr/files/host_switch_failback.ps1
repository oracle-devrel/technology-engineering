#ps1

# For usage instructions see host_switch_readme.txt

$hostsFile = "C:\Windows\System32\drivers\etc\hosts"
$primaryHostsFile = "C:\scripts\primary_hosts.txt"
$standbyHostsFile = "C:\scripts\standby_hosts.txt"

# Mode: "failover" or "failback"
$mode = "failback"

# Get the current date and time for the backup filename
$currentDate = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFile = $hostsFile + ".bak_" + $currentDate

if ($mode -eq "failover") {
    # Create an archive backup of the current hosts file
    Copy-Item $hostsFile $backupFile -Force

    # Overwrite hosts file with standby version
    Copy-Item $standbyHostsFile $hostsFile -Force

} elseif ($mode -eq "failback") {
    # Overwrite hosts file with primary version
    Copy-Item $primaryHostsFile $hostsFile -Force

} else {
    Write-Error "Invalid mode! Please specify either 'failover' or 'failback'."
}
