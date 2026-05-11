# How to Use Cline with OCI Generative AI Models via the OpenAI API

A practical guide for configuring Cline to call OCI Generative AI models through OCI's OpenAI-compatible API.

Cline is an AI coding assistant that works inside your IDE and can help with day-to-day development tasks such as explaining unfamiliar code, generating new files, refactoring existing logic, writing tests, debugging errors, and summarizing repository structure. By connecting Cline to OCI Generative AI, developers can use OCI-hosted models directly from their coding environment while keeping model access, deployment choices, and enterprise controls within Oracle Cloud Infrastructure.

This setup is useful when teams want AI-assisted development workflows that can use either on-demand OCI Generative AI models for quick setup or Dedicated AI Cluster (DAC)-hosted models for production-grade isolation, performance, and customization.

## Overview

This tutorial walks through configuring Cline to use OCI Generative AI models through the OCI OpenAI-compatible API.

The process involves:

1. Selecting an OCI Generative AI model
2. Choosing whether to use the model on demand or from a Dedicated AI Cluster (DAC)
3. Understanding the OCI OpenAI-compatible API endpoint URL
4. Creating an OCI Generative AI API key
5. Configuring Cline with the OCI OpenAI-compatible base URL, API key, and model ID
6. Testing the setup with an example prompt

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

The region is used in the OpenAI-compatible URL.

On-demand example:

```text
https://inference.generativeai.us-chicago-1.oci.oraclecloud.com/openai/v1
```

DAC Chat Completions example:

```text
https://inference.generativeai.us-chicago-1.oci.oraclecloud.com/openai/v1/chat/completions
```


### 2. Choose a Model

Select the OCI Generative AI model that you want Cline to use. OCI Generative AI models can be used either on demand or from a Dedicated AI Cluster (DAC). The Cline setup is different for each option, so choose the deployment path first.

#### On-Demand Models

On-demand models are shared, OCI-hosted models that are ready to call directly through the OpenAI-compatible API. This is the simplest setup for testing, prototyping, and lighter usage patterns.

Example OCI Model Names:

```text
xai.grok-code-fast-1
xai.grok-4.20-0309-reasoning
meta.llama-4-maverick-17b-128e-instruct-fp8
openai.gpt-oss-120b
google.gemini-2.5-flash
```

For on-demand models, the Cline **Model ID** is the OCI Model Name.

#### Dedicated AI Cluster (DAC)-Hosted Models

DAC-hosted models run on dedicated infrastructure in your tenancy. Use a DAC-hosted model when you need production-grade control over model hosting and inference. DACs provide several advantages:

- **Flexibility:** Import supported Hugging Face-format models from Hugging Face or Object Storage, test imported models with shorter commitments, choose fine-tuned or quantized versions, and right-size based on visible hardware specifications.
- **Isolation:** Run workloads on dedicated GPU resources inside your tenancy, which helps protect sensitive data, avoids shared-resource contention, and supports regulated workloads.
- **Predictable latency:** Dedicated infrastructure can provide more stable time-to-first-token and inference response times than shared model endpoints, especially for scaling production applications.
- **Fine-tuning support:** Host fine-tuned models alongside base models, run multiple fine-tuned models on a single cluster, and control model lifecycle and upgrade cadence.
- **Cost efficiency at scale:** For inference-heavy workloads, DACs can reduce effective price per token by keeping dedicated resources highly utilized and hosting multiple models on one cluster.
- **Deployment near data:** Deploy in supported OCI regions, including regulated regions where available, to support data residency, lower latency, and simpler security reviews.
- **Simplified management:** OCI manages the infrastructure while you manage model deployment, scaling, fine-tuning, and application integration.

Before configuring Cline for a DAC-hosted model, make sure the model endpoint is already created and active.

1. Open the OCI Console
2. Navigate to **Analytics & AI -> Generative AI**
3. Go to **Endpoints**
4. Confirm that the endpoint for your DAC-hosted model is **Active**
5. Keep note of the endpoint region and DAC endpoint OCID

