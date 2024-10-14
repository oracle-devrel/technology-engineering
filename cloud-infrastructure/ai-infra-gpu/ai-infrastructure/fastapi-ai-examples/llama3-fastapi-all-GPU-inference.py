#Copyright (c) 2024 Oracle and/or its affiliates.
#
#The Universal Permissive License (UPL), Version 1.0
#
#Subject to the condition set forth below, permission is hereby granted to any
#person obtaining a copy of this software, associated documentation and/or data
#(collectively the "Software"), free of charge and under any and all copyright
#rights in the Software, and any and all patent rights owned or freely
#licensable by each licensor hereunder covering either (i) the unmodified
#Software as contributed to or provided by such licensor, or (ii) the Larger
#Works (as defined below), to deal in both
#
#(a) the Software, and
#(b) any piece of software and/or hardware listed in the lrgrwrks.txt file if
#one is included with the Software (each a "Larger Work" to which the Software
#is contributed by such licensors),
#
#without restriction, including without limitation the rights to copy, create
#derivative works of, display, perform, and distribute the Software and make,
#use, sell, offer for sale, import, export, have made, and have sold the
#Software and the Larger Work(s), and to sublicense the foregoing rights on
#either these or other terms.
#
#This license is subject to the following condition:
#The above copyright notice and either this complete permission notice or at
#a minimum a reference to the UPL must be included in all copies or
#substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

import time
import torch
import pynvml
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer

app = FastAPI()

def print_vram_usage():
    """Prints the VRAM usage of the GPU."""
    pynvml.nvmlInit()
    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
    info = pynvml.nvmlDeviceGetMemoryInfo(handle)
    print(f"Total VRAM: {info.total / 1024**2:.2f} MB")
    print(f"Free VRAM: {info.free / 1024**2:.2f} MB")
    print(f"Used VRAM: {info.used / 1024**2:.2f} MB")

# Define the start time for the total initialization
start_time = time.time()

print("Loading tokenizer and model...")

# Load the tokenizer and model from the local directory
model_name = "/share/app/llama3-8b-instruct/"

# Use torch.bfloat16 to reduce memory usage
model_loading_start_time = time.time()
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.bfloat16
)
print(f"Model loaded in {time.time() - model_loading_start_time:.2f} seconds.")
print_vram_usage()

tokenizer_loading_start_time = time.time()
tokenizer = AutoTokenizer.from_pretrained(model_name)
print(f"Tokenizer loaded in {time.time() - tokenizer_loading_start_time:.2f} seconds.")
print_vram_usage()

# Use Data Parallel to utilize multiple GPUs
if torch.cuda.device_count() > 1:
    print(f"Using {torch.cuda.device_count()} GPUs")
    model = torch.nn.DataParallel(model)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

print(f"Model moved to GPUs in {time.time() - model_loading_start_time:.2f} seconds.")
print_vram_usage()

class InferenceRequest(BaseModel):
    input_text: str

@app.post("/infer")
async def infer(request: InferenceRequest):
    try:
        inference_start_time = time.time()

        # Tokenize input
        inputs = tokenizer(request.input_text, return_tensors="pt")
        inputs = {key: value.to(device) for key, value in inputs.items()}

        # Inference
        with torch.no_grad():
            outputs = model.module.generate(**inputs) if torch.cuda.device_count() > 1 else model.generate(**inputs)

        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

        print(f"Generated text: {generated_text}")
        print(f"Inference completed in {time.time() - inference_start_time:.2f} seconds.")

        return {"generated_text": generated_text}
    except Exception as e:
        print(f"Error during inference: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print(f"Total initialization time: {time.time() - start_time:.2f} seconds.")
    uvicorn.run(app, host="0.0.0.0", port=8000)
