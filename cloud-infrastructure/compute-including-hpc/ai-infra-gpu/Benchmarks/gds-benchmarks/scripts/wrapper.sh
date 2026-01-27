#!/bin/bash

#mode=$1 #0 GPU_DIRECT, 1 CPU_ONLY, 2 CPU_GPU, 5 GPU_DIRECT_ASYNC, 6 GPU_BATCH
#
#workers=$2 #1 to 128
#
#blocksize=$3 #4k to 1M
#
#testmode=$4 #0 Read, 1 Write, 2 Randread, 3 Randwrite

#CMD="/usr/local/cuda/gds/tools/gdsio -D /mnt/nvme0/ -d 0 -w $workers -s $size -x $mode -i $blocksize -I $testmode -T 120 >> $lfname";

for m in 0 2 5 6; do
	for w in 4 8 16 32 64 128; do
		#for b in 4k 8k 16k 32k 64k 128k 256k 512k 1M; do
		for b in 4k 16k 64k 256k 1M; do
			for t in 1 0 3 2; do
				echo "./launch.sh $m $w $b $t";
			done;
		done;
	done;
done;
