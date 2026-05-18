#!/bin/bash

#echo "Creating RAID0 volume" - A10
#mdadm --create --verbose /dev/md0 --level=0 --raid-devices=2 /dev/nvme0n1 /dev/nvme1n1 
echo "Creating RAID0 volume" # - A 100
mdadm --create --verbose /dev/md0 --level=0 --raid-devices=4 /dev/nvme0n1 /dev/nvme1n1 /dev/nvme2n1 /dev/nvme3n1

echo "Formatting RAID0 volume"
mkfs.ext4 /dev/md0 

echo "Creating mount dir"
mkdir /mnt/data

echo "Mounting device md0"
mount -o data=ordered /dev/md0 /mnt/data

echo "Adjusting privileges"
chown -R opc. /mnt/data/
