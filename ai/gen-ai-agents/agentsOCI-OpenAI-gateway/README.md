
# OCI OpenAI-Compatible Gateway

Simple FastAPI gateway exposing OCI LLMs and Agents via OpenAI-compatible API.
Big thanks to https://github.com/RETAJD/modelsOCI-toOpenAI/tree/main

**Author**: matsliwins

**Last review date**: 19/09/2025

![](images/n8n_image.png)

## Quick Start

1. **Install dependencies**:
```bash
pip install fastapi uvicorn oci pyyaml openai
```

2. **Set API key (optional)**:
```bash
export GATEWAY_API_KEYS="ocigenerativeai" #default
```

3. **Prepare config files** (`agents.yaml`, `models.yaml`) next to `app.py`:

Example `agents.yaml`:
```yaml
agents:
  - id: "sales-kb"
    name: "Sales KB Agent"
    description: "Grounded in sales docs"
    region: "eu-frankfurt-1"
    endpoint_ocid: "ocid1.genaiagentendpoint.oc1.xxx"
```

Example `models.yaml`:
```yaml
region: eu-frankfurt-1
compartment_id: "ocid1.compartment.oc1..xxx"
models:
  ondemand:
    - name: "cohere.command-r"
      model_id: "cohere.command-r"
      description: "Command R Model"
```

4. **Run the app**:
```bash
uvicorn app:app --host 0.0.0.0 --port 8088
```
or
```bash
python app.py
```

## Usage Example

```python
from openai import OpenAI

client = OpenAI(api_key="ocigenerativeai", base_url="http://localhost:8088/v1/")

r1 = client.chat.completions.create(
    model="ignored",
    messages=[{"role": "user", "content": "Reply with 'pong'."}],
    extra_body={
        "agent_endpoint_ocid": "ocid1.genaiagentendpoint.oc1.eu-frankfurt-1.", #your genai agent **endpoint** OCID
        "region": "eu-frankfurt-1",
    },
)
print(r1.choices[0].message.content)

```

## n8n/Open WebUI Integration

- URL: `http://localhost:8088/v1`
- Model: `agent:sales-kb` or model names from `models.yaml`
