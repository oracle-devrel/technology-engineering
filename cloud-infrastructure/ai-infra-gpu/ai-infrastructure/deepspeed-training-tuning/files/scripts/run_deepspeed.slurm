#!/bin/bash
#SBATCH --job-name=ds-train
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=8
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:8
#SBATCH --time=06:00:00
#SBATCH --output=ds_output.log
#SBATCH --error=ds_error.log

export NCCL_DEBUG=INFO
export OMP_NUM_THREADS=8

deepspeed --num_gpus=8 /mnt/deepspeed/DeepSpeed/examples/llama_finetune.py \
  --deepspeed /mnt/deepspeed/scripts/tuned_ds_config.json \
  --model_name_or_path mistralai/Mistral-7B-Instruct-v0.1 \
  --train_file /mnt/deepspeed/data/train.json \
  --output_dir /mnt/deepspeed/output
