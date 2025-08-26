import time
from typing import Literal, Iterable

from pydantic import BaseModel, Field

import oci
from oci.generative_ai_inference import models as oci_models
import json
import uuid
import base64


class Model(BaseModel):
    id: str
    created: int = Field(default_factory=lambda: int(time.time()))
    object: str | None = "model"
    owned_by: str | None = "ocigenerativeai"


class Models(BaseModel):
    object: str | None = "list"
    data: list[Model] = []


class ResponseFunction(BaseModel):
    name: str | None = None
    arguments: str


class ToolCall(BaseModel):
    index: int | None = None
    id: str | None = None
    type: Literal["function"] = "function"
    function: ResponseFunction


class TextContent(BaseModel):
    type: Literal["text"] = "text"
    text: str


class ImageUrl(BaseModel):
    url: str
    detail: str | None = "auto"


class ImageContent(BaseModel):
    type: Literal["image_url"] = "image"
    image_url: ImageUrl


class SystemMessage(BaseModel):
    name: str | None = None
    role: Literal["system"] = "system"
    content: str | None = None


class UserMessage(BaseModel):
    name: str | None = None
    role: Literal["user"] = "user"
    content: str | list[TextContent | ImageContent]


class AssistantMessage(BaseModel):
    name: str | None = None
    role: Literal["assistant"] = "assistant"
    content: str | None = None
    tool_calls: list[ToolCall] | None = None


class ToolMessage(BaseModel):
    role: Literal["tool"] = "tool"
    content: str
    tool_call_id: str


class Function(BaseModel):
    name: str
    description: str | None = None
    parameters: object


class Tool(BaseModel):
    type: Literal["function"] = "function"
    function: Function


class StreamOptions(BaseModel):
    include_usage: bool = True


class ChatRequest(BaseModel):
    messages: list[SystemMessage | UserMessage | AssistantMessage | ToolMessage]
    model: str
    frequency_penalty: float | None = Field(default=None, le=2.0, ge=-2.0)  # Not used
    presence_penalty: float | None = Field(default=None, le=2.0, ge=-2.0)  # Not used
    stream: bool | None = False
    stream_options: StreamOptions | None = None
    temperature: float | None = Field(default=None, le=2.0, ge=0.0)
    top_p: float | None = Field(default=None, le=1.0, ge=0.0)
    user: str | None = None  # Not used
    max_tokens: int | None = 2048
    n: int | None = 1  # Not used
    tools: list[Tool] | None = None
    tool_choice: str | object = "auto"


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatResponseMessage(BaseModel):
    # tool_calls
    role: Literal["assistant"] | None = None
    content: str | None = None
    tool_calls: list[ToolCall] | None = None


class BaseChoice(BaseModel):
    index: int | None = 0
    finish_reason: str | None = None
    logprobs: dict | None = None


class Choice(BaseChoice):
    message: ChatResponseMessage


class ChoiceDelta(BaseChoice):
    delta: ChatResponseMessage


class BaseChatResponse(BaseModel):
    # id: str = Field(default_factory=lambda: "chatcmpl-" + str(uuid.uuid4())[:8])
    id: str
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    system_fingerprint: str = "fp"


class ChatResponse(BaseChatResponse):
    choices: list[Choice]
    object: Literal["chat.completion"] = "chat.completion"
    usage: Usage


class ChatStreamResponse(BaseChatResponse):
    choices: list[ChoiceDelta]
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    usage: Usage | None = None


class EmbeddingsRequest(BaseModel):
    input: str | list[str] | Iterable[int | Iterable[int]]
    model: str
    encoding_format: Literal["float", "base64"] = "float"
    dimensions: int | None = None  # not used.
    user: str | None = None  # not used.


class Embedding(BaseModel):
    object: Literal["embedding"] = "embedding"
    embedding: list[float] | bytes
    index: int


class EmbeddingsUsage(BaseModel):
    prompt_tokens: int
    total_tokens: int


class EmbeddingsResponse(BaseModel):
    object: Literal["list"] = "list"
    data: list[Embedding]
    model: str
    usage: EmbeddingsUsage


type_mapping = {
            "array": "list",
            "boolean": "bool",
            "null": "NoneType",
            "integer": "int",
            "number": "float",
            "object": "dict",
            "regular expressions": "str",
            "string": "str"
        }

