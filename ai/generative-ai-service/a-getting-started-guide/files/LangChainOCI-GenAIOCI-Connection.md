## Integrating LangChain with OCI Generative AI
We're excited to announce the official release of `langchain-oci`, the dedicated LangChain integration package for Oracle Cloud Infrastructure services.

Install the LangChain OCI package with the following command:

`pip install -U langchain-oci`

**Note:** The OCI integrations that were available in the `langchain-community` are now deprecated. All future development, bug fixes, and feature enhancements will be hosted in the new dedicated repository. We recommend that you migrate to `langchain-oci` to ensure that you receive the following benefits:

* Latest features and improvements
* Security updates and bug fixes
* Dedicated support and documentation
* Performance optimizations

To learn about OCI Generative AI's integration with LangChain, see the [Generative AI documentation](https://docs.oracle.com/iaas/Content/generative-ai/langchain.htm).

### Prerequisites
1. **OCI Account and Permissions:**
   * Create or use an active OCI tenancy with Generative AI enabled.
   * Set up IAM policies: Grant your user/group access to `generative-ai-family` in a sandbox compartment (e.g., `allow group <group-name> to manage generative-ai-family in compartment <compartment-name>`).
   * Gather: Compartment OCID (from OCI Console > Identity & Security > Compartments).
   * Docs: [OCI Generative AI Getting Started](https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm) and [IAM Policies](https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/policygetstarted.htm).
2. **OCI CLI and SDK Installation:**
   * Install the OCI CLI (includes Python SDK for authentication).
   * Command: `pip install oci-cli`.
   * Verify: `oci --version`.
   * Docs: [Install OCI CLI](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm).
3. **Python Packages:**
   * Install core libraries:
     ```bash
     pip install langchain langchain-oci oci
     ```
   * `langchain`: Core framework.
   * `langchain-oci`: Support for the OCI chat and embedding models.
   * `oci`: SDK for auth and API calls.
4. **[Set up OCI API key](https://docs.oracle.com/en-us/iaas/Content/generative-ai/setup-oci-api-auth.htm) authentication locally.**

## Connecting LangChain to OCI Generative AI
- Using a Chat Model: `ChatOCIGenAI` class exposes chat models from OCI Generative AI
- Using a completion Model: `OCIGenAI` class exposes LLMs from OCI Generative AI
- Using an embeddings Model: `OCIGenAIEmbeddings` class exposes embeddings from OCI Generative AI

### 1. Basic LLM Instantiation and Invocation
Start with a simple call to an on-demand model using API Key auth (default). This invokes the LLM directly.
```python
from langchain_oci import OCIGenAI

# Initialize the OCI GenAI LLM interface
llm = OCIGenAI(
    model_id="cohere.command",  # On-demand model ID
    service_endpoint="https://inference.generativeai.us-chicago-1.oci.oraclecloud.com",
    compartment_id="MY_OCID",  # Your compartment OCID
    # Auth uses ~/.oci/config by default (API Key)
)

# Basic invocation with optional parameters
response = llm.invoke("Tell me one fact about Earth", temperature=0.7)
print(response)
# Expected output: A generated fact, e.g., "Earth is the third planet from the Sun."
```

### 2. Prompt Chaining with LLMChain
Chain a prompt template to the LLM for structured inputs/outputs. This example uses Session Token auth and passes model kwargs for consistency.
```python
from langchain_oci import OCIGenAI
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate

# Initialize with Session Token auth and model parameters
llm = OCIGenAI(
    model_id="meta.llama-3.3-70b-instruct",  # Another on-demand model
    service_endpoint="https://inference.generativeai.us-chicago-1.oci.oraclecloud.com",
    compartment_id="MY_OCID",
    auth_type="SECURITY_TOKEN",
    auth_profile="MY_PROFILE",  # Profile from ~/.oci/config
    model_kwargs={
        "temperature": 0.7,
        "top_p": 0.75,  # Nucleus sampling
        "max_tokens": 200  # Limit response length
    }
)

# Define a prompt template
prompt = PromptTemplate(
    input_variables=["query"],
    template="{query}"  # Simple template; customize for multi-step chaining
)

# Create the chain
llm_chain = LLMChain(llm=llm, prompt=prompt)

# Invoke the chain
response = llm_chain.invoke("What is the capital of France?")
print(response["text"])
# Expected output: "The capital of France is Paris."
```
**Resources:**

* [Full OCI GenAI + LangChain Guide](https://blogs.oracle.com/ai-and-datascience/developing-ai-apps-oci-generative-ai-langchain).
* [LangChain OCI Integration Docs](https://docs.oracle.com/en-us/iaas/Content/generative-ai/langchain.htm).
  