# Overview

This repository provides a step-by-step tutorial for deploying and using Mixtral 8x7B Large Language Model using the NVIDIA Triton Inference Server and the TensorRT-LLM backend.

# Requirements

* An OCI tenancy with GPU4 (A100 40GB) quota
* A Huggingface account with a valid Auth Token

# Model Deployment

## Instance Configuration

In this example a BM.GPU4.8 instance is used. The image is the Oracle Linux Gen2 GPU image. A boot volume of 1000 GB is recommended (running `sudo /usr/libexec/oci-growfs -y` might be necessary). Alternatively, one of the NVMe local drives can be mounted.

## Package Install

### Install and configure Docker

Enable all the required repositories. To do this you are going to need the yum-utils package.
```
sudo dnf install -y dnf-utils zip unzip
sudo dnf config-manager --add-repo=https://download.docker.com/linux/centos/docker-ce.repo
```
Install Docker.
```
sudo dnf remove -y runc
sudo dnf install -y docker-ce --nobest
```
Enable and start the Docker service.
```
sudo systemctl enable docker.service
sudo systemctl start docker.service
```

### Install and configure NVIDIA Container Toolkit

Configure the production repository.
```
curl -s -L https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo | \
sudo tee /etc/yum.repos.d/nvidia-container-toolkit.repo
```
Optionally, configure the repository to use experimental packages.
```
sudo yum-config-manager --enable nvidia-container-toolkit-experimental
```
Install the NVIDIA Container Toolkit packages.
```
sudo yum install -y nvidia-container-toolkit
```
Configure the container runtime by using the nvidia-ctk command.
```
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

## Build the tensortrtllm_backend container

Clone the repoistory.
```
git clone https://github.com/triton-inference-server/tensorrtllm_backend.git
```
Install git-lfs.
```
sudo yum install git git-lfs -y
```
Go to the directory and update the submodules.
```
cd tensorrtllm_backend
git lfs install
git submodule update --init --recursive
```
Build the backend container using the dockerfile.
```
DOCKER_BUILDKIT=1 docker build -t triton_trt_llm -f dockerfile/Dockerfile.trt_llm_backend .
```
## Build the engines

Start the container.
```
sudo docker run --rm -it --net host --shm-size=2g --ulimit memlock=-1 --ulimit stack=67108864 --gpus all -v /home/opc/tensorrtllm_backend:/tensorrtllm_backend triton_trt_llm bash
```
Then  build the model engines with tensor parallelism (split and fit the model on the 8 A100 GPUs).
```
python ../llama/convert_checkpoint.py --model_dir ./Mixtral-8x7B-v0.1 \
                             --output_dir ./tllm_checkpoint_mixtral_8gpu \
                             --dtype float16 \
                             --tp_size 8
trtllm-build --checkpoint_dir ./tllm_checkpoint_mixtral_8gpu \
                 --output_dir ./trt_engines/mixtral/tp8 \
                 --gemm_plugin float16
```
The egines files are located in the `./trt_engines/mixtral/tp8` folder.

## Prepare the model repository

Create the model repository that will be used by the Triton inference server.
```
cd tensorrtllm_backend
mkdir triton_model_repo
```
Copy the example models to the model repository.
```
cp -r all_models/inflight_batcher_llm/* triton_model_repo/
```
Copy the engines to the model repository.
```
cp tensorrt_llm/examples/mixtral/trt_engines/mixtral/tp8/* triton_model_repo/tensorrt_llm/1
```
It is now time to modify the config.pbtxt files. Following the guidelines from the [official repo](https://github.com/triton-inference-server/tensorrtllm_backend), here are the sections to be modified:

* tensorrtllm_backend/triton_model_repo/ensemble/config.pbtxt

```
max_batch_size: 1
```

* tensorrtllm_backend/triton_model_repo/postprocessing/config.pbtxt

```
max_batch_size: 1
...
parameters {
  key: "tokenizer_dir"
  value: {
    string_value: "/tensorrtllm_backend/tensorrt_llm/examples/mixtral/Mixtral-8x7B-Instruct-v0.1"
  }
}

parameters {
  key: "skip_special_tokens"
  value: {
    string_value: "True"
  }
}

instance_group [
    {
        count: 1
        kind: KIND_CPU
    }
]
```

* tensorrtllm_backend/triton_model_repo/preprocessing/config.pbtxt

```
max_batch_size: 1
...
parameters {
  key: "tokenizer_dir"
  value: {
    string_value: "/tensorrtllm_backend/tensorrt_llm/examples/mixtral/Mixtral-8x7B-Instruct-v0.1"
  }
}

parameters {
  key: "skip_special_tokens"
  value: {
    string_value: "True"
  }
}

instance_group [
    {
        count: 1
        kind: KIND_CPU
    }
]
```

* tensorrtllm_backend/triton_model_repo/tensorrt_llm/config.pbtxt
```
max_batch_size: 1

model_transaction_policy {
  decoupled: true
}

dynamic_batching {
    preferred_batch_size: [ 1 ]
    max_queue_delay_microseconds: 100
}
...
instance_group [
  {
    count: 1
    kind : KIND_CPU
  }
]
...
parameters: {
  key: "gpt_model_type"
  value: {
    string_value: "inflight_fused_batching"
  }
}
parameters: {
  key: "gpt_model_path"
  value: {
    string_value: "/tensorrtllm_backend/triton_model_repo/tensorrt_llm/1"
  }
}
...
parameters: {
  key: "batch_scheduler_policy"
  value: {
    string_value: "max_utilization"
  }
}
```

* tensorrtllm_backend/triton_model_repo/tensorrt_llm_bls/config.pbtxt

```
max_batch_size: 1

model_transaction_policy {
  decoupled: true
}
...
instance_group [
  {
    count: 1
    kind : KIND_CPU
  }
]
```
Files examples are provided in this repo.

## Run the inference server

Once all the files are ready, start the container that has been built previously:
```
sudo docker run --rm -it --net host --shm-size=2g --ulimit memlock=-1 --ulimit stack=67108864 --gpus all -v /home/opc/tensorrtllm_backend:/tensorrtllm_backend triton_trt_llm bash
```
and from within the container start the server by running the following python command:
```
python3 scripts/launch_triton_server.py --world_size=8 --model_repo=/tensorrtllm_backend/triton_model_repo
```
where --world_size is the number of GPUs you want to use for serving.
If the deployment is successful you should get something like:
```
I0919 14:52:10.475738 293 grpc_server.cc:2451] Started GRPCInferenceService at 0.0.0.0:8001
I0919 14:52:10.475968 293 http_server.cc:3558] Started HTTPService at 0.0.0.0:8000
I0919 14:52:10.517138 293 http_server.cc:187] Started Metrics Service at 0.0.0.0:8002
```
## Test the model

To test the model, one can query the the server endpoint, for example with:
```
curl -X POST localhost:8000/v2/models/ensemble/generate -d '{"text_input": "What is machine learning?", "max_tokens": 512, "bad_words": "", "stop_words": ""}'
```

# Resources

* [TensortRT-LLM Backend Documentation](https://github.com/triton-inference-server/tensorrtllm_backend)
* [Mistral Documentation](https://docs.mistral.ai/)