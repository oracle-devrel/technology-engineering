#!/bin/bash
curl --fail -H "Authorization: Bearer Oracle" -L0 http://169.254.169.254/opc/v2/instance/metadata/oke_init_script | base64 --decode >/var/run/oke-init.sh

node_memory_gb=$(curl -s --fail -H "Authorization: Bearer Oracle" -L0 http://169.254.169.254/opc/v2/instance/ | jq '.shapeConfig.memoryInGBs' | awk '{print int($0)}')
node_cpu_count=$(curl -s --fail -H "Authorization: Bearer Oracle" -L0 http://169.254.169.254/opc/v2/instance/ | jq '.shapeConfig.ocpus' | awk '{print int($0)}')

kube_cpu_allocation=0
kube_memory_allocation=0

# Calculate CPU allocations for system daemons
i=1
while [ $i -le $node_cpu_count ]
do
    if (( i == 1 )); then
        kube_cpu_allocation=$((kube_cpu_allocation + 60))
    elif (( i == 2 )); then
        kube_cpu_allocation=$((kube_cpu_allocation + 10))
    elif (( i == 3 || i == 4 )); then
        kube_cpu_allocation=$((kube_cpu_allocation + 5))
    elif (( i > 4 )); then
        kube_cpu_allocation=$((kube_cpu_allocation + 3))
    fi
    ((i++))
done

# Calculate Memory allocations for system daemons
i=1
while [ $i -le $node_memory_gb ]
do
    if (( i <= 4 )); then
        kube_memory_allocation=$((kube_memory_allocation + 255))
    elif (( i > 4 && i <= 8 )); then
        kube_memory_allocation=$((kube_memory_allocation + 205))
    elif (( i > 8 && i <= 16 )); then
        kube_memory_allocation=$((kube_memory_allocation + 105))
    elif (( i > 16 && i <= 128 )); then
        kube_memory_allocation=$((kube_memory_allocation + 60))
    elif (( i > 128 )); then
        kube_memory_allocation=$((kube_memory_allocation + 20))
    fi
    ((i++))
done

echo "CPU $kube_cpu_allocation in total"
echo "Memory $kube_memory_allocation in total"

# configure kubelet with image credential provider
bash /var/run/oke-init.sh --kubelet-extra-args "--kube-reserved=cpu="$kube_cpu_allocation"m,memory="$kube_memory_allocation"Mi"