class Convertor:
    def __init__(self):        
        pass
        
    @staticmethod
    def convert_tools_openai_to_cohere(openai_tools: list) -> list[oci_models.CohereTool]:
        """
        Convert a list of OpenAI tool definitions into OCI Cohere tool objects.
        """
        cohere_tools = []    
        
        for tool in openai_tools:
            # if tool.get("type") == "function":
            func = tool.function
            name = func.name.replace("-","_")
            description = func.description
            parameters_schema = func.parameters     
                
            properties = parameters_schema.get("properties", {})
            required = parameters_schema.get("required", [])

            # Iterate through each property to build parameter definitions
            parameter_definitions = {}
            for param_name, param_schema in properties.items():
                is_required = param_name in required
                # Map the OpenAI JSON schema type to the Python type using type_mapping
                openai_type = param_schema.get("type", "string")
                mapped_type = type_mapping.get(openai_type, "str")
                param_description = param_schema.get("description", "")
                parameter_definitions[param_name] = oci_models.CohereParameterDefinition(
                    is_required = is_required,
                    type = mapped_type,
                    description = param_description
                    )
            
            cohere_tool = oci_models.CohereTool(
                name = name,
                description = description,
                parameter_definitions = parameter_definitions
                )
            cohere_tools.append(cohere_tool)
        
        return cohere_tools
    
    @staticmethod
    def convert_tools_openai_to_llama(openai_tools: list) -> list[oci_models.FunctionDefinition]:
        """
        Convert a list of OpenAI tool definitions into OCI Llama tool objects.
        """
        llama_tools = []
        for tool in openai_tools:
            llama_tool = oci_models.FunctionDefinition(
                type = "FUNCTION",
                name = tool.function.name,
                description = tool.function.description,
                parameters = tool.function.parameters
            )
            llama_tools.append(llama_tool)        
        return llama_tools
    
    @staticmethod
    def convert_tool_calls_cohere_to_openai(cohere_tool_calls) -> list[ToolCall]:
        """
        Convert a list of Cohere tool calls into a list of OpenAI tool calls.        
        Returns: list: List of OpenAI tool call dictionaries.
        """
        openai_tool_calls = []
        for call in cohere_tool_calls:

            # MODYFIKACJA 
            try:
                name = call["name"].replace("_", "-")
                arguments = json.dumps(call["parameters"])
            except (TypeError, KeyError):
                name = call.name.replace("_", "-")
                arguments = json.dumps(call.parameters)

            function = ResponseFunction(
                name=name,
                arguments=arguments
            )
            # MODYFIKACJA 
            
            # Generate a unique id for the OpenAI tool call
            tool_id = base64.b64encode(json.dumps(function.model_dump()).encode())

            openai_call = ToolCall(
                index = len(openai_tool_calls),
                id = tool_id,
                type = "function",
                function = function
                )
            openai_tool_calls.append(openai_call)
        return openai_tool_calls

    @staticmethod
    def convert_tool_calls_llama_to_openai(llama_tool_calls) -> list[ToolCall]:
        """
        Convert a list of Llama tool calls into a list of OpenAI tool calls.        
        Returns: list: List of OpenAI tool call dictionaries.
        """
        openai_tool_calls = []
        for call in llama_tool_calls:
            openai_call = ToolCall(
                index = len(openai_tool_calls),
                id = call.id,
                type = "function",
                function = ResponseFunction(
                    name = call.name,
                    arguments = call.arguments
                    )
                )
            openai_tool_calls.append(openai_call)
        return openai_tool_calls
        
    @staticmethod
    def convert_tool_calls_openai_to_cohere(openai_tool_calls) -> list[oci_models.CohereToolCall]:
        """
        Convert a list of OpenAI tool calls into a list of Cohere tool calls.
        Returns: list: List of Cohere tool call dictionaries.
        """
        cohere_tool_calls = []
        for call in openai_tool_calls:
            function_data = call.function
            # Parse the JSON string from the "arguments" field
            try:
                parameters = json.loads(function_data.arguments)
            except json.JSONDecodeError:
                parameters = {}
            cohere_tool_call = oci_models.CohereToolCall(
                name = function_data.name,
                parameters = parameters
                )
        cohere_tool_calls.append(cohere_tool_call)
        return cohere_tool_calls

    @staticmethod
    def convert_tool_calls_openai_to_llama(openai_tool_calls) -> list[oci_models.FunctionCall]:
        """
        Convert a list of OpenAI tool calls into a list of Llama tool calls.
        """                            
        llama_tool_calls = []
        for call in openai_tool_calls:
            function_data = call.function
            llama_tool_call = oci_models.FunctionCall(
                id = call.id,
                type = "FUNCTION",
                name = function_data.name,
                arguments = function_data.arguments
                )
            llama_tool_calls.append(llama_tool_call)
        return llama_tool_calls
    
    @staticmethod
    def convert_tool_result_openai_to_llama(openai_tool_message) -> list[oci_models.CohereToolCall]:
        """
        Convert an OpenAI tool message into an OCI ToolMessage object.
        """
        llama_message = oci_models.ToolMessage(
            role = "TOOL",
            tool_call_id = openai_tool_message.get("tool_call_id",""),
            content = [oci_models.TextContent(
                type = "TEXT",
                text = openai_tool_message.get("content",""))]
                )
        return llama_message
    
    @staticmethod
    def convert_tool_result_openai_to_cohere(openai_tool_message: dict) -> oci_models.CohereToolResult:
        """
        Convert an OpenAI tool result message into an OCI CohereToolResult object.
        """
        tool_id = openai_tool_message.get("tool_call_id", "{}")
        func = json.loads(base64.b64decode(tool_id))
        print(func)
        cohere_tool_call = oci_models.CohereToolCall(
            name = func["name"],
            parameters = json.loads(func["arguments"]),
            )
        cohere_tool_result = oci_models.CohereToolResult(
            call = cohere_tool_call,
            outputs = [{"result": openai_tool_message.get("content", "")}]
            )
        return cohere_tool_result
