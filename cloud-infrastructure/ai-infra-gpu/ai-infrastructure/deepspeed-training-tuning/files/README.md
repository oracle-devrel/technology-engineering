# DeepSpeed LLM Training on OCI H100 SLURM Cluster

This repository automates deployment of a multi-node SLURM cluster with RDMA-enabled H100 GPUs on OCI for training large language models using DeepSpeed.

## 🔧 Tuned Configuration

The `tuned_ds_config.json` includes:
- Mixed precision (fp16) with loss scaling
- ZeRO Stage 2 optimization with overlapping communication
- Optimized AdamW with increased learning rate
- Activation checkpointing
- Gradient accumulation for batch size scaling

📈 This configuration delivers up to **13% more training throughput** versus default settings on OCI H100 infrastructure.

## 📂 Contents

- `scripts/tuned_ds_config.json` – optimized DeepSpeed configuration
- `scripts/run_deepspeed.slurm` – job script for SLURM
- `README.md` – usage overview and tuning explanation

## 🚀 Usage

1. Deploy SLURM H100 cluster on OCI
2. SSH to master node
3. Submit the job:

```bash
sbatch /mnt/deepspeed/scripts/run_deepspeed.slurm
```

Model output and logs will be written to `/mnt/deepspeed/output`.

