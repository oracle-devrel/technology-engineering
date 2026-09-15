"""Embed the paragraphs of a text file with OCI Generative AI.

Usage: python embed_file.py <path-to-text-file>
"""
import os
import sys
import oci
from dotenv import load_dotenv

load_dotenv()
COMPARTMENT_ID = os.environ["OCI_COMPARTMENT_ID"]

MODEL_ID = "cohere.embed-v4.0"

# One embedding per paragraph (each input must stay under 512 tokens,
# max 96 inputs per request)
text = open(sys.argv[1], encoding="utf-8").read()
paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()][:96]

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
        inputs=paragraphs,
    )
)

for paragraph, embedding in zip(paragraphs, response.data.embeddings):
    print(f"{len(embedding)}-dim vector for: {paragraph[:60]}...")
