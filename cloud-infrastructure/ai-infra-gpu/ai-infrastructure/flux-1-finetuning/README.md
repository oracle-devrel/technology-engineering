# flux-1-finetuning

This repo is designed to quickly  prepare a demo that showcases how to use OCI GPU shapes to finetune lora models of flux.1-dev. 

Flux is a set of diffusion models created by BlackForest Labs, and are subject to [licensing terms](https://github.com/black-forest-labs/flux/blob/main/model_licenses/LICENSE-FLUX1-dev)
In this blog we will show how to fine tune flux.1-dev that is available in [HuggingFace](https://huggingface.co/black-forest-labs/FLUX.1-dev)

There are several projects that can be used to work with flux models
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) is a powerful and user-friendly tool for creating high-quality images using AI, including the FLUX model. It offers a modular workflow design that allows users to create custom image generation processes by connecting different components
- [AItoolkit](https://github.com/comfyanonymous/ComfyUI) is a tool that simplifies Flux fine tuning experience expoecially to reduce VRAM requirements. 
- [SimpleTuner](https://github.com/bghira/SimpleTuner) is a set of scripts that simplify distributed fine tuning on multiple GPUs 

Prerequisites: 
- Linux based GPU VM with recent Nvidia driver and Cuda toolkit
- git, Miniconda installed
- An account in HuggingFace where you can login with huggingface-cli login

## Installing AI toolkit ##

use aitoolkit.yaml  to prepare a conda environment with the required packages 

```
conda create env -f aitoolkit.yaml
conda activate aitoolkit
```

then you can clone the ai-toolkit 
```
git clone https://github.com/ostris/ai-toolkit.git
cd ai-toolkit
git submodule update --init --recursive
```

## Dataset generation ##

you can take 10 pictures of yourself.


## Training

Aitoolkit has a large set of options that can be exploited to train a lora model for flux1. You can find examples in the directory config/examples/.
According to the different GPUs you can use them to either reduce video memory consumption, or to improve training performance. 


- folder_path: "/path/to/images/folder" , speicfy where the dataset is
- gradient_checkpointing: true  This feature allows to reduce memory footprint, but this increases computation time by about 35%. On large memory GPUs it is convenient to set it to false.
- model:quantize: true  This uses intermediate 8bit quantization to reduce memory footprint, the final model will still be 16bits, so turn it on only on small GPUs.
- model:low_vram: true  This further reduces memory footprint on very small GPUs.
- prompts: this is a list of prompts that are used the create intermidiate images to chck quality, for analyzing performances you can remove them    
- batch_size: 1 increasing batch size on a single GPU deteriorates performance, recommended to stick with 1.
- trigger_word: a GPU Specialist   Here you set the keyword that you can use in the prompt.

## Installing ComfyUI

ComfyUI can be used the test the generated lora model. It can be installed in the same conda env as Attoolkit

```
git clone https://github.com/comfyanonymous/ComfyUI/tree/v0.3.10
cd ComfyUI
python main.py
```

You can connect to the ComfyUI GUI by pointing your browser to port 8188, according to the network configuration a port forward might be required. 

Then you need to import models that are required by the workflow.

Download the [Clip Safetensor](https://huggingface.co/comfyanonymous/flux_text_encoders/blob/main/clip_l.safetensors) to ComfyUI/models/clip/
This model plays a crucial role in text-to-image generation tasks by processing and encoding textual input.

Download the Text Encoder [T5xxl Safetensor](https://huggingface.co/comfyanonymous/flux_text_encoders/blob/main/t5xxl_fp8_e4m3fn.safetensors) to ComfyUI/models/clip/

Download the [VAE Safetensor](https://huggingface.co/black-forest-labs/FLUX.1-schnell/blob/main/ae.safetensors) to ComfyUI/models/vae

Download the [Flux.1-dev UNET model](https://huggingface.co/black-forest-labs/FLUX.1-dev/tree/main) to ComfyUI/models/unet

## Testing Lora models with ComfyUI

Everytime you create a lora model with Ai-toolkit you can copy it to ComfyUI/models/lora 

Import the workflow by opening the file workflow-lora.json 

You will then be able to select the model in the Load Lora box. Make sure also the proper models are selected in the Load diffusion Model, DualCLIPLoader, and Load VAE boxes.

You can write your own prompt in the CLIP Text Encode box, remeber to refer to the keyword used for training the Lora.
![Alt text](files/ComfyUI.png?raw=true "ComfyUI Lora workflow")

## Installing SimpleTuner

```
git clone --branch=release https://github.com/bghira/SimpleTuner.git
```
Copy config/config.json.example to config/config.json

Then you execute the training with

```
./train.sh
```

Parallel training is possible using Accelerate (the Deepspeed implementation on Flux is buggy at the time of writing.
When more GPUs are used, the batch size is increased automatically, so the number os steps required to process one full epoch is riduced proportionally.


If present the Accelerate configuration will be taken from the config file in

~/.cache/huggingface/accelerate/default_config.yaml

```
compute_environment: LOCAL_MACHINE
debug: false
distributed_type: *MULTI_GPU*
downcast_bf16: 'no'
enable_cpu_affinity: true
gpu_ids: all
machine_rank: 0
main_training_function: main
mixed_precision: bf16
num_machines: 1
num_processes: 4
rdzv_backend: static
same_network: true
tpu_env: []
tpu_use_cluster: false
tpu_use_sudo: false
use_cpu: false
```

If this file is not present you can create a file config/config.env and use it to set this environmental variable:

```
TRAINING_NUM_PROCESSES=4
```






