# Unlisted Model Deployment in OCI Generative AI

A comprehensive guide for deploying Hugging Face models on Oracle Cloud Infrastructure (OCI) Generative AI using Imported Models and Dedicated AI Clusters (DAC).

## Overview

This tutorial walks through deploying a Hugging Face model on OCI Generative AI using Imported Models and a Dedicated AI Cluster (DAC). The process involves:

1. Authenticating with Hugging Face
2. Downloading the model
3. Uploading it to Object Storage
4. Creating an Imported Model
5. Creating a Dedicated AI Cluster (DAC)
6. Deploying an endpoint
7. Testing the model
8. Cleaning up resources

## Prerequisites

Before starting, ensure you have:

- OCI CLI configured
- Hugging Face account
- Hugging Face token (Read access)
- Access to the model (license accepted if required)
- Object Storage bucket
- Permissions set for GPU capacity (e.g., H100)

## Steps

### 1. Hugging Face Authentication

Create a token from [Hugging Face Settings](https://huggingface.co/settings/tokens).

Login using the CLI:
```bash
hf auth login
```

Verify authentication:
```bash
hf auth whoami
```

### 2. Download the Model

Download the model locally:
```bash
hf download <model-name> --local-dir <model-folder> --force-download
```

Example:
```bash
hf download google/medgemma-27b-text-it --local-dir medgemma-27b --force-download
```

### 3. Verify Local Folder Structure

Check the downloaded files:
```bash
ls <model-folder>
```

Example:
```bash
ls medgemma-27b
```

You should see files like:
- `config.json`
- `tokenizer.json`
- `tokenizer_config.json`
- `model-00001-of-xxxxx.safetensors`
- `model-00002-of-xxxxx.safetensors`

**Important:** All files must be inside the model folder.

### 4. Create Object Storage Bucket (if needed)

```bash
oci os bucket create --compartment-id <compartment_ocid> --name <bucket-name>
```

Example:
```bash
oci os bucket create --compartment-id ocid1.compartment... --name HuggingFaceModels
```

### 5. Upload Model to Object Storage

Upload using an object prefix:
```bash
oci os object bulk-upload --bucket-name <bucket-name> --src-dir <model-folder> --object-prefix <model-folder>/ --overwrite
```

Example:
```bash
oci os object bulk-upload --bucket-name HuggingFaceModels --src-dir medgemma-27b --object-prefix medgemma-27b/ --overwrite
```

**Important:** OCI does not use real folders. The object prefix defines the model directory.

### 6. Verify Upload

```bash
oci os object list --bucket-name <bucket-name>
```

Example:
```bash
oci os object list --bucket-name HuggingFaceModels
```

You should see objects like:
- `<model-folder>/config.json`
- `<model-folder>/tokenizer.json`
- `<model-folder>/model-xxxxx.safetensors`

### 7. Create Imported Model

1. Navigate to **Generative AI → Imported Models** in the OCI Console
2. Click **Create Imported Model**

**Basic Configuration**
- Name: model name (e.g., `medgemma-27b`)
- Description: optional
- Click **Next**

**Object Storage Configuration**
- Data source type: **Object Storage**
- Region: where your bucket is located
- Compartment: where your bucket is located
- Bucket name: your bucket
- Model artifact directory: `<model-folder>/` (e.g., `medgemma-27b/`)

**Important:** This must point to the root folder containing model files.

- Click **Next**

**Create Model**
- Review configuration
- Click **Create**

### 8. Create Dedicated AI Cluster (DAC)

1. Navigate to **Generative AI → Dedicated AI Clusters** in the OCI Console
2. Click **Create Dedicated AI Cluster**

**Basic Configuration**
- Compartment: select your compartment
- Name: model name (e.g., `medgemma-27b`)
- Description: optional

**Cluster Type**
- Select: **Hosting**

**Base Model**
- Select: model name (e.g., `medgemma-27b-1`)

**Compute Configuration**
- Generic unit shape: put necessary shape (e.g., `H100_X1`)
- Model replica: 1

**Commitment**
- Check: "I commit to 1 hour of commitment for this hosting dedicated AI cluster..."

**Create Cluster**
- Click **Create**
- Wait until status is **Active**

### 9. Create Endpoint

1. Navigate to **Generative AI → Endpoints** in the OCI Console
2. Click **Create Endpoint**
3. Select your imported model
4. Select your DAC
5. Click **Deploy**
6. Wait until endpoint is **Active**

### 10. Test the Model

In the playground, you should see the endpoint you created which you can use to test (unless it's a multimodal model).
Alternatively, you can use the python snippet in this repository to call the model locally.

## Testing the Deployed Model

You can test your deployed model using the provided example script:

1. Update the `config.py` file with your actual values:
   - `COMPARTMENT_ID`: Your compartment OCID
   - `ENDPOINT`: Your generative AI inference endpoint URL
   - `ENDPOINT_ID`: Your endpoint OCID

2. Run the test script:
   ```bash
   python oci_genai_chat_example.py
   ```

The script will send a chat request to your deployed model and display the response.

### 11. Recommended Tests

Run the following tests:
- Simple prompt
- Summarization
- Structured output (JSON)
- Long input (~5K tokens)
- Near max context

### 12. Cleanup (Important)

1. Delete endpoints first
2. Then delete DAC:
   - Go to **Dedicated AI Clusters**
   - Delete the cluster

**Important:** Endpoint must be deleted before DAC.


## OCI Services Used

- **OCI Generative AI** - Imported Models and Dedicated AI Clusters
- **OCI Object Storage** - Model artifact storage
- **OCI Identity and Access Management** - Authentication and authorization

## References

- [OCI Generative AI Documentation](https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm)
- [Hugging Face Model Hub](https://huggingface.co/models)
- [OCI CLI Documentation](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/)

## License

Copyright (c) 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE.txt) for more details.