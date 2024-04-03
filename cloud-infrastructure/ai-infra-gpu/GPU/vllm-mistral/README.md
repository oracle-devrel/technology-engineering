# Overview

This repository provides a step-by-step tutorial for deploying and using [Mistral 7B Instruct Large Language Model](https://mistral.ai/technology/#models) using [vLLM](https://github.com/vllm-project/vllm?tab=readme-ov-file).

# Requirements

* A OCI tenancy with A10 GPU quota
* A [Huggingface](https://huggingface.co/) account with a valid Auth Token

# Model Deployment

## Mistral models

[Mistral.ai](https://mistral.ai/) is a French AI startup that develop Large Language Models (LLMs). Mistral 7B is the small yet powerful open model that supports English and code. The Mistral 7B Instruct is a chat optimized version of Mistral 7B. Mixtral 8x7B is a 7B sparse Mixture-of-Experts that supports French, Italian, German and Spanish on top of English and code (stronger than Mistra 7B). It uses 12B parameters out of 45B total.

## vLLM Library

vLLM is an alternative model serving solution to NVIDIA Triton. It is easy to use as it comes as a preconfigured container.

## Instance Configuration

In this example a single A10 GPU VM shape, codename VM.GPU.A10.1, is used. The image is the NVIDIA GPU Cloud Machine image from the OCI marketplace. A boot volume of 200 GB is also recommended.

## Image Update

Since the latest NGC image is already 1 year old, it is recommended to update NVIDIA drivers and CUDA by running:

```
sudo apt purge nvidia* libnvidia*
sudo apt-get install -y cuda-drivers-545
sudo apt-get install -y nvidia-kernel-open-545
sudo apt-get install -y cuda-toolkit-12-3
sudo reboot
```

## System configuration

Once the NVIDIA packages are updated, it is necessary to reconfigure docker in order to make it GPU aware:

```
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

## Container Deployment

To deploy the model, simply run the vLLM container:

```
docker run --gpus all \
    -e HF_TOKEN=$HF_TOKEN -p 8000:8000 \
    ghcr.io/mistralai/mistral-src/vllm:latest \
    --host 0.0.0.0 \
    --model mistralai/Mistral-7B-Instruct-v0.2
```
where $HF_TOKEN is the HuggingFace Auth Token set as an environment variable. The model download may take up to 20 minutes.

Once the deployment is finished, the model is available at http://0.0.0.0:8000.

# Model Calling

The Mistral model is available through a OpenAI compatible API. As a prerequisite you must have the curl package installed.

```
sudo apt-get install curl
```

Here are 3 examples:

* List the model available in the container:

```
curl http://localhost:8000/v1/models | json_pp
```

* Complete a sentence:

```
curl http://localhost:8000/v1/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "mistralai/Mistral-7B-Instruct-v0.2",
        "prompt": "A GPU is a",
        "max_tokens": 128,
        "temperature": 0.7
    }' | json_pp
```

* Chat

```
curl http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "mistralai/Mistral-7B-Instruct-v0.2",
        "messages": [
            {"role": "user", "content": "Which GPU models are available on Oracle Cloud Infrastructure?"}
        ]
    }' | json_pp
```

# Notes

Mixtral8x7B is much more greedy that Mistral 7B and it will not fit in a single A10 GPU VM, nor a quad A10 GPU BM. Therefore it is necessary to either:
* Increase the size of the shape to a BM.GPU4.8 (8 x A100 40 GB GPUs).
* Use a quantized version such as [TheBloke/mixtral-8x7b-v0.1-AWQ](https://huggingface.co/TheBloke/mixtral-8x7b-v0.1-AWQ). However, AWQ quantization on vLLM is not fully optimized yet.

```
docker run --gpus all \
    -e HF_TOKEN=$HF_TOKEN -p 8000:8000 \
    vllm/vllm-openai:latest \
    --host 0.0.0.0 \
    --port 8000 \
    --model TheBloke/mixtral-8x7b-v0.1-AWQ \
    --quantization awq \
    --tensor-parallel-size 4 \
    --gpu-memory-utilization 0.95 \
    --enforce-eager
```

# Resources

* [vLLM Documentation](https://docs.vllm.ai/en/latest/)
* [Mistral Documentation](https://docs.mistral.ai/)