from typing import Literal
from datetime import datetime
from oci.generative_ai_inference import models as oci_models

from openai.types.chat.chat_completion_message import ChatCompletionMessage

from openai.types.chat.chat_completion import (
    ChatCompletion, 
    Choice
)

from openai.types.chat.chat_completion_chunk import (
    ChatCompletionChunk, 
    Choice as ChoiceChunk,
    ChoiceDelta
)

from openai.types.completion_usage import (
    CompletionUsage, 
    CompletionTokensDetails, 
    PromptTokensDetails
)

from api.models.adapter.tool_adapter import ToolAdapter



class ResponseAdapter:
    def __init__(self,provider):
        self.provider = provider


    def to_openai(self, message_id: str, model: str,
                  response: oci_models.GenericChatResponse
                          | oci_models.CohereChatResponse
                  ) -> ChatCompletion:
        openai_choices = []
        if self.provider == "cohere":
            openai_choices.append(
                Choice(
                    index=0,
                    logprobs=None,
                    message=MessageAdapter(self.provider).to_openai(response),
                    finish_reason=FinishReasonAdapter.to_openai(response.finish_reason)
                )
            )
        else:
            for choice in response.choices:
                openai_choices.append(
                    Choice(
                        index=0,
                        logprobs=None,
                        message=MessageAdapter(self.provider).to_openai(choice.message),
                        finish_reason=FinishReasonAdapter.to_openai(choice.finish_reason)
                    )
                )

        usage = UsageAdapter.from_oci_usage(response.usage)

        if hasattr(response, 'time_created'):
            created = int(response.time_created.timestamp())
        else:
            created = int(datetime.now().timestamp())

        return ChatCompletion(
            id=message_id,
            model=model,
            created=created,
            object="chat.completion",
            choices=openai_choices,
            usage=usage,
            system_fingerprint=None,
            service_tier=None
        )

    def to_openai_chunk(self, message_id: str, model: str, chunk: dict) -> ChatCompletionChunk:
        index = chunk.get("index", 0)
        created = int(chunk.get("time_created", datetime.now()).timestamp())
        finish_reason = FinishReasonAdapter.to_openai(chunk.get("finishReason"))
        usage = UsageAdapter.from_chunk_usage(chunk.get("usage"))
        delta = MessageAdapter(self.provider).from_chunk_message(chunk)        

        return ChatCompletionChunk(
            id=message_id,
            model=model,
            created=created,
            object="chat.completion.chunk",
            choices=[ChoiceChunk(index=index, logprobs=None, finish_reason=finish_reason, delta=delta)],
            usage=usage,
            system_fingerprint=None,
            service_tier=None
        )


class FinishReasonAdapter:
    _MAPPING = {
        "tool_use": "tool_calls",
        "COMPLETE": "stop",
        "ERROR_TOXIC": "content_filter",
        "ERROR_LIMIT": "stop",
        "ERROR": "stop",
        "USER_CANCEL": "stop",
        "MAX_TOKENS": "length",
    }

    @classmethod
    def to_openai(cls, finish_reason) -> Literal["stop", "length", "tool_calls", "content_filter", "function_call"] | None:
        if not finish_reason:
            return None
        return cls._MAPPING.get(finish_reason, finish_reason)

class MessageAdapter:
    """Convert different provider messages into OpenAI ChatCompletionMessage"""

    def __init__(self,provider):
        self.provider = provider
        
    def to_openai(self, message) -> ChatCompletionMessage:
        if self.provider == "cohere":
            return MessageAdapter.from_cohere(message)
        else:
            return MessageAdapter.from_generic(message)

    @staticmethod
    def from_generic(message: oci_models.Message) -> ChatCompletionMessage:
        chat_completion_message = ChatCompletionMessage(role="assistant", content=None, tool_calls=[])
        if message.content:
            chat_completion_message.content = message.content[0].text

        if message.tool_calls:
            chat_completion_message.content = ""
            chat_completion_message.tool_calls = ToolAdapter.ToolCallAdapter.to_openai(message.tool_calls)
        return chat_completion_message

    @staticmethod
    def from_cohere(response: oci_models.CohereChatResponse) -> ChatCompletionMessage:
        chat_completion_message = ChatCompletionMessage(role="assistant", content=None, tool_calls=None)
        if response.text:
            chat_completion_message.content = response.text
        if response.tool_calls:
            chat_completion_message.content = ""
            chat_completion_message.tool_calls = ToolAdapter.ToolCallAdapter.to_openai(response.tool_calls)
        return chat_completion_message

    @staticmethod
    def from_chunk_message(chunk: dict) -> ChoiceDelta:
        choice_delta = ChoiceDelta(
            role="assistant", 
            refusal=''
            )
        if chunk.get("message"):
            message = chunk["message"]
        else:
            message = chunk
        if message.get("toolCalls"):
            # Avoid duplicate tool calls for Cohere model
            if not message.get("finishReason"):
                choice_delta.tool_calls = []
                for i, tool_call in enumerate(message.get("toolCalls")):
                    choice_delta.tool_calls.append(
                        ToolAdapter.ToolCallAdapter.to_openai_delta(i, tool_call)
                    )
        elif message.get("content"):
            choice_delta.content = message["content"][0]["text"]
        elif message.get("text"):
            # Avoid duplicate content for Cohere model
            if not message.get("finishReason"):
                choice_delta.content = message["text"]
        return choice_delta


class UsageAdapter:
    @staticmethod
    def from_oci_usage(usage) -> CompletionUsage:
        if usage.completion_tokens_details:
            completion_tokens_details = CompletionTokensDetails(
                accepted_prediction_tokens=usage.completion_tokens_details.accepted_prediction_tokens,
                reasoning_tokens=usage.completion_tokens_details.reasoning_tokens,
                rejected_prediction_tokens=usage.completion_tokens_details.rejected_prediction_tokens,
                audio_tokens=None
            )
        else:
            completion_tokens_details = None

        if usage.prompt_tokens_details:
            prompt_tokens_details = PromptTokensDetails(
                cached_tokens=usage.prompt_tokens_details.cached_tokens,
                audio_tokens=None
            )
        else:
            prompt_tokens_details = None

        return CompletionUsage(
            completion_tokens=usage.completion_tokens,
            prompt_tokens=usage.prompt_tokens,
            total_tokens=usage.total_tokens,
            completion_tokens_details=completion_tokens_details,
            prompt_tokens_details=prompt_tokens_details
        )

    @staticmethod
    def from_chunk_usage(usage_dict: dict | None) -> CompletionUsage | None:
        completion_tokens_details = None
        prompt_tokens_details = None

        if not usage_dict:
            return None
        
        if usage_dict.get("completionTokensDetails"):
            completion_tokens_details = CompletionTokensDetails(
                accepted_prediction_tokens=usage_dict["completionTokensDetails"].get("acceptedPredictionTokens"),
                reasoning_tokens=usage_dict["completionTokensDetails"].get("reasoningTokens"),
                rejected_prediction_tokens=None,
                audio_tokens=None
            )
            
        if usage_dict.get("promptTokensDetails"):
            prompt_tokens_details = PromptTokensDetails(
                cached_tokens=usage_dict["promptTokensDetails"].get("cachedTokens"),
                audio_tokens=None
            )
            

        return CompletionUsage(
            completion_tokens=usage_dict.get("completionTokens"),
            prompt_tokens=usage_dict.get("promptTokens"),
            total_tokens=usage_dict.get("totalTokens"),
            completion_tokens_details=completion_tokens_details,
            prompt_tokens_details=prompt_tokens_details
        )
