from typing import List, Union
import logging
from oci.generative_ai_inference import models as oci_models
from api.schema import ChatRequest
from openai.types.chat import (
    completion_create_params,
    ChatCompletionMessageParam
)
from openai.types.shared.response_format_text import ResponseFormatText
from openai.types.shared.response_format_json_object import ResponseFormatJSONObject
from openai.types.shared.response_format_json_schema import ResponseFormatJSONSchema

from api.models.adapter.tool_adapter import ToolAdapter
from api.models.utils import logger
import pprint

class ChatRequestAdapter:
    """
    Top-level adapter that routes conversions depending on provider (generic / cohere).
    """

    def __init__(self, model_info: dict):
        self.model_info = model_info
        self.provider = model_info["provider"]

    def _set_serving_mode(self,model_info):
        type = model_info["type"]
        compartment_id = model_info["compartment_id"]
        if type == "dedicated":
            endpoint = model_info.get("endpoint", None)
            if endpoint is None:
                raise ValueError("Endpoint is required for dedicated model")
            servingMode = oci_models.DedicatedServingMode(
                serving_type="DEDICATED", endpoint_id=endpoint
            )
        elif type == "ondemand":
            model_id = model_info.get("model_id", None)
            if model_id is None:
                raise ValueError("Model ID is required for ondemand model")
            servingMode = oci_models.OnDemandServingMode(
                serving_type="ON_DEMAND", model_id=model_id
            )
        return servingMode, compartment_id

    def to_oci(self, chat_request: ChatRequest) -> oci_models.ChatDetails:
        servingMode, compartment_id = self._set_serving_mode(self.model_info)
        if self.provider == "cohere":
            return ChatRequestAdapter.CohereAdapter.to_cohere(chat_request, servingMode, compartment_id)
        else:
            return ChatRequestAdapter.GenericAdapter.to_generic(chat_request, servingMode, compartment_id)

    class GenericAdapter:
        CHAT_REQUEST_MAPPER_SAME = [
            "frequency_penalty",
            "logit_bias",
            "max_completion_tokens",
            "max_tokens",
            "metadata",
            "prediction",
            "presence_penalty",
            "response_format",
            "seed",
            "stop",
            "temperature",
            "top_p",
            "verbosity",
        ]

        CHAT_REQUEST_MAPPER_DIFF = {
            "n": "num_generations",
            "stream": "is_stream",
            "logprobs": "log_probs",
            "parallel_tool_calls": "is_parallel_tool_calls",
        }

        TOOL_CHOICE_MAPPER = {
            "none": oci_models.ToolChoiceAuto(),
            "auto": oci_models.ToolChoiceAuto(),
            "required": oci_models.ToolChoiceRequired(),
        }

        @staticmethod
        def to_generic(chat_request: ChatRequest, servingMode, compartment_id):
            inference_config = {}
            for key in ChatRequestAdapter.GenericAdapter.CHAT_REQUEST_MAPPER_SAME:
                inference_config[key] = getattr(chat_request, key)
            for key, value in ChatRequestAdapter.GenericAdapter.CHAT_REQUEST_MAPPER_DIFF.items():
                inference_config[value] = getattr(chat_request, key)

            oci_chat_request = oci_models.GenericChatRequest(**inference_config)

            # Stream options
            is_include_usage = True
            if chat_request.stream_options:
                is_include_usage = chat_request.stream_options.get("include_usage", True)
            oci_chat_request.stream_options = oci_models.StreamOptions(
                is_include_usage=is_include_usage
            )

            # Prediction
            if chat_request.prediction:
                oci_chat_request.prediction = oci_models.StaticContent(
                    content=MessageAdapter.ContentAdapter.to_generic_content(chat_request.prediction.content)
                )

            # Tool choice / reasoning effort / verbosity
            if chat_request.tool_choice:
                oci_chat_request.tool_choice = ChatRequestAdapter.GenericAdapter.TOOL_CHOICE_MAPPER.get(chat_request.tool_choice)
            if chat_request.reasoning_effort:
                oci_chat_request.reasoning_effort = chat_request.reasoning_effort.upper()
            if chat_request.verbosity:
                oci_chat_request.verbosity = chat_request.verbosity.upper()

            # Response format
            if chat_request.response_format:
                oci_chat_request.response_format = ResponseFormatAdapter.to_generic(chat_request.response_format)

            # Extra body
            if hasattr(chat_request, "extra_body") and chat_request.extra_body:
                for k, v in chat_request.extra_body.items():
                    try:
                        setattr(oci_chat_request, k, v)
                    except Exception:
                        logging.warning("Unknown extra body key:" + k)

            # Messages & tools
            oci_chat_request.messages = MessageAdapter.to_generic(chat_request.messages)
            if chat_request.tools:
                oci_chat_request.tools = ToolAdapter.ToolsDefinitionAdapter.to_generic(chat_request.tools)

            return oci_models.ChatDetails(
                compartment_id=compartment_id,
                serving_mode=servingMode,
                chat_request=oci_chat_request,
            )

    class CohereAdapter:
        CHAT_REQUEST_MAPPER_SAME = [
            "frequency_penalty",
            "max_tokens",
            "presence_penalty",
            "response_format",
            "seed",
            "temperature",
            "top_p",
        ]

        CHAT_REQUEST_MAPPER_DIFF = {
            "stream": "is_stream",
            "stop": "stop_sequences",
        }

        @staticmethod
        def to_cohere(chat_request: ChatRequest, servingMode, compartment_id):
            inference_config = {}
            for key in ChatRequestAdapter.CohereAdapter.CHAT_REQUEST_MAPPER_SAME:
                inference_config[key] = getattr(chat_request, key)
            for key, value in ChatRequestAdapter.CohereAdapter.CHAT_REQUEST_MAPPER_DIFF.items():
                inference_config[value] = getattr(chat_request, key)

            oci_chat_request = oci_models.CohereChatRequest(**inference_config)

            is_include_usage = True
            if chat_request.stream_options:
                is_include_usage = chat_request.stream_options.get("include_usage", True)
            oci_chat_request.stream_options = oci_models.StreamOptions(
                is_include_usage=is_include_usage
            )

            if chat_request.response_format:
                oci_chat_request.response_format = ResponseFormatAdapter.to_cohere(chat_request.response_format)

            if hasattr(chat_request, "extra_body") and chat_request.extra_body:
                for k, v in chat_request.extra_body.items():
                    try:
                        setattr(oci_chat_request, k, v)
                    except Exception:
                        logging.warning("Unknown extra body key:" + k)

            chat_history, cohere_message, cohere_tool_results, preamble_override = MessageAdapter.to_cohere(chat_request.messages)
            oci_chat_request.message = cohere_message
            oci_chat_request.tool_results = cohere_tool_results
            oci_chat_request.chat_history = chat_history
            oci_chat_request.preamble_override = preamble_override
            logger.info( "--- oci_chat_request:" + pprint.pformat(oci_chat_request) )
            if not oci_chat_request.max_tokens or oci_chat_request.max_tokens>4000:
                oci_chat_request.max_tokens = 4000
            logger.info( "--- oci_chat_request:" + pprint.pformat(oci_chat_request) )

            if chat_request.tools:
                oci_chat_request.tools = ToolAdapter.ToolsDefinitionAdapter.to_cohere(chat_request.tools)

            return oci_models.ChatDetails(
                compartment_id=compartment_id,
                serving_mode=servingMode,
                chat_request=oci_chat_request,
            )




