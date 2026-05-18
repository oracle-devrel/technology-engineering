from typing import Literal
import numpy as np
import base64

from api.schema import (
    EmbeddingsRequest, 
    EmbeddingsResponse
)

from oci.generative_ai_inference import models as oci_models

from openai.types import (
    Embedding,
    CreateEmbeddingResponse as EmbeddingsResponse
)
from openai.types.create_embedding_response import Usage

class EmbedRequestAdapter:
    def __init__(self, model_info: dict):
        self.model_info = model_info
        self.provider = model_info["provider"]

    @staticmethod
    def _set_serving_mode(model_info):
        compartment_id = model_info["compartment_id"]
        serving_mode = oci_models.OnDemandServingMode(
            serving_type="ON_DEMAND",
            model_id=model_info["model_id"],
        )
        return serving_mode, compartment_id

    def to_oci(self, request: EmbeddingsRequest) -> oci_models.EmbedTextDetails:
        serving_mode, compartment_id = EmbedRequestAdapter._set_serving_mode(self.model_info)

        # “SEARCH_DOCUMENT”, “SEARCH_QUERY”, “CLASSIFICATION”, “CLUSTERING”, “IMAGE”
        input_type = "SEARCH_DOCUMENT"
        if isinstance(request.get("input"), str):
            inputs = [request.get("input")]        
        else:
            inputs = request.get("input")

        if len(inputs) == 1:
            if  inputs[0].startswith("data:image/"):
                input_type = "IMAGE" 
        embed_text_details = oci_models.EmbedTextDetails(
            compartment_id=compartment_id,
            serving_mode=serving_mode,
            inputs=inputs,            
            truncate = "END",
            is_echo = False,
            input_type = input_type
        )
        
        return embed_text_details

    @staticmethod
    def to_openai(response: oci_models.EmbedTextResult) -> EmbeddingsResponse:
        embeddings = response.embeddings
        data = EmbedRequestAdapter.convert_data(embeddings)
        openai_response = EmbeddingsResponse(
            object = "list",
            data = data,
            model = response.model_id,
            usage = Usage(
                prompt_tokens = response.usage.prompt_tokens,
                total_tokens = response.usage.total_tokens
            )            
        )
        return openai_response

    @staticmethod
    def convert_data(embeddings: list[list[float]], encoding_format: Literal["float", "base64"] = "float") -> list[Embedding]:
        data = []
        for i, embedding in enumerate(embeddings):
            if encoding_format == "base64":
                arr = np.array(embedding, dtype=np.float32)
                arr_bytes = arr.tobytes()
                embedding = base64.b64encode(arr_bytes)
            else:
                pass
            data.append(
                Embedding(
                    object="embedding", 
                    index=i, 
                    embedding=embedding
                    )
                )
        return data


