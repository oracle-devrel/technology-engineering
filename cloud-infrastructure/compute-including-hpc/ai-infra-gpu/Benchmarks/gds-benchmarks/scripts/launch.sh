#!/bin/bash
set -x

repetitions=1;

mode=$1 #0 GPU_DIRECT, 1 CPU_ONLY, 2 CPU_GPU, 5 GPU_DIRECT_ASYNC, 6 GPU_BATCH

workers=$2 #1 to 128

blocksize=$3 #4k to 1M

testmode=$4 #0 Read, 1 Write, 2 Randread, 3 Randwrite

size=1G

case $mode in
    "0")
    log_dir=$PWD/../logs/GPU_DIRECT/
    ;;
    "1")
    log_dir=$PWD/../logs/CPU_ONLY/
    ;;
    "2")
    log_dir=$PWD/../logs/CPU_GPU/
    ;;
    "5")
    log_dir=$PWD/../logs/GPU_DIRECT_ASYNC/
    ;;
    "6")
    log_dir=$PWD/../logs/GPU_BATCH/
    ;;
    *)
    log_dir=$PWD/../logs/GPU_DIRECT/
    ;;
esac
for k in $(seq 1 $repetitions); 
  do
    timestamp=$(date +%s)
    lfname=$log_dir/gdsio_s${blocksize}_m${mode}_w${workers}_r${k}_t${testmode}_d$timestamp.log

    CMD="/usr/local/cuda/gds/tools/gdsio -D /mnt/nvme0/ -d 0 -w $workers -s $size -x $mode -i $blocksize -I $testmode -T 120 >> $lfname"; 
    echo $CMD >> $lfname
    echo $CMD | bash    
done;
