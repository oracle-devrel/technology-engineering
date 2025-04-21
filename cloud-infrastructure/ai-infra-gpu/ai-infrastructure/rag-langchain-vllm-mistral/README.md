# RAG with OCI, LangChain, and VLLMs

This repository is a variant of the Retrieval Augmented Generation (RAG) tutorial available [here](https://github.com/oracle-devrel/technology-engineering/tree/main/ai-and-app-modernisation/ai-services/generative-ai-service/rag-genai). Instead of the OCI GenAI Service, it uses a local deployment of Mistral 7B Instruct v0.3 using a vLLM inference server powered by an NVIDIA A10 GPU.

Reviewed: 23.05.2024

# When to use this asset?

To run the RAG tutorial with a local deployment of Mistral 7B Instruct v0.3 using a vLLM inference server powered by an NVIDIA A10 GPU.

# How to use this asset?

These are the following libraries and modules being used in this solution:

* **LlamaIndex**: a data framework for LLM-based applications that benefit from context augmentation.
* **LangChain**: a framework for developing applications powered by large language models.
* **vLLM**: a fast and easy-to-use library for LLM inference and serving.
* **Qdrant**: a vector similarity search engine.

As we're using a Mistral model, [Mistral.ai](https://mistral.ai/) also deserves a proper introduction: Mistral AI is a French AI startup that develops Large Language Models (LLMs), and one of the few companies with uncensored versions for their models Mistral 7B Instruct is a small yet powerful open model that supports English and code. The instructional version, the one we're using here, is optimized for chat.

In this example, inference performance is increased using the [FlashAttention](https://huggingface.co/docs/text-generation-inference/conceptual/flash_attention) backend.

These are the components of the Python solution being used here:

* **SitemapReader**: Asynchronous sitemap reader for the web (based on beautifulsoup). Reads pages from the web based on their sitemap.xml. Other data connectors are available (Snowflake, Twitter, Wikipedia, etc.). In this example, the site mapxml file is stored in an OCI bucket.
* **QdrantClient**: Python client for the Qdrant vector search engine.
* **HuggingFaceEmbeddings**: Sentence embeddings model object (from HuggingFace). Other options include Aleph Alpha, Cohere, MistralAI, SpaCy, etc.
* **VLLM**: Fast and easy-to-use LLM inference server.
* **Settings**: Bundle of commonly used resources used during the indexing and querying stage in a LlamaIndex pipeline/application. In this example, we use global configuration.
* **QdrantVectorStore**: Vector store where embeddings and docs are stored within a Qdrant collection.
* **StorageContext**: Utility container for storing nodes, indices, and vectors.
* **VectorStoreIndex**: Index built from the documents loaded in the Vector Store.

## Prerequisites & Docs

### Prerequisites

* An OCI tenancy with available credits to spend, and access to A10 GPU(s).
* A registered and verified HuggingFace account with a valid Access Token
* [Python 3.10](https://www.python.org/downloads/release/python-3100/)
* [Conda](https://conda.io/projects/conda/en/latest/user-guide/install/index.html)

### Docs

* [LlamaIndex](https://docs.llamaindex.ai/en/stable/)
* [LangChain](https://python.langchain.com/docs/get_started/introduction)
* [vLLM](https://docs.vllm.ai/en/latest/)
* [Qdrant](https://qdrant.tech/documentation/)

## Instance Creation

There are two approaches here: either install everything from scratch using an Ubuntu 22 LTS OS Image or use a marketplace image from NVIDIA, which will significantly reduce the overhead from installing all NVIDIA drivers and dependencies manually. However, these steps are also provided for those of you who want to know exactly what goes into your machine.

A boot volume of 200-250 GB is also recommended.

In this example, a single A10 GPU VM shape, codename `VM.GPU.A10.1`, is used. This is currently the smallest GPU shape available on OCI. With this configuration, it is recommended to limit the context length of the VLLM Model to **16384MB**, especially for larger models. To use the full context length, a dual A10 GPU, codename `VM.GPU.A10.2`, will be necessary.

> **Important**: If you've chosen to follow the guide with your NVIDIA GPU Cloud Machine Image (instead of a fresh Ubuntu image), you won't need to execute the steps found below in Chapter 2: Setup. These steps will be marked with an asterisk (*) at the beginning so you know which ones to **skip** and which ones to execute.

1. Create a GPU instance on OCI if you haven't already:

    ![GPU Creation in OCI](./files/img/create_gpu_accelerated.PNG)

2. Connect to the instance via SSH once the instance has been created:

    ```bash
    ssh -i <private.key> ubuntu@<public-ip>
    ```

where `private.key` is the SSH private key provided in the instance creation phase and `public-ip` is the instance Public IP address that can be found in the OCI Console.

Once we have SSH access to our instance, we can proceed with the setup.

## Setup

For the sake of libraries and package compatibility, is highly recommended to update the image packages, NVIDIA drivers, and CUDA versions.

1. Fetch, download, and install the packages of the distribution:

    ```bash
    sudo apt-get update && sudo apt-get upgrade -y
    ```

2. (*) Install the latest NVIDIA drivers.

    ```bash
    sudo apt install ubuntu-drivers-common
    sudo ubuntu-drivers install --gpgpu nvidia:570-server
    sudo apt install nvidia-utils-570-server
    sudo reboot
    ```

3. (*) We make sure that `nvidia-smi` is installed in our GPU instance:

    ```bash
    # run nvidia-smi
    nvidia-smi
    ```

4. (*) After installation, we need to add the CUDA path to the PATH environment variable, to allow for NVCC (NVIDIA CUDA Compiler) is able to find the right CUDA executable for parallelizing and running code:

    ```bash
    # first, we find the CUDA /bin folder:
    find / -type d -name cuda 2>/dev/null
    # e.g. /usr/local/cuda-12.4/bin in Ubuntu 22
    # then, we append it to the end of /home/$USER/.bashrc for consistency:
    echo "export PATH=/usr/local/cuda-12.4/bin:/usr/local/cuda-12.4/NsightCompute-2019.1${PATH:+:${PATH}}" >> /home/$USER/.bashrc
    echo "" >> /home/$USER/.bashrc # we also include a new line at the end.
    ```

5. We also added our HuggingFace Access Token to `.bashrc`, as it will be used in our Python file and retrieved from the environment:

    ```bash
    echo "export HF_TOKEN=<YOUR_HUGGINGFACE_TOKEN>" >> /home/ubuntu/.bashrc
    echo "" >> /home/ubuntu/.bashrc # we also include a new line at the end.
    ```

    > **Note**: if you're having issues during execution with the default Mistral 7B model, it might also be necessary to validate the Mistral model access on the HuggingFace website. If so, go [here](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2) and request permission to use the model.

6. Then, we prepare our Python environment. If it's a new machine where you don't have Conda installed, let's install Miniconda:

    ```bash
    curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
    chmod a+x Miniconda3-latest-Linux-x86_64.sh
    ./Miniconda3-latest-Linux-x86_64.sh
    ```

    > **Note**: remember to accept all defaults in the Miniconda installation script. After the script has been executed, restart your shell session and you'll already have conda installed in the OS.

7. Once the instance is running again, clone the repository and go to the right folder:

    ```bash
    git clone https://github.com/oracle-devrel/technology-engineering.git
    cd technology-engineering/cloud-infrastructure/ai-infra-gpu/ai-infrastructure/rag-langchain-vllm-mistral/
    git checkout rag-marketing-update # switch to this branch just in case new changes aren't synced with the main branch yet
    ```

8. Now, we install the necessary dependencies (in [requirements.txt](requirements.txt)) to run the environment:

    ```bash
    conda create -n rag python=3.10
    conda activate rag
    pip install packaging
    pip install -r requirements.txt
    # requirements.txt can be found in `technology-engineering/cloud-infrastructure/ai-infra-gpu/ai-infrastructure/rag-langchain-vllm-mistral/files`
    ```

9. Install `gcc` compiler to be able to build PyTorch (in vllm):

    ```bash
    sudo apt install -y gcc
    ```

10. Finally, reboot the instance and reconnect via SSH.

    ```bash
    ssh -i <private.key> ubuntu@<public-ip>
    sudo reboot
    ```

## Running the solution

1. You can run an editable file with parameters to test one query but first set a few more details, namely the `VLLM_WORKER_MULTIPROC_METHOD` environment variable and the `ipython` interactive terminal:

    ```bash
    export VLLM_WORKER_MULTIPROC_METHOD="spawn"
    conda install ipython
    ipython
    run rag-langchain-vllm-mistral.py
    ```

2. If you want to run a batch of queries against Mistral with the vLLM engine, execute the following script (containing an editable list of queries):

    ```bash
    python invoke_api.py
    ```

Having these scripts been benchmarked and achieved an average of 40-60 tokens/second *without FlashAttention enabled* (which means there's room for more performance) when retrieving from the RAG system and Mistral generations (with the compute shape mentioned previously).

The script will return the answer to the questions asked in the query.

## Alternative deployment

Alternatively, it is possible to deploy both components (qdrant client and vLLM server) remotely using Docker containers. This option can be useful in two situations:

* The engines are shared by multiple solutions for which data must segregated.
* The engines are deployed on instances with optimized configurations (GPU, RAM, CPU cores, etc.).

### Remote Qdrant client

Instead of:

```bash
client = QdrantClient(location=":memory:")
```

Use:

```bash
client = QdrantClient(host="localhost", port=6333)
```

To deploy the container:

```bash
docker pull qdrant/qdrant
docker run -p 6333:6333 qdrant/qdrant
```

### Remote vLLM server

Instead of:

```bash
from langchain_community.llms import VLLM

llm = VLLM(
    model="mistralai/Mistral-7B-v0.3",
    ...
    vllm_kwargs={
        ...
    },
)
```

Use:

```bash
from langchain_community.llms import VLLMOpenAI

llm = VLLMOpenAI(
    openai_api_key="EMPTY",
    openai_api_base="http://localhost:8000/v1",
    model_name="mistralai/Mistral-7B-v0.3",
    model_kwargs={
        ...
    },
)
```

To deploy the container, refer to this [tutorial](https://github.com/oracle-devrel/technology-engineering/tree/main/cloud-infrastructure/ai-infra-gpu/ai-infrastructure/vllm-mistral).

# Notes

The libraries used in this example are evolving quite fast. The Python script provided here might have to be updated in the near future to avoid Warnings and Errors.

# Contributing

This project is open source.  Please submit your contributions by forking this repository and submitting a pull request!  Oracle appreciates any contributions that are made by the open-source community.

# License
 
Copyright (c) 2025 Oracle and/or its affiliates.
 
Licensed under the Universal Permissive License (UPL), Version 1.0.
 
See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
