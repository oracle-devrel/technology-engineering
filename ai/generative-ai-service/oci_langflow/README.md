# Integration of OCI Generative AI in Langflow

[![License: UPL](https://img.shields.io/badge/license-UPL-green)](https://img.shields.io/badge/license-UPL-green) [![Quality gate](https://sonarcloud.io/api/project_badges/quality_gate?project=oracle-devrel_test)](https://sonarcloud.io/dashboard?id=oracle-devrel_test)

## Introduction
This repository contains the code for a prototype of the integration of OCI Generative AI in Langflow

Reviewed: 25.06.2025

## Components for Retrieval-Augmented Generation (RAG)
In this release (jan 2025), we have included the essential components required to build a robust Retrieval-Augmented Generation (RAG) solution:

1. OCI Embeddings Model
Based on Cohere, this component generates embeddings for your data, enabling effective search and retrieval.

2. OCI Chat Model
Powered by Meta or Cohere models, this component handles conversational AI tasks for natural and engaging user interactions.

3. OCI Vector Store
Built on Oracle Database 23AI, this component provides a highly efficient and scalable vector store for managing and querying embeddings.

## Langflow setup
To setup an environment with Langflow this is the recommended sequence of steps:

1. Create and activate a "conda environment" using Python 3.11
```
conda create -n oci_langflow python==3.11
conda activate oci_langflow
```
2. Install the tool [uv](https://docs.astral.sh/uv/getting-started/) in this environment, using pip
3. Install Langflow using uv. Follow the instructions [here](https://docs.langflow.org/get-started-installation)
```
uv pip install langflow
```
4. Install oci Python sdk and update langchain-community
```
pip install oci -U
```

## Setup your environment for OCI
* Clone the github repository
```
git clone https://github.com/luigisaetta/oci_langflow.git
```
* modify the `set_env.sh` file. Change the env variable `LANGFLOW_COMPONENTS_PATH` to point your local **oci_custom** directory
* execute the following command to set the environment variables:
```
source ./set_env.sh
``` 
* start langflow using the command: 
```
uv run langflow run
```

## Notes
### Setup: do not install Langflow using directly pip, use uv. 
There are many components and pip really struggle to manage them correctly.
As a result the installation is really slow. 
The preferred way to do (as suggested also in the official documentation) is to use
uv.

### The **Philosophy**
The main idea is to provide the code as an easy way that can be used from people. 
Then, if they want, they can add all the details they really need.
Therefore, for example, wrappers expose only the mandatory parameters that needs to be customized. 
For the remaining:
1. I have followed Langchain defaults.
2. The code is simple and easy to be customized.

## Security
Please consult the [security guide](./SECURITY.md) for our responsible security
vulnerability disclosure process.

## License
Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](LICENSE.txt) for more details.

ORACLE AND ITS AFFILIATES DO NOT PROVIDE ANY WARRANTY WHATSOEVER, EXPRESS OR IMPLIED, FOR ANY SOFTWARE, MATERIAL OR CONTENT OF ANY KIND CONTAINED OR PRODUCED WITHIN THIS REPOSITORY, AND IN PARTICULAR SPECIFICALLY DISCLAIM ANY AND ALL IMPLIED WARRANTIES OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY, AND FITNESS FOR A PARTICULAR PURPOSE.  FURTHERMORE, ORACLE AND ITS AFFILIATES DO NOT REPRESENT THAT ANY CUSTOMARY SECURITY REVIEW HAS BEEN PERFORMED WITH RESPECT TO ANY SOFTWARE, MATERIAL OR CONTENT CONTAINED OR PRODUCED WITHIN THIS REPOSITORY. IN ADDITION, AND WITHOUT LIMITING THE FOREGOING, THIRD PARTIES MAY HAVE POSTED SOFTWARE, MATERIAL OR CONTENT TO THIS REPOSITORY WITHOUT ANY REVIEW. USE AT YOUR OWN RISK. 
