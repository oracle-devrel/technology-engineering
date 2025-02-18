#!/bin/bash

# Remove outdated signing key
sudo apt-key del 7fa2af80

# Network installation of the repository
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb

# Update apt repository cache
sudo apt-get update

# install CUDA SDK
sudo apt-get install cuda-toolkit
sudo apt-get install nvidia-gds # to include all GDS (GPUDirect Storage) packages

# Reboot the system
sudo reboot
