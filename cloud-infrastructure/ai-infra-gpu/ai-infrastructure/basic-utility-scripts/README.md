# Basic Utility Scripts

This page contains useful scripts for basic actions, such as checking CUDA health or downloading AI model.

Reviewed: 08.06.2024

# When to use this asset?

When you are planning to install and run a pretrained AI model from Huggingface on an OCI GPU instance.
The examples use LLAMA3, for illustrative purposes, and Torch library.

# How to use this asset?

1. Run `pip install -r requirements.txt`
2. Pick a script from this directory based on its self-descriptive name, and review its content before using. Some scripts contains placeholders such as YOUR TOKEN to be replaced by Huggingface access token
3. Run the script. As some scripts may need to download an AI model, its first invocation may take time

## Prerequisites & Docs

### Prerequisites

* An OCI GPU instance
* A Huggingface account with a valid Auth Token

# License
 
Copyright (c) 2024 Oracle and/or its affiliates.
 
Licensed under the Universal Permissive License (UPL), Version 1.0.
 
See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
