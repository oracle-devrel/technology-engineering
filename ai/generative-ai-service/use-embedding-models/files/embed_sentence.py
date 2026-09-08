"""Embed a single sentence with OCI Generative AI."""
import os
import oci
from dotenv import load_dotenv

load_dotenv()
COMPARTMENT_ID = os.environ["OCI_COMPARTMENT_ID"]

MODEL_ID = "cohere.embed-v4.0"

client = oci.generative_ai_inference.GenerativeAiInferenceClient(
    config=oci.config.from_file(),
    service_endpoint="https://inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com",
)

response = client.embed_text(
    oci.generative_ai_inference.models.EmbedTextDetails(
        serving_mode=oci.generative_ai_inference.models.OnDemandServingMode(
            model_id=MODEL_ID
        ),
        # For a dedicated AI cluster, replace the serving_mode above with the
        # endpoint OCID of your hosted model:
        # serving_mode=oci.generative_ai_inference.models.DedicatedServingMode(
        #     endpoint_id="ocid1.generativeaiendpoint.oc1.eu-frankfurt-1.replace-with-your-endpoint-ocid"
        # ),
        compartment_id=COMPARTMENT_ID,
        inputs=["Oracle Cloud Infrastructure makes embeddings easy."],
    )
)

embedding = response.data.embeddings[0]
print(f"Vector with {len(embedding)} dimensions:")
print(embedding[:5], "...")