For DAC-hosted models, the Cline **Model ID** is the DAC endpoint OCID.

```text
ocid1.generativeaiendpoint.<region>..<unique_id>
```

### 3. Understand the OCI OpenAI-Compatible API Endpoint URL

Cline uses a different OCI OpenAI-compatible endpoint format depending on whether the model is on demand or DAC-hosted.

For on-demand models, configure the base URL **without** `/chat/completions`:

```text
https://inference.generativeai.<region>.oci.oraclecloud.com/openai/v1
```

For DAC-hosted models, configure the full Chat Completions URL **with** `/chat/completions`:

```text
https://inference.generativeai.<region>.oci.oraclecloud.com/openai/v1/chat/completions
```

Keep note of the following values:

- Region
- OCI Model Name or DAC endpoint OCID
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

6. Add a description if needed
7. Configure key names and expiration dates
8. Click **Create**
9. Copy one of the generated key values

OCI Generative AI API keys are service-specific credentials and are different from OCI IAM API keys.

⚠️ Store the key securely. Do not commit it to GitHub or place it in source code.

### 5. Build the OCI OpenAI-Compatible URL

For on-demand models, use the following base URL format for Cline:

```text
https://inference.generativeai.<region>.oci.oraclecloud.com/openai/v1
```

Example for US Midwest Chicago:

```text
https://inference.generativeai.us-chicago-1.oci.oraclecloud.com/openai/v1
```

For DAC-hosted models, use the full Chat Completions URL shown in the DAC section.

Example for UK South London:

```text
https://inference.generativeai.uk-london-1.oci.oraclecloud.com/openai/v1/chat/completions
```


### 6. Configure Cline

Open VS Code or PyCharm and configure Cline:

1. Open the Cline panel
2. Click the **Settings** icon
3. Under **API Provider**, select:

```text
OpenAI Compatible
```

4. Set **Base URL** to your OCI URL.

For on-demand models:

```text
https://inference.generativeai.us-chicago-1.oci.oraclecloud.com/openai/v1
```

For DAC-hosted models:

```text
https://inference.generativeai.uk-london-1.oci.oraclecloud.com/openai/v1/chat/completions
```

5. Paste your OCI Generative AI API key into the **API Key** field
6. Set **Model ID** to your OCI Model Name or DAC endpoint OCID

Example:

```text
xai.grok-code-fast-1
```

For a DAC-hosted model, use the DAC endpoint OCID instead:

```text
ocid1.generativeaiendpoint.<region>..<unique_id>
```

7. Save the configuration

### 7. Test the Connection in Cline

Use a simple prompt first:

```text
Hello. Reply with one sentence confirming that the connection works.
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

- The model is available in the selected region
- The model supports OpenAI-compatible chat completion requests
- If using a DAC-hosted model, the OCI Generative AI endpoint is active and the Model ID field uses the DAC endpoint OCID

### Authorization Error

Check that:

- IAM policy has been added
- The API key OCID is correct in the policy
- The policy is in the correct tenancy or compartment scope
- You are using a Generative AI API key, not an OCI IAM API signing key

### Connection Error

Check that:

- The base URL uses the correct region
- For on-demand models, the URL ends with:

```text
/openai/v1
```

- For DAC-hosted models, the URL ends with:

```text
/openai/v1/chat/completions
```

- Your network can reach OCI public endpoints
- Private endpoints are reachable from your machine if using private networking

## Recommended Tests

Run the following tests in Cline:

- Short coding task
- Code explanation prompt
- Refactoring prompt
- Unit test generation prompt
- Repository summarization prompt

## Cleanup

If this was only a test setup:

1. Remove the API key from Cline
2. Revoke or deactivate the OCI Generative AI API key
3. If using a DAC-hosted model only for testing, delete the endpoint before deleting the Dedicated AI Cluster

## OCI Services Used

- **OCI Generative AI** - Model inference and endpoints
- **OCI Generative AI Dedicated AI Clusters** - Dedicated hosting for deployed models
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
