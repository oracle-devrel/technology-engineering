# gds-benchmakrs
```
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
    ├── launch.sh.backup_2
    ├── rename.sh
    └── rename.sh.backup
```

The **'backups'** dir contains the backup of the previous runs (logfiles) and older csv files. This directory is kept just in case some log files are missing.  
The **'logs'** directory contains the very latest logs of each run. The sub-directories are split based on the 'mode' used during the runs.  
The **'scripts'** contains all the bash scripts used to initiate the gds machine, run the banchmark and convert the log files into csv files.  

**initialize.sh**: This script does everything that's required to have the machine configured to use GDS.  
It checks and disables the ACS, then sets the correct LBA on the NVMes, creates, formats, mounts the RAID 0 array and adjusts the privileges on the mounted fs.  

**launch.sh**: This script is the one that runs the actual benchmarks. The script accepts as first argument the 'mode' (0, 1, 2, 5, 6 which correspond to GPU_DIRECT, CPU_ONLY, CPU_GPU, GPU_DIRECT_ASYNC, GPU_BATCH, GPU_DIRECT) and as a second parameter the number of threads. (I would create a for loop and input different threads numbers when running the benchmarks). As an additional 3rd parameter, we now have to specify the block size (4k 8k 16k 32k 64k 128k 256k 512k 1M 2M 4M 8M 16M).  

The **launch.sh** script, will then launch several tests with different block and file sizes. This has been hardcoded (Block sizes: 4k 8k 16k 32k 64k 128k 256k 512k 1M 2M 4M 8M 16M). Each test will be repeated 4 times.  
Depending by the number of threads, the file size will change. For the sake of time, this has been kept rather low. The gdsio benchmark will multiply the number of threads for the file size. This might result time consuming even if you consider the scenario in which you are running 8 threads using 128G file size for example, because the file size is per thread. In that case the benchmark will attempt to write 128GB * 8 threads equals 1024 TB of data.  


Each test will be logged under the corresponding directoy. The naming of the log files has the following format: ``gdsio_s<block size>_m<mode number>_w<threads / workers>_r<repetition number>_d<timestamp>.log``  
gdsio_s1M_m2_w1_r1_d1671836744.log  
For example, this log refers to a test that used 1M as block size, Mode 2 (CPU_GPU), 1 thread and its timestamp.  
Each log also contains the full command that was issues to run:  
```
/usr/local/cuda/gds/tools/gdsio -D /mnt/nvme0/ -d 0 -w 1 -s 8G -x 2 -i 1M -I 1 -V >> /home/ubuntu/gds_benchmarks/scripts/../logs/CPU_GPU//gdsio_s1M_m2_w1_r1_d1671836744.log  
IoType: WRITE XferType: CPU_GPU Threads: 1 DataSetSize: 8388608/8388608(KiB) IOSize: 1024(KiB) Throughput: 4.179353 GiB/sec, Avg_Latency: 233.618286 usecs ops: 8192 total_time 1.914172 secs  
Verifying data  
IoType: READ XferType: CPU_GPU Threads: 1 DataSetSize: 8388608/8388608(KiB) IOSize: 1024(KiB) Throughput: 2.681619 GiB/sec, Avg_Latency: 364.043213 usecs ops: 8192 total_time 2.983272 secs  
```

**2csv.sh**: This script is the one that converts the content of the logfiles into csv format. The output csv file can then be imported into excel and plotted.  

**How to launch the scripts**: In order to have more flexibility, the launch.sh script has been adapted to accept more input parameters. The last parameter that was added is the block size. Doing so, allows us to resume runs that might have been interrupted without starting from scratch. One example above. In this example i had to resume the runs for mode 0, resuming from 32 threads and 16k block size. Following that, there are instead complete runs for all block sies and number of threads:
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

all other scripts were used to solve some issues and i just kept there in case these issues re-appear.  
