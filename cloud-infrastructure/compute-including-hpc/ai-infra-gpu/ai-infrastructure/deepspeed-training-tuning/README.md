# Overview

This repository provides a step-by-step deployment of DeepSpeed training for Large Language Models (LLMs) on Oracle Cloud Infrastructure (OCI), using H100 GPU clusters with RDMA and SLURM.

This setup includes a tuned DeepSpeed configuration (`tuned_ds_config.json`) that provides up to **13% performance improvement** over standard configurations.

Reviewed: 06.06.2025
# When to use this asset?

Use this asset when you need to:
- Train large-scale language models on OCI with H100 hardware.
- Utilize RDMA-enabled SLURM clusters for distributed multi-node DeepSpeed training.
- Achieve improved throughput via custom-tuned DeepSpeed JSON configs.

# How to use this asset?
- deploy OCI HPC stack with H100 multiple instances.
- Improve training performance by using a tuned configuration for the deepspeed LLM model.

## Prerequisites & Docs

### Prerequisites

* An OCI tenancy with H100 GPU quota (shape: BM.GPU.H100.8).
* A [Huggingface](https://huggingface.co/) account with a valid Auth Token.
* SSH access to the deployed head node of your SLURM cluster.

### Documentation & Resources

* [DeepSpeed Documentation](https://www.deepspeed.ai/docs/)
* [TinyLlama Model (HF)](https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0)
* [Mistral LLMs](https://mistral.ai/technology/#models)
* [OCI HPC Stack](https://github.com/oracle-quickstart/oci-hpc)

## Model Training Workflow
- please refer files/README.md for more details

### Instance Configuration

The deployment uses a cluster of `BM.GPU.H100.8` bare metal instances, provisioned with cluster networking and RDMA.

The DeepSpeed job is submitted via SLURM using the `run_deepspeed.slurm` script. The environment includes a shared OCI File Storage System mounted on all nodes.

### DeepSpeed Tuned Configuration

The `tuned_ds_config.json` applies the following optimizations:
- Switched from fp16 to bf16 (optimal for H100)
- Enabled overlap_comm, contiguous_gradients, and increased bucket sizes
- Used gradient_accumulation_steps=8 to balance memory use and throughput
- Tweaked aio settings for better I/O performance during training
- Removed optimizer/parameter offloading to fully utilize GPU RA

These optimizations are benchmarked to deliver up to **13% faster training throughput** on OCI H100 clusters.

### Launch Training Job

Submit your training job using SLURM:

```bash
sbatch $HOME$/scripts/run_deepspeed.slurm
```

The job script uses:
- `train.py`: your LLM training script
- `tuned_ds_config.json`: DeepSpeed configuration file
- Local datasets and Hugging Face model/tokenizer

### Example curl Test (after model fine-tuning)

To serve the trained model via OpenAI-compatible API:

```bash
curl http://localhost:8000/v1/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "your-model-name",
        "prompt": "A GPU is a",
        "max_tokens": 128,
        "temperature": 0.7
    }'
```

## Notes

To train larger models like Mixtral or Mistral 7B on H100, make sure to:
- Scale the number of nodes appropriately
- Use quantization or tensor parallelism when needed
- Ensure models and datasets fit into GPU memory with DeepSpeed ZeRO optimization

# Acknowledgments

- **Author** - Deepak Soni (GPU Black Belt)

# License
 
Copyright (c) 2025 Oracle and/or its affiliates.
 
Licensed under the Universal Permissive License (UPL), Version 1.0.
 
See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.