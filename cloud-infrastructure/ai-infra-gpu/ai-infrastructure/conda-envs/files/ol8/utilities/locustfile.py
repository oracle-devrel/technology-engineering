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
# Import the Locust dependencies
from locust import HttpUser, task

# Import general library from python
import os
import random

# Import lorem ipsum library to generate some random texts
from lorem_text import lorem

# Import dotenv to load the environments variables
from dotenv import load_dotenv
load_dotenv()

# Create a table with some lorem ipsum texts
messages = []

# Add 1000 random texts of 10 paragraphs each (simulate 1000 emails)
for i in range(1000):
    messages.append(lorem.paragraphs(10))

# Define the headers of the request. Token is stored as an environment variable here
headers = {
    "Authorization": "Bearer {os.getenv('TOKEN')}", "Content-Type": "application/json"}

class HelloWorldUser(HttpUser):
    # Definition of the first path where we do our post request
    @task
    def hello_world(self):
        # Define the body with the email choose randomly from the tab of all the emails
        body = {"model": "meta-llama/Llama-2-7b-chat-hf","prompt": "the following is a conversation with an AI research assistant. The assistant tone is technical and scientific. Human: Hello, who are you? AI: Greeting! I am an AI research assistant. How can I help you today? Human: Can you tell me about the creation of blackholes? AI:","max_tokens": 20,"temperature": 0}
        # Do the post request on the spam detection path
        self.client.post("/v1/completions",
                         headers=headers, json=body)
