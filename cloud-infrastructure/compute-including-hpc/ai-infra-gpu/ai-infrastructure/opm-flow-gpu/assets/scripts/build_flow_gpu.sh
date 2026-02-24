#!/bin/bash

for repo in opm-common opm-grid
do
    git clone https://github.com/OPM/$repo.git
    mkdir $repo/build && cd $repo/build
    cmake ..
    make -j 8
    cd ../..
done

git clone https://github.com/OPM/opm-simulators.git
mkdir opm-simulators/build && cd opm-simulators/build
cmake .. -DUSE_GPU_BRIDGE=OFF # add the -DCONVERT_CUDA_TO_HIP=ON option for AMD GPUs
make -j 8
cd ../..

git clone https://github.com/OPM/opm-upscaling.git
mkdir opm-upscaling/build && cd opm-upscaling/build
cmake ..
make -j 8
cd ../..