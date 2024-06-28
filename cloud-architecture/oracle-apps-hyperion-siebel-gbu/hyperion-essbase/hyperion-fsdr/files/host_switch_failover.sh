#!/bin/bash

# For usage instructions see host_switch_readme.txt

hosts_file="/etc/hosts"
backup_file="${hosts_file}.bak"  # Change if needed
standby_hosts_file="/path/to/standby_hosts.txt"

# Get the current date and time for the optional backup filename
current_date=$(date +"%Y%m%d_%H%M%S")

# Create an archive backup of the current hosts file (optional)
sudo cp $hosts_file "${backup_file}_${current_date}"

# Overwrite hosts file with standby version
sudo cp $standby_hosts_file $hosts_file

echo "Failover to standby complete."
