from typing import Annotated, Union

from fastapi import APIRouter, Depends, Body, Request
from fastapi.responses import StreamingResponse

from api.auth import api_key_auth
from api.models.oci_chat import OCIGenAIModel
#from api.models.ociodsc import OCIOdscModel
from openai.types.chat.chat_completion import ChatCompletion
from openai.resources.chat.completions import CompletionsWithStreamingResponse
from api.schema import ChatRequest #, ChatCompletion, CompletionsWithStreamingResponse
from api.setting import SUPPORTED_OCIGENAI_CHAT_MODELS, SUPPORTED_OCIODSC_CHAT_MODELS

router = APIRouter(
    prefix="/chat",
    dependencies=[Depends(api_key_auth)]
)


@router.post(
    "/completions", 
    response_model=Union[ChatCompletion], 
    response_model_exclude_unset=True
    )
async def chat_completions(
    chat_request: Annotated[
        ChatRequest,
        Body(
            examples=[
                {
                    "model": "xai.grok-4",
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": "Hello!"},
                    ],
                }
            ],
        ),
    ]
):
    try:
        model_type = SUPPORTED_OCIGENAI_CHAT_MODELS[chat_request.model]["type"]
    except:
        raise HTTPException(status_code=400, detail="Unsupported model")
    
    # except:
    #     model_type = SUPPORTED_OCIODSC_CHAT_MODELS[chat_request.model]["type"]
    # Exception will be raised if model not supported.

    # if model_type == "datascience":
    #     model = OCIOdscModel()  # Data Science models
    # GenAI service ondemand models
    if model_type == "ondemand":
        model = OCIGenAIModel() 
    # GenAI service dedicated models
    elif model_type == "dedicated":
        model = OCIGenAIModel()  

    model.validate(chat_request)

    if chat_request.stream:
        return StreamingResponse(
            content=model.chat_stream(chat_request), media_type="text/event-stream"
        )
    return model.chat(chat_request)
