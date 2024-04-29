# Overview

This repository is a variant of the Retrieval Augmented Generation (RAG) tutorial available [here](https://github.com/oracle-devrel/technology-engineering/tree/main/ai-and-app-modernisation/ai-services/generative-ai-service/rag-genai/files). Instead of the OCI GenAI Service, it uses a local deployment of Mistral 7B Instruct v0.2 using a vLLM inference server powered by a NVIDIA A10 GPU.

# Requirements

* An OCI tenancy with A10 GPU quota.
* An HuggingFace account with a valid Access Token

# Libraries

* **LlamaIndex**: a data framework for LLM-based applications which benefit from context augmentation.
* **LangChain**: a framework for developing applications powered by large language models.
* **vLLM**: a fast and easy-to-use library for LLM inference and serving.
* **Qdrant**: a vector similarity search engine.

# Mistral LLM

[Mistral.ai](https://mistral.ai/) is a French AI startup that develop Large Language Models (LLMs). Mistral 7B Instruct is a small yet powerful open model that supports English and code. The Instruct version is optimized for chat. In this example, inference performance is increased using the [FlashAttention](https://huggingface.co/docs/text-generation-inference/conceptual/flash_attention) backend.

# Instance Creation

In this example a single A10 GPU VM shape, codename VM.GPU.A10.1, is used. This is currently the smallest GPU shape available on OCI. With this configuration, it is necessary to limit the VLLM Model context length option to 16384 because the memory is unsufficient. To use the full context length, a dual A10 GPU, codename VM.GPU.A10.2, will be necessary.\
The image is the NVIDIA GPU Cloud Machine image from the OCI marketplace.\
A boot volume of 200 GB is also recommended.\
Create the the instance and connect to it once it is running.
```
ssh -i public.key ubuntu@public.ip
```
where `public.key` is the ssh public key provided in the instance creation phase and `public.ip` is the instance Public IP address that can be found in the OCI Console.

# Walkthrough

Along this walkthrough you will be guided through the different steps of the deployment, from configuring the environment to running the different components of the RAG solution.

## Update packages and drivers

For the sake of libraries and packages comptibility, is highly recommended to update the image packages, NVIDIA drivers and CUDA versions. First fetch, download and install the packages of the distribution (optional).
```
sudo apt-get update && sudo apt-get upgrade -y

```
Then remove the current NVIDIA packages and replace it with the following versions.

```
sudo apt purge nvidia* libnvidia* -y
sudo apt-get install -y cuda-drivers-545
sudo apt-get install -y nvidia-kernel-open-545
sudo apt-get install -y cuda-toolkit-12-3
```
Finally reboot the instance.
```
sudo reboot
```

## Configure environment

Once the instance is running again, clone the repository and go to the right folder:
```
git clone https://github.com/oracle-devrel/technology-engineering.git
cd technology-engineering/cloud-infrastructure/ai-infra-gpu/AI\ Infrastructure/rag-langchain-vllm-mistral/
```
Then update conda and create a virtual environment with all the required packages:
```
conda update -n base -c conda-forge conda
conda env create -f environment.yml
```
Then activate the environment.
```
conda activate rag
```

## Deploy the framework

### Framework components

* **SitemapReader**: Asynchronous sitemap reader for web (based on beautifulsoup). Reads pages from the web based on their sitemap.xml. Other data connectors are available (Snowflake, Twitter, Wikipedia, etc.). In this example the site mapxml file is stored in an OCI bucket.
* **QdrantClient**: Python client for the Qdrant vector search engine.
* **SentenceTransformerEmbeddings**: Sentence embeddings model object (from HuggingFace). Other options include Aleph Alpha, Cohere, MistralAI, SpaCy, etc.
* **VLLM**: Fast and easy-to-use LLM inference server.
* **Settings**: Bundle of commonly used resources used during the indexing and querying stage in a LlamaIndex pipeline/application. In this example we use global configuration.
* **QdrantVectorStore**: Vector store where embeddings and docs are stored within a Qdrant collection.
* **StorageContext**: Utility container for storing nodes, indices, and vectors.
* **VectorStoreIndex**: Index built from the documents loaded in the Vector Store.

### Running the solution

The python script creates an all-in-one framework with local instances of the Qdrant vector similarity search engine and the vLLM inference server. First set your HuggingFace Access Token as an environment variable:
```
export HF_TOKEN=your-hf-token
```
where `your-hf-token` is you personal Access Token. It might also be necessary to validate the Mistral model access on the HuggingFace website. Then run the python script:
```
python rag-langchain-vllm-mistral.py
```
The script will return the answer to the question asked in the query.

## Alternative deployment

Alternatively it is possible to deploy these two components remotely using Docker containers. This option can be useful in two situations:
* The engines are shared by multiple solutions for which data must segregated.
* The engines are deployed on instances with optimized configurations (GPU, RAM, CPU cores, etc.).

### Remote Qdrant client

Instead of:
```
client = QdrantClient(location=":memory:")
```
Use:
```
client = QdrantClient(host="localhost", port=6333)
```

To deploy the container:
```
docker pull qdrant/qdrant
docker run -p 6333:6333 qdrant/qdrant
```

### Remote vLLM server

Instead of:
```
from langchain_community.llms import VLLM

llm = VLLM(
    model="mistralai/Mistral-7B-v0.1",
    ...
    vllm_kwargs={
        ...
    },
)
```
Use:
```
from langchain_community.llms import VLLMOpenAI

llm = VLLMOpenAI(
    openai_api_key="EMPTY",
    openai_api_base="http://localhost:8000/v1",
    model_name="mistralai/Mistral-7B-v0.1",
    model_kwargs={
        ...
    },
)
```
To deploy the container, refer to this [tutorial](https://github.com/oracle-devrel/technology-engineering/tree/main/cloud-infrastructure/ai-infra-gpu/AI%20Infrastructure/vllm-mistral).

# Notes

The libraries used in this example are evolving quite fast. The python script provided here might have to be updated in a near future to avoid Warnings and Errors.

# Documentation

* [LlamaIndex](https://docs.llamaindex.ai/en/stable/)
* [LangChain](https://python.langchain.com/docs/get_started/introduction)
* [vLLM](https://docs.vllm.ai/en/latest/)
* [Qdrant](https://qdrant.tech/documentation/)