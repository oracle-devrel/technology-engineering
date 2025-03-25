#!/bin/bash

# For usage instructions see host_switch_readme.txt

hosts_file="/etc/hosts"
primary_hosts_file="/path/to/primary_hosts.txt"

# Overwrite hosts file with primary version
sudo cp $primary_hosts_file $hosts_file

echo "Failback to primary complete."
