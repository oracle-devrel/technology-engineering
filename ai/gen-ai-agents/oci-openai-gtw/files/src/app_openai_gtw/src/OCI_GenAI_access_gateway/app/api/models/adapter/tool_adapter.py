import json
from typing import List, Union
from oci.generative_ai_inference import models as oci_models
from openai.types.chat import (
    ChatCompletionFunctionToolParam,
    ChatCompletionMessageFunctionToolCall
)

from openai.types.chat.chat_completion_chunk import (
    ChoiceDeltaToolCall,
    ChoiceDeltaToolCallFunction
)

from openai.types.chat.chat_completion_message_function_tool_call import (
    Function
)

class ToolAdapter:
    class ToolsDefinitionAdapter:
        @staticmethod
        def to_generic(tools: List[ChatCompletionFunctionToolParam]) -> List[oci_models.FunctionDefinition]:
            """
            Convert OpenAI tools to OCI Generic tools.
            """
            new_tools = []
            for tool in tools:
                if isinstance(tool, dict):            
                    name = tool["function"]["name"]
                    description = tool["function"]["description"]
                    parameters = tool["function"]["parameters"]           
                else:
                    name = tool.function.name
                    description = tool.function.description
                    parameters = tool.function.parameters

                new_tools.append(
                    oci_models.FunctionDefinition(
                        name = name,
                        description = description,
                        parameters = parameters
                    )
                )
            return new_tools

        @staticmethod
        def to_cohere(tools: List[ChatCompletionFunctionToolParam]) -> List[oci_models.CohereTool]:
            """
            Convert OpenAI tools to OCI Cohere tools.
            """
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
            new_tools = []
            for tool in tools:
                if isinstance(tool, dict):
                    name = tool["function"]["name"]
                    description = tool["function"]["description"]
                    parameters_schema = tool["function"]["parameters"]
                else:
                    name = tool.function.name
                    description = tool.function.description
                    parameters_schema = tool.function.parameters     
                    
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

                new_tools.append(
                    oci_models.CohereTool(
                        name = name,
                        description = description,
                        parameter_definitions = parameter_definitions
                        )
                )
            return new_tools

    class ToolCallAdapter:
        @staticmethod
        def to_generic(tool_calls: List) -> List[oci_models.ToolCall]:
            """
            Convert OpenAI tool calls to OCI Generic tool calls.
            """
            new_tool_calls = []
            for tool_call in tool_calls:
                if isinstance(tool_call, dict):
                    new_tool_call = oci_models.FunctionCall(
                        id = tool_call["id"],
                        name = tool_call["function"]["name"],
                        arguments = str(tool_call["function"]["arguments"])
                        )
                else:
                    new_tool_call = oci_models.FunctionCall(
                        id = tool_call.id,
                        name = tool_call.function.name,
                        arguments = str(tool_call.function.arguments)
                        )
                new_tool_calls.append(new_tool_call)
            return new_tool_calls

        @staticmethod
        def to_cohere(tool_calls: List) -> tuple[List[oci_models.CohereToolCall], dict]:
            """
            Convert OpenAI tool calls to Cohere tool calls.
            """
            new_tool_calls = []
            tool_info = {}
            for tool_call in tool_calls:
                if isinstance(tool_call, dict):
                    id = tool_call["function"]["name"]
                    name = tool_call["function"]["name"]
                    arguments = str(tool_call["function"]["arguments"])
                else:
                    id = tool_call.function.name
                    name = tool_call.function.name
                    arguments = str(tool_call.function.arguments)
                if isinstance(arguments,str):
                    arguments = json.loads(arguments)
                new_tool_calls.append(
                    oci_models.CohereToolCall(
                        name = name,
                        parameters = arguments
                        )
                    )
                tool_info[id] = {"name": name, "arguments": arguments}
            return new_tool_calls, tool_info

        @staticmethod
        def to_openai(tool_calls: List[oci_models.ToolCall]) -> List[ChatCompletionMessageFunctionToolCall]:
            openai_tool_calls = []
            for call in tool_calls:
                if isinstance(call, dict):
                    name = call["name"]
                    id = call.get("id", name)
                    arguments = str(call["parameters"]) if call.get("parameters") else call["arguments"]
                else:                    
                    name = call.name
                    id = call.id if hasattr(call, "id") else call.name
                    arguments = call.arguments if hasattr(call, "arguments") else call.parameters
                if isinstance(arguments, dict):
                    arguments = json.dumps(arguments)
                openai_tool_calls.append(
                    ChatCompletionMessageFunctionToolCall(
                        id=id,
                        type="function",
                        function=Function(
                            name=name, 
                            arguments=arguments
                            )
                    )
                )
            return openai_tool_calls

        @staticmethod
        def to_openai_delta(index: int, tool_call: dict) -> ChoiceDeltaToolCall:
            tool_index = tool_call.get("index", index)
            tool_delta = ChoiceDeltaToolCall(
                type="function",
                index=tool_index,
                id=tool_call.get("id", tool_call.get("name")),
                function=ChoiceDeltaToolCallFunction(
                    name=tool_call.get("name"),
                    arguments=str(tool_call.get("arguments",tool_call.get("parameters")))
                )
            )
            return tool_delta

    class ToolResultAdapter:
        @staticmethod
        def to_generic(content, tool_call_id) -> List[oci_models.ToolMessage]:
            new_msg = oci_models.ToolMessage(content = content)
            if tool_call_id:
                new_msg.tool_call_id = tool_call_id
            return new_msg

        @staticmethod
        def to_cohere(tool_call_id: str,openai_tool_calls: dict, content: Union[str, List]) -> List[oci_models.CohereToolResult]:
            """
            Convert OpenAI tool result to Cohere tool result.
            """            
            result = ToolAdapter.ToolResultAdapter.content_to_str(content)    
            new_tool_result = oci_models.CohereToolResult(
                    call = oci_models.CohereToolCall(
                        name = openai_tool_calls[tool_call_id]["name"],
                        parameters = openai_tool_calls[tool_call_id]["arguments"]
                    ),
                    outputs  = [{"result": result}]
                    )
            return [new_tool_result]

        @staticmethod
        def content_to_str(content: Union[str, List]) -> str:
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