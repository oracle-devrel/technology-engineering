#!/bin/bash

echo "Checking ACS"
/usr/local/cuda/gds/tools/gdscheck.py -p | grep "ACS enabled" | sort -u -k 6

echo "Disabling ACS"
/usr/local/cuda/gds/tools/gdscheck.py -p | grep "ACS enabled" | sort -u -k 6 | awk '{print $NF}' | xargs -I {} sudo setpci -s {} ecap_acs+6.w=0

echo "Checking ACS"
/usr/local/cuda/gds/tools/gdscheck.py -p | grep "ACS enabled" | sort -u -k 6

echo "Setting correct LBA on NVMEs"
#the -f in the nvme command is required if using a os version higher than 18.04
for i in $(lsblk | grep -i nvme | awk '{print $1}'); do echo nvme format  -l 0 /dev/${i}; done | bash


echo "Creating RAID0 volume"
mdadm --create --verbose /dev/md0 --level=0 --raid-devices=4 /dev/nvme0n1 /dev/nvme1n1 /dev/nvme2n1 /dev/nvme3n1

echo "Formatting RAID0 volume"
mkfs.ext4 /dev/md0 

echo "Mounting device md0"
mount -o data=ordered /dev/md0 /mnt/nvme0

echo "Adjusting privileges"
chown -R ubuntu. /mnt/nvme0/
