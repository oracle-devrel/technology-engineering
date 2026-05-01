# How to Use Cline with OCI Generative AI Models via the OpenAI API

A practical guide for configuring Cline to call OCI Generative AI models through OCI's OpenAI-compatible API.

## Overview

This tutorial walks through configuring Cline to use OCI Generative AI models through the OCI OpenAI-compatible API.

The process involves:

1. Selecting an OCI Generative AI model
2. Understanding the OCI OpenAI-compatible API endpoint URL
3. Creating an OCI Generative AI API key
4. Configuring Cline with the OCI OpenAI-compatible base URL, API key, and model ID
5. Testing the setup with an example prompt

OCI provides OpenAI-compatible APIs for model inference, including Chat Completions and Responses. This tutorial uses the OCI Generative AI OpenAI-compatible API documented here:

https://docs.oracle.com/en-us/iaas/Content/generative-ai/openai-compatible-api.htm

Cline can connect to this API by using the **OpenAI Compatible** provider configuration.

## Prerequisites

Before starting, ensure you have:

- Access to Oracle Cloud Infrastructure
- Access to OCI Generative AI
- A compartment where you can create Generative AI resources
- Cline installed in VS Code or PyCharm

## Steps

### 1. Select a Supported OCI Region

Choose a region where OCI Generative AI and your target model are available.

Example regions include:

- `us-chicago-1`
- `us-ashburn-1`
- `uk-london-1`
- `eu-frankfurt-1`

The region is used in the OpenAI-compatible base URL.

Example:

```text
https://inference.generativeai.us-chicago-1.oci.oraclecloud.com/openai/v1
```

**Important:** Create the OCI Generative AI API key in the same region where you plan to use the model.

### 2. Choose a Model

Select the OCI Generative AI model that you want Cline to use.

Example model IDs:

```text
xai.grok-code-fast-1
xai.grok-4.20-0309-reasoning
meta.llama-4-maverick-17b-128e-instruct-fp8
openai.gpt-oss-120b
google.gemini-2.5-flash
```

### 3. Understand the OCI OpenAI-Compatible API Endpoint URL

All calls from Cline go through the OCI OpenAI-compatible API endpoint URL:

```text
https://inference.generativeai.<region>.oci.oraclecloud.com/openai/v1
```

This base URL is the endpoint you configure in Cline.

Keep note of the following values:

- Region
- Model ID
- Compartment

### 4. Create an OCI Generative AI API Key

1. In the OCI Console, select the same region as your model
2. Navigate to **Analytics & AI -> Generative AI**
3. Select **API keys**
4. Click **Create API key**
5. Enter a name, for example:

```text
cline-genai-key
```

6. Optionally add a description
7. Configure key names and expiration dates
8. Click **Create**
9. Copy one of the generated key values immediately

OCI Generative AI API keys are service-specific credentials and are different from OCI IAM API keys.

**Important:** Store the key securely. Do not commit it to GitHub or place it in source code.

### 5. Build the OCI OpenAI-Compatible Base URL

Use the following base URL format for Cline:

```text
https://inference.generativeai.<region>.oci.oraclecloud.com/openai/v1
```

Example for US Midwest Chicago:

```text
https://inference.generativeai.us-chicago-1.oci.oraclecloud.com/openai/v1
```


### 6. Configure Cline

Open VS Code or PyCharm and configure Cline:

1. Open the Cline panel
2. Click the **Settings** icon
3. Under **API Provider**, select:

```text
OpenAI Compatible
```

4. Set **Base URL** to your OCI base URL:

```text
https://inference.generativeai.us-chicago-1.oci.oraclecloud.com/openai/v1
```

5. Paste your OCI Generative AI API key into the **API Key** field
6. Set **Model ID** to your OCI model ID

Example:

```text
xai.grok-code-fast-1
```

7. Save the configuration

### 7. Test the Connection in Cline

Use a simple prompt first:

```text
Write a one-sentence commit message for a change that adds OCI Generative AI support to a Cline tutorial.
```

If the setup is correct, Cline should return a normal response from the OCI-hosted model.

### 8. Example Coding Prompt

After the basic test succeeds, try a Cline-style development prompt:

```text
Create a small Python script that reads a text file, counts the number of lines, words, and characters, and prints the results in a clean table. Include basic error handling for missing files.
```

You can also test repository-aware behavior:

```text
Review this project and explain the main application structure. Then suggest three small improvements that would make the code easier to maintain.
```

## Troubleshooting

### Invalid API Key

Check that:

- The key was copied correctly
- The key is active
- The key has not expired
- The key was created in the same region as the model

### Model Not Found

Check that:

- The model ID is correct
- The model is available in the selected region
- The model supports OpenAI-compatible chat completion requests

### Authorization Error

Check that:

- IAM policy has been added
- The API key OCID is correct in the policy
- The policy is in the correct tenancy or compartment scope
- You are using a Generative AI API key, not an OCI IAM API signing key

### Connection Error

Check that:

- The base URL uses the correct region
- The URL ends with:

```text
/openai/v1
```

- Your network can reach OCI public endpoints
- Private endpoints are reachable from your machine if using private networking

## Recommended Tests

Run the following tests in Cline:

- Simple math prompt
- Short coding task
- Code explanation prompt
- Refactoring prompt
- Unit test generation prompt
- Repository summarization prompt

## Cleanup

If this was only a test setup:

1. Remove the API key from Cline
2. Revoke or deactivate the OCI Generative AI API key

## OCI Services Used

- **OCI Generative AI** - Model inference
- **OCI IAM** - Policies and authorization
- **OCI Generative AI API Keys** - API key authentication
- **Cline** - AI coding assistant in VS Code or PyCharm

## References

- [OCI Generative AI Documentation](https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm)
- [OCI Generative AI OpenAI-Compatible API](https://docs.oracle.com/en-us/iaas/Content/generative-ai/openai-compatible-api.htm)
- [OCI Generative AI API Keys](https://docs.oracle.com/en-us/iaas/Content/generative-ai/api-keys.htm)
- [Cline OpenAI Compatible Provider](https://docs.cline.bot/provider-config/openai-compatible)

## License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE.txt) for more details.
