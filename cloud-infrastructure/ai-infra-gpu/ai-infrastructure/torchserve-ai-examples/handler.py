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

import logging
import json
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

logger = logging.getLogger(__name__)

class SimpleTextGenerationHandler:
    def __init__(self):
        self.initialized = False

    def initialize(self, context):
        logger.info("YR: model initialization")
        self.model_dir = context.system_properties.get("model_dir")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        logger.info("YR: loading model")
        # Load the tokenizer and model from the local directory
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_dir,
            torch_dtype=torch.bfloat16
        ).to(self.device)

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_dir)

        logger.info("YR: setting pipeline")
        # Use the Hugging Face pipeline for text generation
        self.pipe = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            device=0  # Use GPU
        )

        self.initialized = True

    def preprocess(self, data):
        input_text = data[0].get("body")
        return input_text.decode('utf-8') if isinstance(input_text, (bytes, bytearray)) else input_text

    def inference(self, input_text):
        try:
            result = self.pipe(input_text)[0]['generated_text']
            return [result]
        except Exception as e:
            raise RuntimeError(f"Error during inference: {str(e)}")

    def postprocess(self, inference_output):
        return [json.dumps({"generated_text": inference_output[0]})]

_service = SimpleTextGenerationHandler()

def handle(data, context):
    if not _service.initialized:
        _service.initialize(context)
    if data is None:
        return None

    data = _service.preprocess(data)
    predictions = _service.inference(data)
    return _service.postprocess(predictions)
