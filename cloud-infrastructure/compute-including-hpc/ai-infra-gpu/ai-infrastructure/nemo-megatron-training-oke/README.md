# Training LLMs with NVIDIA NeMo using Oracle Container Engine for Kubernetes

This repository demonstrates how to train LLM using
[NVIDIA NeMo](https://www.nvidia.com/en-gb/ai-data-science/products/nemo/)
on the Oracle Container Engine for Kubernetes (OKE) using
[NVIDIA Megatron](https://developer.nvidia.com/megatron-core).

Reference results from NVIDIA to train Llama 3 can be found on the
[NGC Catalog](https://catalog.ngc.nvidia.com/orgs/nvidia/teams/dgxc-benchmarking/resources/llama3-dgxc-benchmarking).

Reviewed: 16.10.2025

# When to use this asset?

* If you want to get started with training LLM like Llama 3 on Kubernetes using OCI.

# How to use this asset?

## Prerequisites

* You have access to an Orcale Cloud Tenancy.
* You have access to shapes with NVIDIA GPUs such as H100.
* You have a HuggingFace account and access to `meta-llama/Llama-3.1-8B-Instruct`.

This guide is loosely based on the
[NVIDIA NeMo Framework Launcher guide for Kubernetes](https://docs.nvidia.com/nemo-framework/user-guide/24.07/playbooks/kubernetes.html).

## Infrastructure Setup

1. Create an OKE cluster according
   [to the instructions](https://github.com/oracle-quickstart/oci-hpc-oke/tree/main#instructions-for-deploying-an-oke-cluster-with-gpus-and-rdma-connectivity),
   importing one of the images and creating a GPU partition with BM.GPU.H100.8 nodes.

   The configuration here assumes a minimum of 1 BM.GPU.H100.8 node for
   training with 8B parameters, and a minimum of 8 BM.GPU.H100.8 nodes for 70B
   parameters.
   
   If another shape is used, the NCCL and MPI parameters in the Kubernetes
   [configuration map](./files/training/templates/mpi.yaml) should be adapted
   using the same parameter values as the
   [performance testing scripts](https://github.com/oracle-quickstart/oci-hpc-oke/tree/main/manifests/nccl-tests).

   - Ensure that the follwing setting is selected under the "OKE Cluster" section:

     > Disable OKE GPU device plugin

     as this tutorial will install the GPU operator later.

2. Create a new File System for NFS, and modify the [persistent volume configuration in `pv.yaml`](./files/pv.yaml) to match.
   Optimally, this will utilize High Performance Mount Targets (HMPT) as described in the following two whitepapers:
   * [Scale Out OCI File Storage Performance for AI/ML and
Data-Intensive Workloads](https://docs.oracle.com/en-us/iaas/Content/Resources/Assets/whitepapers/scale-out-oci-file-storage-performance-for-data-intensive-workloads.pdf)
   * [File Storage Performance Guide](https://docs.oracle.com/en-us/iaas/Content/Resources/Assets/whitepapers/file-storage-performance-guide.pdf)

3. Install the NVIDIA GPU Operator according to
   [NVIDIA NeMo Framework Launcher guide for Kubernetes](https://docs.nvidia.com/nemo-framework/user-guide/24.07/playbooks/kubernetes.html), then install the [Volcano scheduler](https://github.com/volcano-sh/volcano) with:
   ```sh
   kubectl apply -f https://raw.githubusercontent.com/volcano-sh/volcano/master/installer/volcano-development.yaml
   ```

4. Copy the [files in this repository](./files) to the Kubernetes operator node.
   You can download them from this repository via:
   ```sh
   BRANCH=main
   curl -L https://github.com/oracle-devrel/technology-engineering/archive/refs/heads/${BRANCH}.tar.gz|tar xzf - --strip-components=6 technology-engineering-${BRANCH}/cloud-infrastructure/ai-infra-gpu/ai-infrastructure/nemo-megatron-training-oke/files
   ```
   
   Then modify the values in [`training/values.yaml`](./files/training/values.yaml) to match the storage server and export path.

5. Mount the file system on the Kubernetes operator node. In the following, the mount location is assumed to be `/mnt/data/`.

## Data Preparation and Training

1. Download the tokenizer model from HuggingFace:
   ```sh
   mkdir -p /mnt/data/tokenizer
   huggingface-cli login
   huggingface-cli download meta-llama/Llama-3.1-8B-Instruct tokenizer_config.json --local-dir /mnt/data/tokenizer
   huggingface-cli download meta-llama/Llama-3.1-8B-Instruct tokenizer.json --local-dir /mnt/data/tokenizer
   ```

2. Apply the preprocessing job that will download and tokenize parts of the Pile dataset:
   ```sh
   helm install --set num_nodes=1 --set download_data=true "my-preprocessing" ./training
   ```

   The progress can then be monitored by
   ```sh
   kubectl logs -f megatron-prep-my-preprocessing-mpimaster-0
   ```

3. Following successful preprocessing, the training can be started with:
   ```sh
   helm install --set num_nodes=1 "my-training-v0" ./training
   ```

   The progress can then be monitored by
   ```sh
   kubectl logs -f megatron-train-my-training-v0-mpimaster-0
   ```

4. Calculate training throughput. For this, the following data is required from the training output:
   ```
   [NeMo I 2025-03-10 16:24:43 perf_metrics_utils:42] train_step_timing in s: [7.13, 7.12, 7.12, 7.13, 7.13, 7.13, 7.12, 7.13, 7.14, 7.13, 7.14, 7.26, 7.13, 7.13, 7.13, 7.13, 7.15, 7.14, 7.14, 7.13, 7.14, 7.14, 7.14, 7.14, 7.13, 7.14, 7.14, 7.14, 7.14, 7.14]
   ```
   This log can be saved into a file with:
   ```sh
   kubectl logs  megatron-train-my-training-v0-mpimaster-0 > training.log
   ```
   and the performance analyzed with
   ```sh
   python3 utils/performance.py training.log
   ```

## Potential Issues

* **PyTorch can't resolve hostnames via c10d**

  If the rendezvous backend for PyTorch fails to connect to an OCI style
  hostname for Kubernetes clusters, one work around this resolution failure by
  augmenting `/etc/hosts` for every pod.

  For convenience, this is facilitated by enhancing `mpi.yaml` via
  ```sh
  ./utils/host_list.sh >> ./training/files/mpi.yaml
  ```
  and afterwards reinstalling the training job via Helm.

# Acknowledgments

- **Author** - Matthias Wolf (GPU Solution Specialist)

# License
 
Copyright (c) 2025 Oracle and/or its affiliates.
 
Licensed under the Universal Permissive License (UPL), Version 1.0.
 
See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
