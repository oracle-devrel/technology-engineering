## Connecting Oracle AI Database 26ai to OCI Generative AI Services from Apps

### Prerequisites
1. **OCI Account and Permissions:**
   * Create or use an active OCI tenancy with Generative AI enabled.
   * Set up IAM policies: Grant your user/group access to `generative-ai-family` in a sandbox compartment (e.g., `allow group <group-name> to manage generative-ai-family in compartment <compartment-name>`).
   * Gather: Compartment OCID (from OCI Console > Identity & Security > Compartments).
   * Docs: [OCI Generative AI Getting Started](https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm) and [IAM Policies](https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/policygetstarted.htm).
2. **[Set up OCI API key](https://docs.oracle.com/en-us/iaas/Content/generative-ai/setup-oci-api-auth.htm) authentication locally.**
3. **[AI-enable](https://docs.oracle.com/en/database/oracle/oracle-database/26/aienb/ai-enablement-guide.pdf) the 26ai database schema.**
4. Install packages:
   ```bash
   pip install oci oracledb
   ```

## Working Example

### Step 1: Create the OCI GenAI Inference client (config-file auth)
```python
import os
import oci
from oci.generative_ai_inference import GenerativeAiInferenceClient

def create_genai_client():
    config = oci.config.from_file(
        file_location=os.path.expanduser("~/.oci/config"),
        profile_name=os.getenv("OCI_PROFILE", "DEFAULT"),
    )
    return GenerativeAiInferenceClient(
        config=config,
        service_endpoint=os.environ["GENAI_ENDPOINT"],  # e.g. https://inference.generativeai.us-chicago-1.oci.oraclecloud.com
        timeout=(10, 240),
    )
```

**What you must set**

* `GENAI_ENDPOINT` (region-specific).
* `OCI_PROFILE` (optional; defaults to `DEFAULT`).

### Step 2: Create an embedding for the user’s question (OCI SDK)
This is the “query vector” used for vector search in the DB.

> Important: **the query embedding model must match the document embedding model** you used to populate your DB table.

```python
import oci
from oci.generative_ai_inference.models import EmbedTextDetails, OnDemandServingMode
def embed_query(genai_client, question: str) -> list[float]:
    embed_details = EmbedTextDetails(
        compartment_id=os.environ["OCI_COMPARTMENT_ID"],
        serving_mode=OnDemandServingMode(model_id=os.environ["EMBED_MODEL_ID"]),
        inputs=[question],
        input_type="SEARCH_QUERY",
    )
    resp = genai_client.embed_text(embed_details)
    # resp.data is EmbedTextResult with .embeddings attribute
    vector = resp.data.embeddings[0]
    return vector
```

**Environment variables**

* `OCI_COMPARTMENT_ID`.
* `EMBED_MODEL_ID` (example: `cohere.embed-english-v3.0`, depending on what your tenancy exposes).

**What changes depending on needs**

* `input_type` can be `SEARCH_QUERY` vs `SEARCH_DOCUMENT` (commonly used to improve retrieval quality).
* embedding model name/OCID and embedding dimension.

### Step 3: Retrieve top-K context from 26ai using vector similarity search
```python
import oracledb

def create_db_connection():
    return oracledb.connect(
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        dsn=os.environ["DB_DSN"],
    )

def retrieve_top_k(conn, query_vec: list[float], k: int = 5):
    """
    Returns: list of (doc_id, chunk_text, source)
    """
    sql = """
        SELECT doc_id, chunk_text, source
        FROM docs
        ORDER BY VECTOR_DISTANCE(embedding, :qv, COSINE)
        FETCH FIRST :k ROWS ONLY
    """
    with conn.cursor() as cur:
        cur.execute(sql, qv=query_vec, k=k)
        return cur.fetchall()
```

**What changes depending on needs (and environment)**

* The distance function/operator can vary (`COSINE`, dot product, etc.).
* Vector bind support depends on DB/driver versions and how your VECTOR column is defined.

### Step 4: Call OCI GenAI Inference Chat with grounded context (OCI SDK)
```python
from oci.generative_ai_inference.models import ChatDetails, OnDemandServingMode, CohereChatRequest

def build_prompt(question: str, rows) -> str:
    context = "\n\n".join(
        [f"[doc_id={doc_id} source={source}]\n{text}" for (doc_id, text, source) in rows]
    )
    return f"""You are a helpful assistant. Use ONLY the context below to answer.
If the context is insufficient, say "I don't know".
Context:
{context}
Question:
{question}
"""

def chat_answer(genai_client, prompt: str) -> str:
    chat_details = ChatDetails(
        compartment_id=os.environ["OCI_COMPARTMENT_ID"],
        serving_mode=OnDemandServingMode(model_id=os.environ["CHAT_MODEL_ID"]),
        chat_request=CohereChatRequest(
            message=prompt,
            max_tokens=600,
            temperature=0.2,
            top_p=0.75,
        ),
    )
    resp = genai_client.chat(chat_details)
    return resp.data.chat_response.text
```

**Environment variables**

* `CHAT_MODEL_ID` (example: a Cohere Command model available in your region/tenancy).

**What changes depending on needs**

* The request object differs if you switch model families/providers (some use a messages array vs a single `message`).
* generation parameters: `temperature`, `max_tokens`, etc.
