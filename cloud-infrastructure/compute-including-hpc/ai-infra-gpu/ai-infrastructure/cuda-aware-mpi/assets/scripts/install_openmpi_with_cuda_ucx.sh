#!/bin/bash

wget https://download.open-mpi.org/release/open-mpi/v4.1/openmpi-4.1.8.tar.bz2

tar xf openmpi-4.1.8.tar.bz2
cd openmpi-4.1.8

# Configure with CUDA and UCX support
./configure --prefix=/opt/openmpi --with-cuda=/usr/local/cuda --with-ucx=/usr/local/ucx

# Build OpenMPI on 8 parallel threads
make -j 8 all
sudo make install