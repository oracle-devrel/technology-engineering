import base64
import json
import logging
import re
import time
from abc import ABC
from typing import AsyncIterable, Iterable, Literal

import oci
from api.setting import (
    DEBUG,
    CLIENT_KWARGS,
    SUPPORTED_OCIODSC_CHAT_MODELS
)

import requests, json
import numpy as np
from api.models.odsc_client import DataScienceAiInferenceClient
from fastapi import HTTPException

from api.models.base import BaseChatModel
from api.schema import (
#     # Chat
     ChatResponse,
    ChatRequest,
#     Choice,
#     ChatResponseMessage,
#     Usage,
     ChatStreamResponse,
#     ImageContent,
#     TextContent,
#     ToolCall,
#     ChoiceDelta,
#     UserMessage,
#     AssistantMessage,
#     ToolMessage,
#     Function,
#     ResponseFunction
 )
from openai.types import *

from api.setting import DEBUG

logging.basicConfig(format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)

odsc_client = DataScienceAiInferenceClient(
                **CLIENT_KWARGS
            )


class OCIOdscModel(BaseChatModel):
    # https://docs.oracle.com/en-us/iaas/data-science/using/ai-quick-actions-model-deploy.htm
    _supported_models = {}

    for model in SUPPORTED_OCIODSC_CHAT_MODELS:
        _supported_models[model] = {
            "system": True,
            "multimodal": False,
            "tool_call": False,
            "stream_tool_call": False,
        }

    def list_models(self) -> list[str]:
        return list(self._supported_models.keys())

    def validate(self, chat_request: ChatRequest):
        """Perform basic validation on requests"""
        error = ""
        # check if model is supported
        if chat_request.model not in self._supported_models.keys():
            error = f"Unsupported model {chat_request.model}, please use models API to get a list of supported models"

        # check if tool call is supported
        elif chat_request.tools and not self._is_tool_call_supported(chat_request.model, stream=chat_request.stream):
            tool_call_info = "Tool call with streaming" if chat_request.stream else "Tool call"
            error = f"{tool_call_info} is currently not supported by {chat_request.model}"

        if error:
            raise HTTPException(
                status_code=400,
                detail=error,
            )

    def _invoke_genai(self, chat_request: ChatRequest, stream=False):
        """Common logic for invoke OCI GenAI models"""
        if DEBUG:
            logger.info("Raw request: " + chat_request.model_dump_json())

        # convert OpenAI chat request to OCI Generative AI SDK request
        args = self._parse_request(chat_request)
        if DEBUG:
            logger.info("OCI Data Science AI Quick Actions request: " + json.dumps(args))
        try:
            endpoint = SUPPORTED_OCIODSC_CHAT_MODELS[chat_request.model]["endpoint"]
            response = odsc_client.chat(endpoint, chat_details=args)
        except Exception as e:
            logger.error(e)
            raise HTTPException(status_code=500, detail=str(e))
        return response

    def chat(self, chat_request: ChatRequest) -> ChatResponse:
        """Default implementation for Chat API."""

        # message_id = self.generate_message_id()
        try:
            response = self._invoke_genai(chat_request)

            texts = [{"text": response["choices"][0]["message"]["content"].strip()}]

            chat_response = self._create_response(
                model=chat_request.model,
                message_id=response["id"],
                content=texts,
                finish_reason=response["choices"][0]["finish_reason"],
                input_tokens=response["usage"]["prompt_tokens"],
                output_tokens=response["usage"]["completion_tokens"],
            )
        except Exception as e:
            logger.error("Error in _invoke_genai: " + str(response))
            logger.error(e)
            raise HTTPException(status_code=500, detail=str(e) + str(response))
        if DEBUG:
            logger.info("Proxy response :" + chat_response.model_dump_json())
        return chat_response

    def chat_stream(self, chat_request: ChatRequest) -> AsyncIterable[bytes]:
        """Default implementation for Chat Stream API"""
        response = self._invoke_genai(chat_request, stream=True)

        events = response.events()
        for stream in events:
            try:
                chunk = json.loads(stream.data)
            except:
                break
            stream_response = self._create_response_stream(
                model_id=chat_request.model,
                message_id=chunk["id"],
                chunk=chunk
            )
            if DEBUG:
                logger.info(stream_response)
            if not stream_response:
                continue
            if DEBUG:
                logger.info("Proxy response :" + stream_response.model_dump_json())
            if stream_response.choices:
                yield self.stream_response_to_bytes(stream_response)
            elif (
                    chat_request.stream_options
                    and chat_request.stream_options.include_usage
            ):
                # An empty choices for Usage as per OpenAI doc below:
                # if you set stream_options: {"include_usage": true}.
                # an additional chunk will be streamed before the data: [DONE] message.
                # The usage field on this chunk shows the token usage statistics for the entire request,
                # and the choices field will always be an empty array.
                # All other chunks will also include a usage field, but with a null value.
                yield self.stream_response_to_bytes(stream_response)

        # return an [DONE] message at the end.
        yield self.stream_response_to_bytes()

    def _parse_system_prompts(self, chat_request: ChatRequest) -> list[dict[str, str]]:
        """Create system prompts.
        Note that not all models support system prompts.

        example output: [{"text" : system_prompt}]

        See example:
        https://docs.oracle.com/en-us/iaas/api/#/EN/generative-ai-inference/20231130/ChatResult/Chat
        """

        system_prompts = []
        for message in chat_request.messages:
            if message.role != "system":
                # ignore system messages here
                continue
            assert isinstance(message.content, str)
            system_prompts.append(message.content)

        return system_prompts

    def _parse_messages(self, chat_request: ChatRequest) -> list[dict]:
        """
        Converse API only support user and assistant messages.

        example output: [
            {"role": "user", "content": "What is your favourite condiment?"},
            {"role": "assistant", "content": "Well, I'm quite partial to a good squeeze of fresh lemon juice. },
            {"role": "user", "content": "Do you have mayonnaise recipes?"}
        ]

        See example:
        https://github.com/oracle-samples/oci-data-science-ai-samples/blob/b1e319a935a0b85ccc2f6f1065e63915581c9442/ai-quick-actions/multimodal-models-tips.md
        """
        messages = []
        for message in chat_request.messages:
            if isinstance(message, UserMessage):
                messages.append(
                    {
                        "role": message.role,
                        "content": self._parse_content_parts(
                            message, chat_request.model
                        ),
                    }
                )
            elif isinstance(message, AssistantMessage):
                if message.content:
                    # Text message
                    messages.append(
                        {"role": message.role, "content": message.content}
                    )
                # else:
                # Tool use message
                # tool_input = json.loads(message.tool_calls[0].function.arguments)
                # messages.append(
                #     {
                #         "role": message.role,
                #         "content": [
                #             {
                #                 "toolUse": {
                #                     "toolUseId": message.tool_calls[0].id,
                #                     "name": message.tool_calls[0].function.name,
                #                     "input": tool_input
                #                 }
                #             }
                #         ],
                #     }
                # )
            # elif isinstance(message, ToolMessage):

            #     # Add toolResult to content
            #     # https://docs.oracle.com/en-us/iaas/api/#/EN/generative-ai-inference/20231130/ChatResult/Chat
            #     messages.append(
            #         {
            #             "role": "user",
            #             "content": [
            #                 {
            #                     "toolResult": {
            #                         "toolUseId": message.tool_call_id,
            #                         "content": [{"text": message.content}],
            #                     }
            #                 }
            #             ],
            #         }
            #     )

            else:
                # ignore others, such as system messages
                continue
        return messages

    def _parse_request(self, chat_request: ChatRequest) -> dict:
        """Create default converse request body.

        Also perform validations to tool call etc.

        Ref: https://github.com/oracle-samples/oci-data-science-ai-samples/tree/b1e319a935a0b85ccc2f6f1065e63915581c9442/ai-quick-actions
        """

        messages = self._parse_messages(chat_request)

        # Base inference parameters.        
        chat_detail = {
            "model": "odsc-llm",
            "messages": messages,
            "max_tokens": chat_request.max_tokens,
            "stream": chat_request.stream,
            "frequency_penalty": chat_request.frequency_penalty,
            "presence_penalty": chat_request.presence_penalty,
            "temperature": chat_request.temperature,
            "top_p": chat_request.top_p,
            # "topK": chat_request.top_k
        }

        return chat_detail

    def _create_response(
            self,
            model: str,
            message_id: str,
            content: list[dict] = None,
            finish_reason: str | None = None,
            input_tokens: int = 0,
            output_tokens: int = 0,
    ) -> ChatResponse:

        message = ChatResponseMessage(
            role="assistant",
        )
        if finish_reason == "tool_use":
            # https://docs.oracle.com/en-us/iaas/api/#/EN/generative-ai-inference/20231130/datatypes/CohereChatRequest
            tool_calls = []
            for part in content:
                if "toolUse" in part:
                    tool = part["toolUse"]
                    tool_calls.append(
                        ToolCall(
                            id=tool["toolUseId"],
                            type="function",
                            function=ResponseFunction(
                                name=tool["name"],
                                arguments=json.dumps(tool["input"]),
                            ),
                        )
                    )
            message.tool_calls = tool_calls
            message.content = None
        else:
            message.content = content[0]["text"]

        response = ChatResponse(
            id=message_id,
            model=model,
            choices=[
                Choice(
                    index=0,
                    message=message,
                    finish_reason=self._convert_finish_reason(finish_reason),
                    logprobs=None,
                )
            ],
            usage=Usage(
                prompt_tokens=input_tokens,
                completion_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
            ),
        )
        response.system_fingerprint = "fp"
        response.object = "chat.completion"
        response.created = int(time.time())
        return response

    def _create_response_stream(
            self, model_id: str, message_id: str, chunk: dict
    ) -> ChatStreamResponse | None:
        """Parsing the OCI GenAI stream response chunk.

        Ref: https://docs.oracle.com/en-us/iaas/api/#/EN/generative-ai-inference/20231130/ChatResult/Chat
        """
        # if DEBUG:
        #    logger.info("OCI GenAI response chunk: " + str(chunk))

        finish_reason = None
        message = None
        usage = None
        if "choices" in chunk:
            finish_reason = chunk["choices"][0]["finish_reason"]
            text = chunk["choices"][0]["delta"]["content"]
            message = ChatResponseMessage(
                role="assistant",
                content=text,
            )

            # logger.info("消息："+str(message))
        if "contentBlockStart" in chunk:
            # tool call start
            delta = chunk["contentBlockStart"]["start"]
            if "toolUse" in delta:
                # first index is content
                index = chunk["contentBlockStart"]["contentBlockIndex"] - 1
                message = ChatResponseMessage(
                    tool_calls=[
                        ToolCall(
                            index=index,
                            type="function",
                            id=delta["toolUse"]["toolUseId"],
                            function=ResponseFunction(
                                name=delta["toolUse"]["name"],
                                arguments="",
                            ),
                        )
                    ]
                )

        if "metadata" in chunk:
            # usage information in metadata.
            metadata = chunk["metadata"]
            if "usage" in metadata:
                # token usage
                return ChatStreamResponse(
                    id=message_id,
                    model=model_id,
                    choices=[],
                    usage=Usage(
                        prompt_tokens=metadata["usage"]["inputTokens"],
                        completion_tokens=metadata["usage"]["outputTokens"],
                        total_tokens=metadata["usage"]["totalTokens"],
                    ),
                )

        if message:
            return ChatStreamResponse(
                id=message_id,
                model=model_id,
                choices=[
                    ChoiceDelta(
                        index=0,
                        delta=message,
                        logprobs=None,
                        finish_reason=self._convert_finish_reason(finish_reason),
                    )
                ],
                usage=usage,
            )

        return None

    def _parse_content_parts(
            self,
            message: UserMessage,
            model_id: str,
    ) -> list[dict]:
        if isinstance(message.content, str):
            return message.content
        content_parts = []
        for part in message.content:
            if isinstance(part, TextContent):
                content_parts.append(
                    {
                        "text": part.text,
                    }
                )
            elif isinstance(part, ImageContent):
                if not self._is_multimodal_supported(model_id):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Multimodal message is currently not supported by {model_id}",
                    )
                image_data, content_type = self._parse_image(part.image_url.url)
                content_parts.append(
                    {
                        "image": {
                            "format": content_type[6:],  # image/
                            "source": {"bytes": image_data},
                        },
                    }
                )
            else:
                # Ignore..
                continue
        return content_parts

    def _is_tool_call_supported(self, model_id: str, stream: bool = False) -> bool:
        feature = self._supported_models.get(model_id)
        if not feature:
            return False
        return feature["stream_tool_call"] if stream else feature["tool_call"]

    def _is_multimodal_supported(self, model_id: str) -> bool:
        feature = self._supported_models.get(model_id)
        if not feature:
            return False
        return feature["multimodal"]

    def _is_system_prompt_supported(self, model_id: str) -> bool:
        feature = self._supported_models.get(model_id)
        if not feature:
            return False
        return feature["system"]

    # def _convert_tool_spec(self, func: Function) -> dict:

    #     return {
    #             "name": func.name,
    #             "description": func.description,
    #             "parameter_definitions": {
    #                 "type":
    #                 "description":
    #                 "is_required":
    #                 "json": func.parameters,
    #             }
    #         }

    def _convert_finish_reason(self, finish_reason: str | None) -> str | None:
        """
        Below is a list of finish reason according to OpenAI doc:

        - stop: if the model hit a natural stop point or a provided stop sequence,
        - length: if the maximum number of tokens specified in the request was reached,
        - content_filter: if content was omitted due to a flag from our content filters,
        - tool_calls: if the model called a tool
        """
        if finish_reason:
            finish_reason_mapping = {
                "tool_calls": "tool_calls",
                "stop": "stop",
                "content_filter": "content_filter",
                "stop": "stop",
                "length": "length",
            }
            return finish_reason_mapping.get(finish_reason.lower(), finish_reason.lower())
        return None
