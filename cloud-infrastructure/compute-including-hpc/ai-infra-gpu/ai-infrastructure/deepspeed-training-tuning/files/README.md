# DeepSpeed LLM Training on OCI H100 SLURM Cluster

This repository automates deployment of a multi-node SLURM cluster with RDMA-enabled H100 GPUs on OCI for training large language models using DeepSpeed.

##  Tuned Configuration

We developed a custom-tuned deepspeed_config.json tailored for:
- Multi-node training
- RDMA-aware NCCL backend
- H100’s bfloat16-optimized tensor cores
- DeepSpeed ZeRO Stage 2 with communication overlap

The `tuned_ds_config.json` includes:
- Switched from fp16 to bf16 (optimal for H100)
- Enabled overlap_comm, contiguous_gradients, and increased bucket sizes
- Used gradient_accumulation_steps=8 to balance memory use and throughput
- Tweaked aio settings for better I/O performance during training
- Removed optimizer/parameter offloading to fully utilize GPU RAM


This configuration delivers up to **13% more training throughput** versus default settings on OCI H100 infrastructure.

## With this updated configuration:
- Training throughput improved by ~13%
- GPU utilization increased more consistently across all 8 nodes
- Communication latency reduced on RDMA fabric
- No stability or memory issues observed with ZeRO Stage 2

## 📂 Contents

- `scripts/tuned_ds_config.json` – optimized DeepSpeed configuration
- `scripts/run_deepspeed.slurm` – job script for SLURM
- `README.md` – usage overview and tuning explanation

## Usage

1. Deploy SLURM H100 cluster on OCI
2. SSH to master node
3. Submit the job:

```bash
sbatch run_deepspeed.slurm
```

Model output and logs will be written to `$HOME/output`.

## Conclusion
- NCCL tuning alone isn’t always sufficient — framework-level configuration (DeepSpeed) must align with hardware.
- H100 GPUs benefit significantly from bfloat16 and increased comm overlap.
- ZeRO Stage 2 provided a solid balance of memory efficiency and speed. ZeRO-3 is reserved for future scaling.
- System-aware configuration (bucket sizes, threading, and memory layout) is essential for reaching peak performance.

## Next Steps
- Benchmark with ZeRO Stage 3 for models approaching GPU memory limits.
- Test pipeline parallelism on >16 node jobs.
- Evaluate DeepSpeed 0.13+ features such as NVMe offloading and optimizer fusion on upcoming jobs.