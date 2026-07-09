#!/bin/bash
#IoType: READ XferType: CPUONLY Threads: 1 DataSetSize: 16777216/16777216(KiB) IOSize: 512(KiB) Throughput: 0.870023 GiB/sec, Avg_Latency: 561.190887 usecs ops: 32768 total_time 18.390314 secs
#IoType: WRITE XferType: GPUD Threads: 4 DataSetSize: 660071168/4194304(KiB) IOSize: 256(KiB) Throughput: 5.280329 GiB/sec, Avg_Latency: 185.122957 usecs ops: 2578403 total_time 119.214722 secs

declare -a dirs=("../logs/CPU_GPU/" "../logs/CPU_ONLY/" "../logs/GPU_DIRECT/" "../logs/GPU_DIRECT_ASYNC/" "../logs/GPU_BATCH/")

echo "size;mode;test;workers;bandwidth (GiB/s);latency (usecs);iops;time(secs)";
for d in "${dirs[@]}"; do
    for i in $(ls -1 $d | sort -t _ -k7,7); do 
        size=$(echo $i | sed 's/IoDepth: [0-9]* //g' | awk -F'[_]' '{print $2;}' | sed 's/s//'); 
        mode=$(echo $i | sed 's/IoDepth: [0-9]* //g' | awk -F'[_]' '{print $3;}' | sed 's/m//'); 
        workers=$(echo $i | sed 's/IoDepth: [0-9]* //g' | awk -F'[_]' '{print $4;}' | sed 's/w//'); 
        reps=$(echo $i | sed 's/IoDepth: [0-9]* //g' | awk -F'[_]' '{print $5;}' | sed 's/r//'); 
        bandwidth=$(tail -n 1 $d/$i | sed 's/IoDepth: [0-9]* //g' | awk '{print $12}'); 
        lat=$(tail -n 1 $d/$i | sed 's/IoDepth: [0-9]* //g' | awk '{print $15}' ); 
        ops=$(tail -n 1 $d/$i | sed 's/IoDepth: [0-9]* //g' | awk '{print $18}' ); 
        time=$(tail -n 1 $d/$i | sed 's/IoDepth: [0-9]* //g' | awk '{print $20}' ); 
	test=$(tail -n 1 $d/$i | sed 's/IoDepth: [0-9]* //g' | awk '{print $2}' );
	#echo "$size;$mode;$reps;${write::5};${reads::5}"; 
	echo "$size;$mode;$test;$workers;${bandwidth};$lat;$ops;$time;";
    done
done;
