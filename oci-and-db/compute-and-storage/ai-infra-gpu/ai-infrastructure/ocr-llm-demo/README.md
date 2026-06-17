# ocr-llm-demo
How to quickly setup a demo to demonstrate OCR capabilities of multimodal llm
New generation open multimodal llm are a very good fit for complex OCR workloads.
Many of the funcionalities that would require fine tuning with traditional OCR models can now be achieved with prompt engineering. 
The multilingual support, the hability to recognize handwriting are some of the features that can be used to improve OCR workloads.

## Prerequisites of the demo
To download model weights you will need access token to Hugging Face.
The demo was run on Ubuntu 24.04. But it should be possible to run it on other Ubuntu versions.
You need to install
- Cuda toolkit/Nvidia Driver
- anaconda or miniconda
- sudo apt-get install python-poppler


### Install and activate 
```
conda env create -f ocr-llm.yaml
conda activate ocr-llm
```

## LLM Models

In this Demo we use VLLM to serve multi modal models with the OpenAI API. We tested Pixtral-12B on a VM with 2 A10, and Qwen2-VL on a single A10. 
Llama-3.2-11B-Vision-Instruct is also an option.

You first need to login to Hugging Face to download the weights
```
huggingface-cli login
```
and you serve one of the VLLM supported visual models. According to the number of GPUs in your shape you might be able to execute one model or more concurrenlty. For llama-3.2 access in Europe is currenlty restricted.

```
vllm serve  mistralai/Pixtral-12B-2409 --dtype auto  --tokenizer-mode  mistral -tp 2 --port 8001 --max-model-len 32768

vllm serve  Qwen/Qwen2-VL-7B-Instruct  --dtype auto --max-model-len 8192 --enforce-eager --port 8000

vllm serve  meta-llama/Llama-3.2-11B-Vision-Instruct --dtype auto   --port 8002 --max-model-len 32768
```  
## Sample images

The folder pictures includes some example pictures that can be used in the demo. You can add additional images to improve the demo.
The LLM supported formats are PNG,JPG,WEBP, non animated GIF. I also added automated conversion for PDF images, but for multipage PDF only the firt page will be considered.


## Running the GUI

You have a Gradio based GUI available:
```
python gui.py
```

Gradio is configured to proxy to a public connection, similar to the following one
 ![Alt text](files/gui.png?raw=true "GUI")

## Executing Qwen-2.5-VL as backend API




Qwen-2.5-VL are now supported by VLLM but you mught still need to install transformers from github repo. 

You can execute the 72B model  on the 8 A100 GPUs of BM.GPU.4.8  with

```
vllm serve Qwen/Qwen2.5-VL-72B-Instruct  --dtype auto  -tp 8 --port 9193
```
inference time 40-50 seconds.

It can also be executed on a BM.GPU.L40s.4 by limiting context length

```
vllm serve Qwen/Qwen2.5-VL-72B-Instruct  --dtype auto  -tp 4 --port 9193 --max-model-len 16000 --enforce-eager
```
inference time about 60 seconds

The 7B model can be executed on 2 GPUs

```
vllm serve Qwen/Qwen2.5-VL-7B-Instruct  --dtype auto -tp 2  --port 9192
```



