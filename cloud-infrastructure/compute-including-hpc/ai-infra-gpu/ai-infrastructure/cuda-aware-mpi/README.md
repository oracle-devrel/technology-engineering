# Build a CUDA-aware version of OpenMPI 

Open MPI is an open source Message Passing Interface (MPI) implementation that is heavily used on parallel computing architectures. For HPC workloads, with a lot of traffic between the CPU and the GPU, marginal gains can be obtained by making Open MPI CUDA-aware. 

## Prerequisites

In this example, we are using a type VM.GPU.A100.80G.1 instance, a virtual machine featuring a NVIDIA A100 80 GB GPU and a standard Ubuntu 22.04 image. On this instance, we will install:
* NVIDIA drivers
* CUDA Container toolkit
* GDRCOPY
* UCX
* Open MPI

## Configuration walkthrough

For the sake of simplicity, installation scripts can be found in the [scripts](assets/scripts) folder.

### Installing NVIDIA drivers and CUDA

The first is to install the NVIDIA drivers using the `ubuntu-drivers-common` package:
```
sudo apt-get install -y ubuntu-drivers-common
```
Available drivers can be found using the `sudo ubuntu-drivers --gpgpu list` command. If you want to install the 535 server driver version, run:
```
sudo ubuntu-drivers --gpgpu install nvidia:535-server
```
The `nvidia-smi` command requires the installation of the additional package:
```
sudo apt-get install -y nnvidia-utils-535-server
```
CUDA and its compiler `nvcc` can be installed with the following commands:
```
# Remove outdated signing key
sudo apt-key del 7fa2af80

# Network repository installation
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb

# Update apt repository cache
sudo apt-get update

# install CUDA SDK
sudo apt-get install cuda-toolkit
sudo apt-get install nvidia-gds # to include all GDS (GPUDirect Storage) packages

# Reboot the system
sudo reboot
```
Verify that NVCC is available with `nvcc --version`. One can also verify that cuda has been correctly installed and added to your path with `echo $PATH`.

### Installing GDRCopy

This step is pretty straightforward. One can simply download the project from the official repo `git clone https://github.com/NVIDIA/gdrcopy.git` and then use the following commands to build the packages:
```
cd gdrcopy
sudo apt-get install -y nvidia-dkms-535-server
sudo apt-get install -y build-essential devscripts debhelper fakeroot pkg-config dkms
cd packages
CUDA=/usr/local/cuda-12.8 ./build-deb-packages.sh
sudo dpkg -i gdrdrv-dkms_2.5-1_amd64.Ubuntu22_04.deb
sudo dpkg -i libgdrapi_2.5-1_amd64.Ubuntu22_04.deb
sudo dpkg -i gdrcopy-tests_2.5-1_amd64.Ubuntu22_04+cuda12.8.deb
sudo dpkg -i gdrcopy_2.5-1_amd64.Ubuntu22_04.deb
```

### Building UCX with GDRCopy and CUDA support

Same as previous step, one can download the project from the official repo `git clone https://github.com/openucx/ucx.git` and then build it:
```
cd ucx
./configure --prefix=/usr/local/ucx --with-cuda=/usr/local/cuda --with-gdrcopy=/usr
make -j8 install
```
Additionnally, one can check the UCX build info:
```
ubuntu@<hostname>:~$ /usr/local/ucx/bin/ucx_info -d | grep cuda
# Memory domain: cuda_cpy
#     Component: cuda_cpy
#         memory types: host (reg), cuda (access,alloc,reg,detect), cuda-managed (access,alloc,reg,cache,detect)
#      Transport: cuda_copy
#         Device: cuda
# Memory domain: cuda_ipc
#     Component: cuda_ipc
#         memory types: cuda (access,reg,cache)
#      Transport: cuda_ipc
#         Device: cuda
#         memory types: cuda (access,reg)
#         Device: cuda
ubuntu@<hostname>:~$ /usr/local/ucx/bin/ucx_info -d | grep gdr_copy
# Memory domain: gdr_copy
#     Component: gdr_copy
#      Transport: gdr_copy
```

### Building Open MPI with CUDA and UCX

To install Open MPI, download the package from the [download page](https://www.open-mpi.org/software/ompi/v4.1/) and run the following commands:
```
wget https://download.open-mpi.org/release/open-mpi/v4.1/openmpi-4.1.8.tar.bz2

tar xf openmpi-4.1.8.tar.bz2
cd openmpi-4.1.8

# Configure with CUDA and UCX support
./configure --prefix=/opt/openmpi --with-cuda=/usr/local/cuda --with-ucx=/usr/local/ucx

# Build OpenMPI on 8 parallel threads
make -j 8 all
sudo make install
```
If several Open MPI implementations are installed on the same machine, make sure to verify which one is used by default (if added to the `$PATH` environment variable) by the `mpirun` command:
```
which mpirun
```
To make sure that the custom one is used, call `mpirun` with its full path `/opt/openmpi/bin/mpirun`.

One can verify that Open MPI has been successfully built with CUDA support running either one of the below commands:
```
ubuntu@<hostname>:~$ /opt/openmpi/bin/ompi_info | grep "MPI extensions"
          MPI extensions: affinity, cuda, pcollreq
ubuntu@<hostname>:~$ /opt/openmpi/bin/ompi_info --parsable --all | grep mpi_built_with_cuda_support:value
mca:mpi:base:param:mpi_built_with_cuda_support:value:true
```

## Sources

Here are useful links:
* [CUDA installation Guide](https://docs.nvidia.com/cuda/cuda-installation-guide-linux/#ubuntu)
* [Building CUDA-aware Open MPI](https://www.open-mpi.org/faq/?category=buildcuda)
* [GDRCopy GitHUb repo](https://github.com/NVIDIA/gdrcopy)
* [UCX GitHub repo](https://github.com/openucx/ucx)
* [Open MPI download](https://www.open-mpi.org/software/ompi/v4.1/)