class ResponseFormatAdapter:
    @staticmethod
    def to_generic(response_format: completion_create_params.ResponseFormat) -> oci_models.ResponseFormat:
        if isinstance(response_format, ResponseFormatText):
            return oci_models.TextResponseFormat()
        elif isinstance(response_format, ResponseFormatJSONObject):
            return oci_models.JsonObjectResponseFormat()
        elif isinstance(response_format, ResponseFormatJSONSchema):
            return oci_models.JsonSchemaResponseFormat(
                json_schema=oci_models.ResponseJsonSchema(
                    name=response_format.json_schema.name,
                    description=response_format.json_schema.description,
                    schema=response_format.json_schema.schema,
                    is_strict=response_format.json_schema.is_strict,
                )
            )
        elif isinstance(response_format, dict) and response_format.get('type') == 'json_schema':
            return oci_models.JsonSchemaResponseFormat(
                json_schema=oci_models.ResponseJsonSchema(
                    name=response_format.get('json_schema', {}).get('name'),
                    description=response_format.get('json_schema', {}).get('description'),
                    schema=response_format.get('json_schema', {}).get('schema'),
                    is_strict=response_format.get('json_schema', {}).get('strict', False),
                )
            )
        else:
            raise ValueError("Unknown response format type:" + str(response_format))

    @staticmethod
    def to_cohere(response_format: completion_create_params.ResponseFormat):
        if isinstance(response_format, ResponseFormatText):
            return oci_models.CohereResponseTextFormat()
        elif isinstance(response_format, ResponseFormatJSONObject):
            return oci_models.CohereResponseJsonFormat()
        else:
            raise ValueError("Unknown response format type:" + str(response_format))


