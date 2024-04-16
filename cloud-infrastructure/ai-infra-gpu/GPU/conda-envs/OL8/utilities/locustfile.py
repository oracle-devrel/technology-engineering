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
