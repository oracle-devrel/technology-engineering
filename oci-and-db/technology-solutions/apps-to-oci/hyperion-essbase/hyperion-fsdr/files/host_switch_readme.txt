# README for Host Switch Scripts

During a failover to a standby region, applications often rely on hostnames to access critical resources. These hostnames usually resolve to IP addresses within the primary region. By switching the hosts file to a version containing the corresponding IP addresses for the standby region, applications can continue to function seamlessly without needing code modifications. This ensures minimal disruption and a smoother transition during a failover event. The host_switch scripts automate this process and can be integrated into Full Stack Disaster Recovery plans.

## Instructions

### Prerequisites

- Ensure the PowerShell execution policy allows script execution (set to at least RemoteSigned or similar if the script is not signed).
- The script needs to be run with sufficient privileges to modify the hosts files.
- Make sure you are able to run commands on OCI compute nodes: https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/runningcommands.htm

### Files

- `host_switch_failover.ps1`: PowerShell script to switch the hosts file after failover to the standby region.
- `host_switch_failback.ps1`: PowerShell script to restore the original hosts file after failback to the primary region.
- `primary_hosts.txt`: Contains the original host file for the primary region.
- `standby_hosts.txt`: Maps standby region IP addresses to primary region hostnames.

### Overall Process

#### Preparation

1. Create `primary_hosts.txt` and `standby_hosts.txt` files with the appropriate IP address and hostname mappings for their corresponding regions.
2. Place all files (`host_switch_failover.ps1`, `host_switch_failback.ps1`, `primary_hosts.txt`, `standby_hosts.txt`) in an accessible location on both the primary and standby systems.

#### Failover to Standby

1. On the standby system, execute the script `host_switch_failover.ps1`:

    C:\Windows\System32\WindowsPowerShell\v1.0\Powershell.exe c:\scripts\host_switch_failover.ps1

   Or, if using a shell script:

    /path/to/host_switch_failover.sh

2. This will replace the hosts file with the standby mappings.

#### Failback to Primary

1. On the original primary system, execute the script `host_switch_failback.ps1`:

    C:\Windows\System32\WindowsPowerShell\v1.0\Powershell.exe c:\scripts\host_switch_failback.ps1

   Or, if using a shell script:

    /path/to/host_switch_failback.sh

2. This will restore the hosts file to the original primary mappings.

### Important Notes

- **File Paths**: Adjust file paths in the instructions and the script if your files are located in a different directory.
- **Backup**: The script creates an archive backup of the hosts file with a date and time appended to the filename (e.g., `hosts.bak_20240308_163012`) before any modifications are made.
- **Permissions**: Ensure the user or process executing the script has permissions to modify the hosts file in `C:\Windows\System32\drivers\etc`. You may need to run the script with administrative privileges.
- **Automation**: Consider integrating this script into your broader disaster recovery orchestration processes for automated execution, if applicable.

### Additional Tips

- **Test Thoroughly**: Test the script in a non-production environment to ensure it works as expected before using it in your production switchover process.
- **Script Protection**: Store the script and host files in a secure location with appropriate access controls to prevent unauthorized modifications.
