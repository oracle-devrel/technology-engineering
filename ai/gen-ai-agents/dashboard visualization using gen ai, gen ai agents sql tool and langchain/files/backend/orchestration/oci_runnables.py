"""
LangChain Runnables that wrap OCI SDK calls for clean integration
"""

from langchain_core.runnables import Runnable
try:
    from langchain_oci.chat_models import ChatOCIGenAI
except ImportError:
    try:
        from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
    except ImportError:
        print("⚠️ Neither langchain-oci nor langchain-community ChatOCIGenAI available")
        ChatOCIGenAI = None
from langchain_core.messages import HumanMessage
from typing import Dict, Any, List
import oci
from utils import config
import json

class OciSqlAgentRunnable(Runnable):
    """
    LangChain Runnable that wraps OCI Agent Runtime SDK to extract tool_outputs reliably
    """

    def __init__(self):
        # Initialize OCI Agent Runtime client
        try:
            oci_config = oci.config.from_file()
            # Override region to match the agent endpoint
            oci_config['region'] = 'eu-frankfurt-1'
            self.client = oci.generative_ai_agent_runtime.GenerativeAiAgentRuntimeClient(oci_config)
            self.agent_endpoint_id = config.AGENT_ENDPOINT_ID
            print("OCI SQL Agent Runnable initialized with eu-frankfurt-1")
        except Exception as e:
            print(f"Failed to initialize OCI Agent Runtime: {e}")
            self.client = None
            self.agent_endpoint_id = None

    def invoke(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call OCI Agent and extract tool_outputs[0].result for reliable data
        """
        user_question = input_data.get("question", "") if isinstance(input_data, dict) else str(input_data)

        if not self.client or not self.agent_endpoint_id:
            return {
                "success": False,
                "error": "OCI Agent Runtime not available",
                "data": [],
                "agent_response": "Agent not initialized"
            }

        try:
            print(f"OCI SQL Agent: Executing query: {user_question}")

            # Step 1: Create a session first (required for sessionId)
            create_session_response = self.client.create_session(
                create_session_details=oci.generative_ai_agent_runtime.models.CreateSessionDetails(
                    display_name="SQL Query Session",
                    description="Session for SQL query execution"
                ),
                agent_endpoint_id=self.agent_endpoint_id
            )
            session_id = create_session_response.data.id
            print(f"Created session: {session_id}")

            # Step 2: Create chat request with required sessionId
            chat_request = oci.generative_ai_agent_runtime.models.ChatDetails(
                user_message=user_question,
                session_id=session_id,
                should_stream=False
            )

            # Step 3: Call OCI Agent
            response = self.client.chat(
                agent_endpoint_id=self.agent_endpoint_id,
                chat_details=chat_request
            )

            # Extract message content
            message_content = ""
            if hasattr(response.data, 'message') and response.data.message:
                if hasattr(response.data.message, 'content') and response.data.message.content:
                    if hasattr(response.data.message.content, 'text'):
                        message_content = response.data.message.content.text or ""

            # Extract tool outputs (where SQL data lives)
            tool_outputs = getattr(response.data, 'tool_outputs', []) or []
            data = []
            generated_sql = None
            additional_info = None

            if tool_outputs and len(tool_outputs) > 0:
                result = tool_outputs[0].result if hasattr(tool_outputs[0], 'result') else None
                if result:
                    try:
                        # Parse JSON data from tool output
                        if isinstance(result, str):
                            parsed_result = json.loads(result)
                        else:
                            parsed_result = result

                        if isinstance(parsed_result, list):
                            data = parsed_result
                        elif isinstance(parsed_result, dict):
                            data = parsed_result.get('data', [])
                            generated_sql = parsed_result.get('generated_sql')
                            additional_info = parsed_result.get('additional_info')
                    except json.JSONDecodeError:
                        # If not JSON, treat as raw data
                        data = [{"result": result}]

            return {
                "success": True,
                "agent_response": message_content.strip(),
                "data": data,
                "generated_sql": generated_sql,
                "additional_info": additional_info,
                "tool_outputs": tool_outputs  # Pass through for transparency
            }

        except Exception as e:
            print(f"OCI SQL Agent error: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": [],
                "agent_response": f"Error calling SQL Agent: {str(e)}"
            }


class RouterRunnable(Runnable):
    """
    LangChain Runnable for intelligent routing using ChatOCIGenAI
    """

    def __init__(self):
        self.genai_client = None
        self.oci_available = False

        if ChatOCIGenAI is None:
            print("ChatOCIGenAI not available - Router using fallback")
            return

        try:
            self.genai_client = ChatOCIGenAI(
                model_id=config.MODEL_ID,
                service_endpoint=config.SERVICE_ENDPOINT,
                compartment_id=config.COMPARTMENT_ID,
                model_kwargs={
                    "temperature": config.TEMPERATURE,
                    "top_p": config.TOP_P,
                    "max_tokens": config.MAX_TOKENS
                }
            )
            self.oci_available = True
            print("Router Runnable with ChatOCIGenAI initialized")
        except Exception as e:
            print(f"Router Runnable fallback mode: {e}")
            self.genai_client = None
            self.oci_available = False

    def invoke(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route user query and return routing decision
        """
        user_question = input_data.get("question", "") if isinstance(input_data, dict) else str(input_data)
        context = input_data.get("context", {}) if isinstance(input_data, dict) else {}

        # Routing prompt
        prompt = f"""You are an intelligent router for a data dashboard. Analyze the user query and decide which tool to use.

Tools Available:
1. DATA_QUERY: For getting new data from database (show orders, get customers, etc.)
2. CHART_EDIT: For modifying existing charts (make it pie chart, sort by amount, etc.)
3. INSIGHT_QA: For analyzing current data (trends, patterns, outliers)

User Query: "{user_question}"

Respond with ONLY a JSON object:
{{
  "route": "DATA_QUERY|CHART_EDIT|INSIGHT_QA",
  "reasoning": "Brief explanation",
  "confidence": 0.0-1.0,
  "params": {{}}
}}"""

        if self.oci_available:
            try:
                messages = [HumanMessage(content=prompt)]
                response = self.genai_client.invoke(messages)

                # Extract content from response
                if hasattr(response, 'content'):
                    content = response.content
                else:
                    content = str(response)

                # Parse JSON response
                try:
                    import json
                    route_data = json.loads(content)
                    return {
                        "route": route_data.get("route", "DATA_QUERY"),
                        "reasoning": route_data.get("reasoning", "GenAI routing"),
                        "confidence": route_data.get("confidence", 0.9),
                        "params": route_data.get("params", {})
                    }
                except json.JSONDecodeError:
                    print(f"Failed to parse GenAI response: {content}")
                    return self._fallback_route(user_question)

            except Exception as e:
                print(f"GenAI routing error: {e}")
                return self._fallback_route(user_question)
        else:
            return self._fallback_route(user_question)

    def _fallback_route(self, user_question: str) -> Dict[str, Any]:
        """Simple rule-based fallback routing"""
        user_lower = user_question.lower()

        if any(word in user_lower for word in ["show", "get", "find", "list", "data"]):
            return {
                "route": "DATA_QUERY",
                "reasoning": "Fallback: Detected data request",
                "confidence": 0.5,
                "params": {}
            }
        elif any(word in user_lower for word in ["chart", "pie", "bar", "line", "graph"]):
            return {
                "route": "CHART_EDIT",
                "reasoning": "Fallback: Detected chart modification",
                "confidence": 0.5,
                "params": {}
            }
        else:
            return {
                "route": "INSIGHT_QA",
                "reasoning": "Fallback: Default to analysis",
                "confidence": 0.3,
                "params": {}
            }


class VizGeneratorRunnable(Runnable):
    """
    LangChain Runnable for generating visualization configs from data
    """

    def __init__(self):
        try:
            self.genai_client = ChatOCIGenAI(
                model_id=config.MODEL_ID,
                service_endpoint=config.SERVICE_ENDPOINT,
                compartment_id=config.COMPARTMENT_ID,
                model_kwargs={
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "max_tokens": 1000
                }
            )
            self.oci_available = True
            print("Viz Generator Runnable initialized")
        except Exception as e:
            print(f"Viz Generator fallback mode: {e}")
            self.genai_client = None
            self.oci_available = False

    def invoke(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate chart config from data and user question
        """
        data = input_data.get("data", [])
        question = input_data.get("question", "")
        suggested_type = input_data.get("chart_type", "auto")

        if not data:
            return {
                "success": False,
                "error": "No data provided for visualization"
            }

        # Analyze data structure
        sample_row = data[0] if data else {}
        columns = list(sample_row.keys()) if sample_row else []

        # Generate chart config prompt
        prompt = f"""Generate a chart configuration for this data visualization request.

User Question: "{question}"
Suggested Chart Type: {suggested_type}
Data Columns: {columns}
Data Sample (first 3 rows): {data[:3]}
Total Rows: {len(data)}

Respond with ONLY a JSON object:
{{
  "chart_type": "bar|line|pie|scatter",
  "x_axis": "column_name",
  "y_axis": "column_name",
  "title": "Chart Title",
  "caption": "Brief insight about the data",
  "color_field": "optional_column_for_colors"
}}"""

        if self.oci_available:
            try:
                messages = [HumanMessage(content=prompt)]
                response = self.genai_client.invoke(messages)

                # Extract content
                if hasattr(response, 'content'):
                    content = response.content
                else:
                    content = str(response)

                # Parse JSON response
                try:
                    import json
                    config_data = json.loads(content)
                    return {
                        "success": True,
                        "config": config_data,
                        "method": "genai_generated"
                    }
                except json.JSONDecodeError:
                    print(f"Failed to parse viz config: {content}")
                    return self._fallback_config(data, question)

            except Exception as e:
                print(f"Viz generation error: {e}")
                return self._fallback_config(data, question)
        else:
            return self._fallback_config(data, question)

    def _fallback_config(self, data: List[Dict], question: str) -> Dict[str, Any]:
        """Generate simple fallback chart config"""
        if not data:
            return {"success": False, "error": "No data"}

        sample_row = data[0]
        columns = list(sample_row.keys())

        # Find numeric columns
        numeric_cols = []
        for col in columns:
            try:
                float(str(sample_row[col]))
                numeric_cols.append(col)
            except (ValueError, TypeError):
                pass

        # Simple config generation
        if len(columns) >= 2:
            x_axis = columns[0]
            y_axis = numeric_cols[0] if numeric_cols else columns[1]
            chart_type = "bar"
        else:
            x_axis = columns[0]
            y_axis = columns[0]
            chart_type = "bar"

        return {
            "success": True,
            "config": {
                "chart_type": chart_type,
                "x_axis": x_axis,
                "y_axis": y_axis,
                "title": f"Chart for: {question}",
                "caption": "Fallback visualization configuration"
            },
            "method": "fallback"
        }