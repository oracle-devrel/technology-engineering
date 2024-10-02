# Reserve Memory and CPU for Kubernetes System Daemons

Kubernetes resources can be reserved at the node pool level and applied to every worker node with cloud-init execution at boot time. Remember, OKE uses cloud-init to set up the worker node customizations.

If you wonder what the magic number for CPU and memory reservations is, the answer is hidden in the node shape and size correlation. The implementation below is based on well-known algorithms from the market described [here](https://learnk8s.io/allocatable-resources).

The script reserves memory with the following rules:
- 255 MiB for every 1 GB of memory (up to 4 GB)
- 205 MiB for every 1 GB of memory (from 4 GB up to 8 GB)
- 105 MiB for every 1 GB of memory (from 8 GB up to 16 GB)
- 160 MiB for every 1 GB of memory (from 16 GB up to 128 GB)
- 20 MiB for every 1 GB of memory (from 128 GB)

The script reserves CPU with the following rules:
- 60 milicores for the first physical core (OCPU)
- 10 milicores for the second physical core (OCPU)
- 5 milicores for the third and fourth physical core (OCPU)
- 3 milicores for every further physical core (OCPU)

Paste the following [cloud-init script](/app-dev/oke/oke-kube-reserved-cloud-init/cloud-init.sh) to every node pool where you want to reserve kube resources. The quantity of reserved resources depends on the node’s memory and OCPUs. The process of adding cloud-init scripts to OKE is defined [here](https://docs.oracle.com/en-us/iaas/Content/ContEng/Tasks/contengusingcustomcloudinitscripts.htm#contengusingcustomcloudinitscripts_topic_Using_the_Console).

```bash
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
```