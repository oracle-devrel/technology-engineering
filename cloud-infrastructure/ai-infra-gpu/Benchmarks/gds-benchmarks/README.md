# DISCLAIMER

This code is provided as a starting point for your own benchmarks or for adaptation to your specific needs. It is not production-ready, and may lack a testing strategy, requiring modifications to function properly.

# gds-benchmakrs

```bash
[root@machine gds_benchmarks]# tree -L 2
.
├── backups
│   ├── csv
├── logs
│   ├── CPU_GPU
│   ├── CPU_ONLY
│   ├── GPU_BATCH
│   ├── GPU_DIRECT
│   └── GPU_DIRECT_ASYNC
├── README.md
└── scripts
    ├── 2csv.sh
    ├── cufile.log
    ├── initialize.sh
    ├── launch.sh
    └── rename.sh
```

The **'backups'** dir contains the backup of the previous runs (logfiles) and older CSV files. This directory is kept just in case some log files are missing.  
The **'logs'** directory is designated for storing the most recent log files. Its sub-directories are organized according to the **'mode'** employed during the runs.

The **'scripts'** directory contains all the bash scripts used for initializing the GDS machine, running benchmarks, and transforming log files into CSV format.

**'initialize.sh'**: This script prepares the machine for GDS usage by performing necessary configurations. It disables ACS, sets the correct LBA for the NVMes, and handles the creation, formatting, and mounting of a RAID 0 array, while also adjusting file system privileges.

**'launch.sh'**: This script executes the benchmarks and is parameterized by 'mode' (with options 0, 1, 2, 5, 6 corresponding to GPU_DIRECT, CPU_ONLY, CPU_GPU, GPU_DIRECT_ASYNC, GPU_BATCH, GPU_DIRECT) and the number of threads. Additionally, a third parameter allows for the specification of block size (ranging from 4k to 16M).

During operation, **'launch.sh'** will conduct multiple tests using a variety of block and file sizes, which are predefined (Block sizes include: 4k, 8k, 16k, 32k, 64k, 128k, 256k, 512k, 1M, 2M, 4M, 8M, 16M). Each test iteration is performed four times. The file size varies depending on the number of threads, and to maintain efficiency, file sizes are kept relatively small. The GDSIO benchmark scales the file size with the number of threads, which can lead to extensive data processing. For example, running eight threads with a 128G file size would result in a total of 1024 TB of data being written, reflecting the scale of operations handled by this setup.

Each test will be logged under the corresponding directory. The naming of the log files has the following format: ``gdsio_s<block size>_m<mode number>_w<threads / workers>_r<repetition number>_d<timestamp>.log``  
gdsio_s1M_m2_w1_r1_d1671836744.log  
For example, this log refers to a test that used 1M as block size, Mode 2 (CPU_GPU), 1 thread, and its timestamp.  
Each log also contains the full command that was issued to run:  

```bash
/usr/local/cuda/gds/tools/gdsio -D /mnt/nvme0/ -d 0 -w 1 -s 8G -x 2 -i 1M -I 1 -V >> /home/ubuntu/gds_benchmarks/scripts/../logs/CPU_GPU//gdsio_s1M_m2_w1_r1_d1671836744.log  
IoType: WRITE XferType: CPU_GPU Threads: 1 DataSetSize: 8388608/8388608(KiB) IOSize: 1024(KiB) Throughput: 4.179353 GiB/sec, Avg_Latency: 233.618286 usecs ops: 8192 total_time 1.914172 secs  
Verifying data  
IoType: READ XferType: CPU_GPU Threads: 1 DataSetSize: 8388608/8388608(KiB) IOSize: 1024(KiB) Throughput: 2.681619 GiB/sec, Avg_Latency: 364.043213 usecs ops: 8192 total_time 2.983272 secs  
```

**'2csv.sh'**: This script is responsible for converting the log files into CSV format. The resulting CSV files can then be imported into Excel for data visualization and analysis.

**'How to launch the scripts'**: To enhance operational flexibility, the launch.sh script has been modified to accommodate additional input parameters, including the block size. This enhancement allows for the resumption of interrupted runs without the necessity to restart them entirely. For instance, in a previous scenario, it was necessary to resume runs for mode 0 from 32 threads and a 16k block size. Subsequently, complete runs were conducted for all specified block sizes and thread counts:
```
for i in 32 64 128; 
  do 
    for k in 16k 32k 64k 128k 256k 512k 1M 2M 4M 8M 16M; 
      do 
        echo ./launch.sh 0 $i $k; 
    done; 
done | bash; 

for i in 1 2 4 8 16 32 64 128; 
  do 
    for k in 4k 8k 16k 32k 64k 128k 256k 512k 1M 2M 4M 8M 16M; 
      do 
        echo ./launch.sh 2 $i $k; 
    done; 
done | bash; 

for i in 1 2 4 8 16 32 64 128; 
  do 
    for k in 4k 8k 16k 32k 64k 128k 256k 512k 1M 2M 4M 8M 16M; 
      do 
        echo ./launch.sh 5 $i $k; 
    done; 
done | bash; 

for i in 1 2 4 8 16 32 64 128; 
  do 
    for k in 4k 8k 16k 32k 64k 128k 256k 512k 1M 2M 4M 8M 16M; 
      do 
      echo ./launch.sh 6 $i $k; 
    done; 
done | bash;
```

# License
 
Copyright (c) 2024 Oracle and/or its affiliates.
 
Licensed under the Universal Permissive License (UPL), Version 1.0.
 
See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
