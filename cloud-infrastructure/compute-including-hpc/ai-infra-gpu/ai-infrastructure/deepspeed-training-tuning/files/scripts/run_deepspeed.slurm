#!/bin/bash

#SBATCH --nodes=4
#SBATCH --job-name=deepspeed-performance-test
#SBATCH --exclusive
srun -l exec_torchrun.sh
