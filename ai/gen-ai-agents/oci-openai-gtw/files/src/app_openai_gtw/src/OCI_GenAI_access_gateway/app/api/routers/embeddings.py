from typing import Annotated

from fastapi import APIRouter, Depends, Body

from api.auth import api_key_auth
from api.models.oci_embed import get_embeddings_model
from api.schema import EmbeddingsRequest, EmbeddingsResponse

router = APIRouter(
    prefix="/embeddings",
    dependencies=[Depends(api_key_auth)],
)


@router.post("", response_model=EmbeddingsResponse)
async def embeddings(
        embeddings_request: Annotated[
            EmbeddingsRequest,
            Body(
                examples=[
                    {
                        "model": "cohere.embed-multilingual-v3",
                        "input": [
                            "Your text string goes here"
                        ],
                    }
                ],
            ),
        ]
):

    # Exception will be raised if model not supported.
    model = get_embeddings_model(embeddings_request.get("model"))
    return model.embed(embeddings_request)
