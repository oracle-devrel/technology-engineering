#!/bin/bash

git clone https://github.com/openucx/ucx.git
cd ucx
./configure --prefix=/usr/local/ucx --with-cuda=/usr/local/cuda --with-gdrcopy=/usr
make -j8 install