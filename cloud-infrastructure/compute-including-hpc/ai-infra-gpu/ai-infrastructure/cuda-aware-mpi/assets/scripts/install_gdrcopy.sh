#!/bin/bash

git clone https://github.com/NVIDIA/gdrcopy.git
cd gdrcopy
sudo apt-get install -y nvidia-dkms-535-server
sudo apt-get install -y build-essential devscripts debhelper fakeroot pkg-config dkms
cd packages
CUDA=/usr/local/cuda-12.8 ./build-deb-packages.sh
sudo dpkg -i gdrdrv-dkms_2.5-1_amd64.Ubuntu22_04.deb
sudo dpkg -i libgdrapi_2.5-1_amd64.Ubuntu22_04.deb
sudo dpkg -i gdrcopy-tests_2.5-1_amd64.Ubuntu22_04+cuda12.8.deb
sudo dpkg -i gdrcopy_2.5-1_amd64.Ubuntu22_04.deb