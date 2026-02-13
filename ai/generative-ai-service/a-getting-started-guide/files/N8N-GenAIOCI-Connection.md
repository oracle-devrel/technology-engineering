## Integrating n8n Workflows with OCI Generative AI

### Prerequisites
1. **OCI Account and Permissions:**
   * Create or use an active OCI tenancy with Generative AI enabled.
   * Set up IAM policies: Grant your user/group access to `generative-ai-family` in a sandbox compartment (e.g., `allow group <group-name> to manage generative-ai-family in compartment <compartment-name>`).
   * Gather: Compartment OCID (from OCI Console > Identity & Security > Compartments).
   * Docs: [OCI Generative AI Getting Started](https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm) and [IAM Policies](https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/policygetstarted.htm).
2. **[Set up OCI API key](https://docs.oracle.com/en-us/iaas/Content/generative-ai/setup-oci-api-auth.htm) authentication locally.**
3. n8n installed and running (self-hosted or cloud version; version 1.0+ recommended for AI nodes).

## Step 1: Launch the OCI GenAI Gateway
The gateway runs a local server (port 8088) that mimics the OpenAI API, allowing n8n to interact with OCI models like those provided by OpenAI, Llama and Grok as an example.

### Option 1: Run with Uvicorn (Local Development)
From the repo root:

1. Navigate to `./app` and install dependencies: `pip install -r requirements.txt`.
2. Start the server:
   ```bash
   cd app
   uvicorn app:app --host 0.0.0.0 --port 8088 --reload
   ```
   For production (Linux only, with Gunicorn for scaling):
   ```bash
   gunicorn app:app --workers 16 --worker-class uvicorn.workers.UvicornWorker --timeout 600 --bind 0.0.0.0:8088
   ```

### Option 2: Run with Podman (Containerized Deployment)

1. Install Podman:
   * Linux: `sudo apt install podman` (Ubuntu) or `sudo dnf install podman` (Fedora).
   * macOS: `brew install podman`.
   * Windows: Follow [Podman for Windows guide](https://podman.io/docs/installation#windows).
2. Ensure `~/.oci/config` is set up (from prerequisites).
3. Build and run:
   ```bash
   podman build -t oci_genai_gateway .
   podman run -p 8088:8088 \
     -v ~/.oci:/root/.oci:Z \
     -it --name oci_genai_gateway oci_genai_gateway
   ```
4. Verify: Open `http://localhost:8088` in a browser (should show a health check or API docs). Check logs with `podman logs oci_genai_gateway`.

**Gateway Endpoint:** The server exposes `/v1/chat/completions` (OpenAI-compatible) at `http://localhost:8088`.

## Step 2: Configure n8n to Use the OCI Gateway
In n8n, use the **OpenAI** node but point it to your local gateway as a custom endpoint. This lets you select OCI models seamlessly.

1. In n8n, create a new workflow.
2. Add an **OpenAI** node (under AI > Chat Models).
3. Configure credentials:
   * **API Key:** Leave blank or use a dummy value (gateway uses OCI auth).
   * **Base URL:** `http://host.docker.internal:8088/v1` (for Podman/Docker; use `http://localhost:8088/v1` if running natively).
   * **Model:** Select or enter an OCI model (list available models via gateway docs or OCI Console).
n8n will now route requests through the gateway to OCI GenAI.

## Step 3: Simple n8n Workflow Example – AI-Powered Text Summarization
This example creates a workflow that triggers on a webhook (e.g., incoming email or form data), summarizes text using an OCI LLM, and sends the result via email. It demonstrates calling the LLM with minimal code.

### Workflow Overview
* **Trigger:** Webhook (receives input text).
* **AI Node:** OpenAI (calls OCI via gateway for summarization).
* **Output:** Email node (sends summary).

### Step-by-Step Setup in n8n

1. **Add Webhook Trigger:**
   Drag Webhook node.
   * Set Method: POST.
   * Path: `/summarize` (test URL: `http://your-n8n-instance/webhook/summarize`).
   * This receives JSON payload like `{"text": "Long article content here..."}`.
2. **Add OpenAI Node for Summarization:**
   * Connect after Webhook.
   * Operation: Chat.
   * Credentials: Use the custom setup from Step 2 (Base URL: `http://localhost:8088/v1`).
   * Model: `meta.llama-3.3-70b-instruct` (or your preferred OCI model).
   * Messages:
     * Role: System – Prompt: `You are a helpful summarizer. Provide a concise 3-sentence summary.`
     * Role: User – Prompt: `{{ $json.text }}` (references webhook input).
   * Options: Temperature: 0.3 (for consistent outputs); Max Tokens: 200.
   **Effective API Call (Behind the Scenes):**
   The node generates a request like this to the gateway:
   ```json
   POST http://localhost:8088/v1/chat/completions
   {
     "model": "meta.llama-3.3-70b-instruct",
     "messages": [
       {"role": "system", "content": "You are a helpful summarizer. Provide a concise 3-sentence summary."},
       {"role": "user", "content": "{{input_text}}"}
     ],
     "temperature": 0.3,
     "max_tokens": 200
   }
   ```
   The gateway forwards this to OCI GenAI, returning a response like:
   ```json
   {
     "choices": [
       {
         "message": {
           "role": "assistant",
           "content": "Summary sentence 1. Sentence 2. Sentence 3."
         }
       }
     ]
   }
   ```
3. **Add Email Output Node:**
   * Connect after OpenAI.
   * Node: Send Email (or Gmail/SMTP).
   * To: `recipient@example.com`.
   * Subject: `AI Summary of Input`.
   * Body: `{{ $json.choices[0].message.content }}` (extracts summary from AI response).
4. **Activate and Test:**
   * Save and activate the workflow.
   * Send a POST request to the webhook (e.g., via curl):
     ```bash
     curl -X POST http://your-n8n-instance/webhook/summarize \
       -H "Content-Type: application/json" \
       -d '{"text": "Oracle OCI GenAI enables powerful automations. n8n connects apps seamlessly. Together, they boost productivity."}'
     ```
   * Check n8n executions: The workflow should summarize the text and email it.
   * View logs in n8n for details (e.g., AI response parsing).

## Troubleshooting & Tips
* **Authentication Errors:** Verify `~/.oci/config` permissions and OCI policies (from prerequisites). Test with `oci` CLI commands like `oci os ns get`.
* **Connection Issues:** Ensure port 8088 is open (firewall/OCI security lists). For Podman, use `--network=host` if needed.
* **Model Not Found:** List OCI models in Console under **Analytics & AI > Generative AI**. Ensure your tenancy has the required permissions for `generative-ai-family`.