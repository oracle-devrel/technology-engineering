#!/bin/bash

set -ex

source myenv/bin/activate

## NCCL parameters configuration based on OCI H100 GPU Instance deployment 
export NCCL_TIMEOUT=1800

export NCCL_IGNORE_CPU_AFFINITY=1
export OMPI_MCA_coll_hcol_enable=0
export NCCL_CROSS_NIC=2
export NCCL_SOCKET_NTHREADS=16
export NCCL_DEBUG=DEBUG
export NCCL_CUMEM_ENABLE=0
export NCCL_IB_SPLIT_DATA_ON_QPS=0
export NCCL_IB_QPS_PER_CONNECTION=16
export NCCL_IB_GID_INDEX=3
export NCCL_IB_HCA="mlx5_0,mlx5_1,mlx5_3,mlx5_4,mlx5_5,mlx5_6,mlx5_7,mlx5_8,mlx5_9,mlx5_10,mlx5_12,mlx5_13,mlx5_14,mlx5_15,mlx5_16,mlx5_17"
export NCCL_IB_TC=41
export NCCL_IB_SL=0
export NCCL_IB_TIMEOUT=22
export HCOLL_ENABLE_MCAST_ALL=0
export UCX_TLS=tcp
export UCX_NET_DEVICES=eth0
export RX_QUEUE_LEN=8192
export NCCL_SOCKET_IFNAME=eth0 

export OMP_NUM_THREADS=16  # should be optimally number of CPU cores / number of GPUs per node

export GPUS_PER_NODE=8
MASTER_NODE=$(scontrol show hostname | head -n 1)
export MASTER_ADDR=$(scontrol show node=$MASTER_NODE | awk -F= '/NodeAddr=/{print $2}' | awk '{print $1}')
export NNODES=$SLURM_NTASKS
export NODE_RANK=$SLURM_NODEID
export MASTER_PORT=9001
export WORLD_SIZE_JOB=$SLURM_NTASKS
export DISTRIBUTED_ARGS="--nproc_per_node $GPUS_PER_NODE --nnodes $NNODES --node_rank $NODE_RANK --master_addr $MASTER_ADDR --master_port $MASTER_PORT "

torchrun $DISTRIBUTED_ARGS \
	train.py \
	--model_config tuned_ds_config.json \
	--tokenizer_name TinyLlama/TinyLlama-1.1B-Chat-v1.0 \
	--dataset_mixer data_mixer.json \
	--dataset_name mix \
	--dataset_type local \
	--dataset_packed \
	--batch_size 12 \
	--gradient_checkpointing \
	--max_train_steps 1000000 \
	--val_after_steps 10000 \
	--num_warmup_steps 10000 \
	--learning_rate 1e-4 \
	--num_gpus_node $GPUS_PER_NODE \
	--gradient_clipping 1 \
	--gradient_accumulation_steps 2 \
	--dataset_cache "./hf-cache"

