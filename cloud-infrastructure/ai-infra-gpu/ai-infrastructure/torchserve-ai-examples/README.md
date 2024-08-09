### How to Configure AI model as HTTP Endpoint Using TorchServe

1. Download and test the model using download script ../basic-utility-scripts/download\_and\_test\_huggingface\_model.py

2. Go to the folder where you downloaded model is located, for the sake of example, it'll be /share/app/llama3-8b-instruct folder, and do the following as a regular user.

3. Put handler.py to this folder. The handler is a python file that implements semantics of inference; in particular, it implements methods 'preprocess', 'inference', 'postprocess', and an umbrella method 'handle' that invokes previous methods sequentially.

4. Put config.properties to this folder. This file name is fixed and recognized by TorchServe. This file defines performance & scalability characteristics of a given model, such as batch size and number of 'workers', that is, processes, associated with the inference of a given model.

5. Archive the model along with all required file into .mar file recognizable by TorchServe using this command:

torch-model-archiver --model-name llama3-8b-instruct --version 1.0 --serialized-file /share/app/llama3-8b-instruct/model-00001-of-00004.safetensors --handler /share/app/llama3-8b-instruct/handler.py --extra-files "/share/app/llama3-8b-instruct/config.json,/share/app/llama3-8b-instruct/generation\_config.json,/share/app/llama3-8b-instruct/model-00002-of-00004.safetensors,/share/app/llama3-8b-instruct/model-00003-of-00004.safetensors,/share/app/llama3-8b-instruct/model-00004-of-00004.safetensors,/share/app/llama3-8b-instruct/model.safetensors.index.json,/share/app/llama3-8b-instruct/tokenizer.json,/share/app/llama3-8b-instruct/tokenizer\_config.json,/share/app/llama3-8b-instruct/special\_tokens\_map.json" --export-path model\_store --force

6. Start TorchServe:

torchserve --start --ts-config /share/app/llama3-8b-instruct/config.properties --model-store model\_store --models llama3-8b-instruct.mar

7. You can use the following basic commands with the running TorchServe:
    * How to stop TorchServe: torchserve --stop
    * How to send inference request: curl -X POST http://127.0.0.1:8080/predictions/llama3-8b-instruct -T input\_example.json
    * How to directly pass payload to inference request: curl -X POST http://localhost:8080/predictions/llama -H "Content-Type: application/json" -d '{ "input": "Hello, who are you?" }'
    * How to monitor GPU utilization during inference processing: watch -n 1 nvidia-smi
    * How to check if TorchServe is healthy: curl http://localhost:8080/ping
    * How to check the list of models exposed via TorchServe: curl http://localhost:8081/models