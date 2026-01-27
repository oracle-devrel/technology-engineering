from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path

from api.auth import api_key_auth
from api.models.oci_chat import OCIGenAIModel
#from api.models.ociodsc import OCIOdscModel
from api.schema import Models, Model

router = APIRouter(
    prefix="/models",
    dependencies=[Depends(api_key_auth)],
    # responses={404: {"description": "Not found"}},
)

chat_model = OCIGenAIModel()
#odsc_model = OCIOdscModel()
all_models = chat_model.list_models() #+ odsc_model.list_models()


async def validate_model_id(model_id: str):
    if model_id not in all_models:
        raise HTTPException(status_code=500, detail="Unsupported Model Id")


@router.get("", response_model=Models)
async def list_models():
    model_list = []
    for model_id in all_models:
        model = Model(
            object="model",
            id=model_id,
            created=0,
            owned_by=""
            )
        model_list.append(model)
    return Models(data=model_list)


@router.get("/{model_id}", response_model=Model, )
async def get_model(
        model_id: Annotated[str, Path(description="Model ID", example="cohere.command-r-plus"),]
):
    await validate_model_id(model_id)
    return Model(id=model_id)
