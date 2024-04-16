from vllm import LLM

# Replace the model name with the one you want to use:
# Mixtral simple: mistralai/Mixtral-8x7B-v0.1
# Mixtral instruct: mistralai/Mixtral-8x7B-Instruct-v0.1
# Mistral 7B simple: mistralai/Mistral-7B-v0.1
# Mistral 7B instruct: mistralai/Mistral-7B-Instruct-v0.1
# LLaMA 2 70B: meta-llama/Llama-2-70b-hf



llm = LLM("meta-llama/Llama-2-7b-chat-hf", tensor_parallel_size=1, max_model_len=4096)

print(llm.generate("What is batch inference?"))
