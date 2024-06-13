# Conda Environments

In this repository, you can find a collection of ready-to-use conda environments.

Reviewed 23.05.2024

# When to use this asset?
 
ML projects require final users to experiment with a lot of different tools that interact in a complex ecosystem. Conva environments greatly simplify the management of such ecosystems and the dependencies between the tools.  In this repo we provide Conda Environment templates that have been tested on OCI shapes and easily recreate ML environments.

# How to use this asset?
 
The templates are divided per OS version, so they should be applied to the same OS.

To create an environment

```conda env create -f  environment.yml```

## Pytorch

You can check that pytorch works with GPUs with the command

```run_cifar```

which will run a test training:

```text
Using pytorch version: 2.2.1+cu121
Using: NVIDIA A10
Downloading https://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz to ./data/cifar-10-python.tar.gz
100%|███████████████████████████████████████████████████████████████████████████████████████| 170498071/170498071 [00:05<00:00, 33540043.06it/s]
Extracting ./data/cifar-10-python.tar.gz to ./data
/home/opc/anaconda3/envs/pytorch/lib/python3.9/site-packages/torchvision/models/_utils.py:208: UserWarning: The parameter 'pretrained' is deprecated since 0.13 and may be removed in the future, please use 'weights' instead.
  warnings.warn(
/home/opc/anaconda3/envs/pytorch/lib/python3.9/site-packages/torchvision/models/_utils.py:223: UserWarning: Arguments other than a weight enum or `None` for 'weights' are deprecated since 0.13 and may be removed in the future. The current behavior is equivalent to passing `weights=ResNet50_Weights.IMAGENET1K_V1`. You can also use `weights=ResNet50_Weights.DEFAULT` to get the most up-to-date weights.
  warnings.warn(msg)
26-03-2024-10-13
[1,    20] loss: 1.745
[1,    40] loss: 0.989
[1,    60] loss: 0.765
[1,    80] loss: 0.671
[2,    20] loss: 0.424
...
```

## vLLM

Login into Hugging Face HUB with
```huggingface-cli login```

You can then start an Open AI compatible API running Llama2 on http://localhost:8000

```python -m vllm.entrypoints.openai.api_server --model meta-llama/Llama-2-7b-chat-hf```

It can be tested with `curl`.

```bash
      curl http://localhost:8000/v1/completions     -H "Content-Type: application/json"     -d \
   '{
        "model": "meta-llama/Llama-2-7b-chat-hf",
        "prompt": "he following is a conversation with an AI research assistant. The assistant tone is technical and scientific. Human: Hello, who are you? AI: Greeting! I am an AI     research assistant. How can I help you today? Human: Can you tell me about the creation of blackholes? AI",
        "max_tokens": 30,
        "temperature": 0
    }'
```

## Load test with Locust

1. Execute the following command in the utilities folder

  ```bash
  locust --host  httry utilitiesocalhost:8000
  ```

This will create a web port on `http://localhost:8089`.

# License
 
Copyright (c) 2024 Oracle and/or its affiliates.
 
Licensed under the Universal Permissive License (UPL), Version 1.0.
 
See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.