# Streaming Chatbot
This asset is a Python-based chatbot that utilizes Oracle Cloud Infrastructure (OCI) Generative AI services to provide real-time, streaming responses. It is designed to interact with Cohere models available within OCI's Generative AI service. Users interested in leveraging other models, such as those from Meta or Google, can refer to the OCI Generative AI documentation for guidance on integrating these alternatives.

Reviewed: 22.10.2025

# When to use this asset?

This asset is suitable for developers and organizations aiming to integrate AI-driven conversational interfaces into their applications, particularly when:

- **Real-Time Interaction**: Immediate, dynamic responses are required in a chat interface.
- **Stateless Processing**: Each user input is processed independently, without context from prior exchanges.
- **Scalable AI Solutions**: Utilizing OCI's Generative AI services to handle varying loads and complex queries.

# How to use this asset?

To set up and run the `genai-streaming-chatbot`, follow these steps:

1. **Prerequisites**:

   - **Python Environment**: Ensure Python 3.6 or later is installed.
   - **OCI Account**: An active Oracle Cloud Infrastructure account with necessary permissions.
   - **API Key**: Generate and configure an API key for authentication.

2. **Installation**:

   - **Virtual Environment**: It's recommended to use a virtual environment to manage dependencies.

     ```bash
     pip install virtualenv
     virtualenv oci_env
     source oci_env/bin/activate
     ```

   - **Install OCI SDK**:

     ```bash
     pip install oci
     ```

3. **Configuration**:

   - **API Key Setup**: Generate an API key pair in the OCI Console and configure it in the `~/.oci/config` file. Ensure the private key has appropriate permissions.
   
   - **Configuration File**: Create a `config` file in the `~/.oci` directory with the necessary details:

     ```ini
     [DEFAULT]
     user=ocid1.user.oc1..<unique_ID>
     fingerprint=<your_fingerprint>
     key_file=~/.oci/oci_api_key.pem
     tenancy=ocid1.tenancy.oc1..<unique_ID>
     region=us-ashburn-1
     ```

4. **Running the Chatbot**:

   - **Script Setup**: Save the chatbot script to a file, e.g., `genai_streaming_chatbot.py`.

   - **Execute the Script**:

     ```bash
     python genai_streaming_chatbot.py
     ```

   - **Interaction**: Engage with the chatbot by typing messages. Type 'exit' to end the session.

**Note**: This chatbot processes each input independently and does not retain context from previous interactions. To implement a conversational chatbot that maintains context, you would need to manage the conversation history externally by storing previous user inputs and model responses, then appending this history to each new prompt.

# Useful Links

- [OCI Python SDK Documentation](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/pythonsdk.htm)
  - Comprehensive guide on using the OCI Python SDK.
- [OCI Generative AI Inference API Documentation](https://docs.oracle.com/en-us/iaas/tools/python/latest/api/generative_ai_inference.html)
  - Detailed information on the Generative AI Inference API.
- [OCI Generative AI Service](https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm)
  - Detailed information on OCI Generative AI Service 

# License

Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE.txt) for more details.