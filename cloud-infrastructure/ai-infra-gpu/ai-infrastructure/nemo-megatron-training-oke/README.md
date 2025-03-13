# Training LLMs with NVIDIA NeMo using Oracle Container Engine for Kubernetes

This repository demonstrates how to train LLM using
[NVIDIA NeMo](https://www.nvidia.com/en-gb/ai-data-science/products/nemo/)
on the Oracle Container Engine for Kubernetes (OKE) using
[NVIDIA Megatron](https://developer.nvidia.com/megatron-core).

Reference results from NVIDIA to train Llama 2 can be found on the
[NGC Catalog](https://catalog.ngc.nvidia.com/orgs/nvidia/teams/dgxc-benchmarking/resources/llama2-dgxc-benchmarking).

Reviewed: dd.mm.yyyy

# When to use this asset?

* If you want to get started with training LLM like Llama 2 on Kubernetes using OCI.

# How to use this asset?

## Prerequisites

* You have access to an Orcale Cloud Tenancy.
* You have access to shapes with NVIDIA GPUs such as A100.
* You have a HuggingFace account and access to `meta-llama/Llama-2-70b-hf`.

This guide is loosely based on the
[NVIDIA NeMo Framework Launcher guide for Kubernetes](https://docs.nvidia.com/nemo-framework/user-guide/24.07/playbooks/kubernetes.html).

## Infrastructure Setup

1. Create an OKE cluster according
   [to the instructions](https://github.com/oracle-quickstart/oci-hpc-oke/tree/main#instructions-for-deploying-an-oke-cluster-with-gpus-and-rdma-connectivity),
   importing one of the images and creating a GPU partition with BM.GPU.H100.8 nodes.

   The configuration here assumes a minimum of 16 BM.GPU.H100.8 nodes.

   - Ensure that the follwing setting is selected under the "OKE Cluster" section:

     > Disable OKE GPU device plugin

     as this tutorial will install the GPU operator later.

2. Create a new File System for NFS, and modify the [persistent volume configuration in `pv.yaml`](./files/pv.yaml) to match.
   Optimally, this will utilize High Performance Mount Targets (HMPT) as described in the following two whitepapers:
   * [Scale Out OCI File Storage Performance for AI/ML and
Data-Intensive Workloads](https://docs.oracle.com/en-us/iaas/Content/Resources/Assets/whitepapers/scale-out-oci-file-storage-performance-for-data-intensive-workloads.pdf)
   * [File Storage Performance Guide](https://docs.oracle.com/en-us/iaas/Content/Resources/Assets/whitepapers/file-storage-performance-guide.pdf)

3. Install Helm, the NVIDIA GPU Operator, and the Volcano scheduler according to
   [NVIDIA NeMo Framework Launcher guide for Kubernetes](https://docs.nvidia.com/nemo-framework/user-guide/24.07/playbooks/kubernetes.html).

4. Apply the persistenv volume configuration and MPI parameter configuration map:
   ```sh
   kubectl apply -f mpi.yaml
   kucectl apply -f pv.yaml
   ```

5. Mount the file system on the Kubernetes operator node. In the following, the mount location is assumed to be `/mnt/data/`.

6. Copy the node sorting script and LLM configuration into the file system:
   ```sh
   cp -R config utils /mnt/data
   ```

## Data Preparation and Training

1. Download the tokenizer model from HuggingFace:
   ```sh
   mkdir -p /mnt/data/tokenizer
   huggingface-cli login
   huggingface-cli download meta-llama/Llama-2-70b-hf tokenizer.model --local-dir /mnt/data/tokenizer
   huggingface-cli download meta-llama/Llama-2-70b-hf config.json --local-dir /mnt/data/tokenizer
   ```

2. Apply the preprocessing job that will download and tokenize parts of the Pile dataset:
   ```sh
   kubectl apply -f preprocessing.yaml
   ```

   The progress can then be monitored by
   ```sh
   kubectl logs -f nemo-megatron-preprocessing-mpimaster-0
   ```

3. Following successful preprocessing, the training can be started with:
   ```sh
   kubectl apply -f training_70b.yaml
   ```

   The progress can then be monitored by
   ```sh
   kubectl logs -f nemo-megatron-training-mpimaster-0
   ```

4. Calculate training throughput. For this, the following data is required from the training output:
   ```
   [NeMo I 2025-03-10 16:24:43 perf_metrics_utils:42] train_step_timing in s: [7.13, 7.12, 7.12, 7.13, 7.13, 7.13, 7.12, 7.13, 7.14, 7.13, 7.14, 7.26, 7.13, 7.13, 7.13, 7.13, 7.15, 7.14, 7.14, 7.13, 7.14, 7.14, 7.14, 7.14, 7.13, 7.14, 7.14, 7.14, 7.14, 7.14]
   ```
   This log can be saved into a file with:
   ```sh
   kubectl logs nemo-megatron-training-mpimaster-0 > training.log
   ```
   and the performance analyzed with
   ```sh
   python3 utils/performance.py training.log
   ```

## Changing the Configuration

* **Increase the training file count**

  To increase the amount of training data, edit the file count by modifying all
  occurences of the `file_numbers=0-0` range in
  [`preprocessing.yaml`](./files/preprocessing.yaml) and re-run the
  preprocessing step.
  E.g. change this setting to `file_numbers=0-9` to process 10 files.

  Then modify the file list in the training configuration, e.g.,
  [`config_7b.yaml`](./files/config/config_7b.yaml)
  to match the file count:
  ```yaml
  data_prefix:
  - 1
  - /mnt/data/pile/my-gpt3_00_text_document
  ...
  - 1
  - /mnt/data/pile/my-gpt3_09_text_document
  ```

* **Vary the node count for training**

  Changing the node count will require modifications to both the training
  configuration and the Volcano job. E.g. to double the node count for the 7B
  example, modify

  * [`training_7b.yaml`](./files/training_7b.yaml) to have twice the replica
    count for the `mpiworker` definition
  * Double the `num_nodes` and `global_batch_size` keys in
    [`config_7b.yaml`](./files/config/config_7b.yaml).  In the optimal case,
    this should give constant performance in terms of token throughput per
    second per GPU.

## Potential Issues

* **PyTorch can't resolve hostnames via c10d**

  If the rendezvous backend for PyTorch fails to connect to an OCI style
  hostname for Kubernetes clusters, one work around this resolution failure by
  augmenting `/etc/hosts` for every pod.

  For convenience, this is facilitated by enhancing `mpi.yaml` via
  ```sh
  ./utils/host_list.sh >> mpi.yaml
  kubectl apply -f mpi.yaml
  ```
  and afterwards restarting the training job.

# Acknowledgments

- **Author** - Matthias Wolf (GPU Solution Specialist)

# License
 
Copyright (c) 2025 Oracle and/or its affiliates.
 
Licensed under the Universal Permissive License (UPL), Version 1.0.
 
See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