class MessageAdapter:
    def __init__(self,provider) -> None:
        self.provider = provider
    
    def convert(self,messages: List[ChatCompletionMessageParam]) -> List:
        if self.provider == "cohere":
            return self.to_cohere(messages)
        else:
            return self.to_generic(messages)
    
    @staticmethod
    def to_generic(messages: List[ChatCompletionMessageParam]) -> list[oci_models.Message]:
        """
        Convert OpenAI message to OCI Generic message.
        """
        new_msg_list = []
        for msg in messages:
            content = None
            if msg.get("content"):
                content = MessageAdapter.ContentAdapter.to_generic_content(msg["content"])
            # DeveloperMessage
            if msg["role"] == "developer":
                new_msg = oci_models.DeveloperMessage(content = content)
            # SystemMessage
            elif msg["role"] == "system":
                new_msg = oci_models.SystemMessage(content = content)
            # UserMessage
            elif msg["role"] == "user":
                new_msg = oci_models.UserMessage(content = content)
            # AssistantMessage
            elif msg["role"] == "assistant":
                new_msg = oci_models.AssistantMessage()
                if msg.get("tool_calls"):
                    new_msg.tool_calls = ToolAdapter.ToolCallAdapter.to_generic(msg["tool_calls"])
                elif content:
                    new_msg.content = content
            # ToolMessage
            elif msg["role"] == "tool":
                new_msg = ToolAdapter.ToolResultAdapter.to_generic(content, msg.get("tool_call_id"))
            # ChatCompletionFunctionMessageParam Deprecated and replaced by `tool_calls`.
            else:
                new_msg = None
                raise ValueError("Unknown message type:"+str(msg))
            if new_msg:
                new_msg_list.append(new_msg)
        return new_msg_list

    @staticmethod
    def to_cohere(messages: List[ChatCompletionMessageParam])-> list[oci_models.CohereMessage]:
        """
        Convert OpenAI messages to Cohere messages.
        """
        chatHistory,cohere_message,cohere_tool_results,preamble_override = None,"",None,None
        history, last_message = messages[:-1], messages[-1]
        openai_tool_calls = {}
        if history:
            chatHistory = []
            for i,message in enumerate(history):
                text = MessageAdapter.ContentAdapter.to_str(message["content"])
                if message["role"] == "system":
                    preamble_override = text
                else:
                    if message["role"] == "user":
                        new_msg = oci_models.CohereUserMessage(message = text)             
                    elif message["role"] == "assistant":
                        if message.get("tool_calls"):
                            new_tool_calls, tool_info = ToolAdapter.ToolCallAdapter.to_cohere(message["tool_calls"])
                            openai_tool_calls.update(tool_info)
                            new_msg = oci_models.CohereChatBotMessage(
                                message = text,
                                tool_calls = new_tool_calls
                                ) 
                        else:
                            new_msg = oci_models.CohereChatBotMessage(message = text)              

                    elif message["role"] == "tool":
                        new_tool_results = ToolAdapter.ToolResultAdapter.to_cohere(openai_tool_calls, message)
                        new_msg = oci_models.CohereToolMessage(
                            tool_results = new_tool_results
                        )                
                    chatHistory.append(new_msg)
        
        if last_message["role"] in ("user","assistant"):
            cohere_message = MessageAdapter.ContentAdapter.to_str(last_message["content"])
            
        elif last_message["role"] == "tool":
            cohere_tool_results = ToolAdapter.ToolResultAdapter.to_cohere(last_message.get("tool_call_id"),openai_tool_calls,last_message["content"])
        return chatHistory,cohere_message,cohere_tool_results,preamble_override


    class ContentAdapter:
        @staticmethod
        def to_generic_content(content: Union[str, List])-> list[oci_models.ChatContent]:
            """
            Convert OpenAI message content to OCI Generic message content.
            """
            contents = []
            if isinstance(content, str):
                content = oci_models.TextContent(type = "TEXT",text = content)
                return [content]
            elif isinstance(content, list):
                for each in content:
                    if each["type"] == "text":
                        contents.append(oci_models.TextContent(text = each["text"]))
                    elif each["type"] == "image_url":
                        contents.append(oci_models.ImageContent(image_url = each["image_url"]))
                    else:
                        raise ValueError("Unknown content type:",each)
                return contents

        @staticmethod
        def to_str(content: Union[str, List]) -> str:
            """
            Convert OpenAI message content to string.
            """
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                text = ""
                for c in content:
                    if c["type"] == "text":
                        text += " " + c["text"]
                return text

