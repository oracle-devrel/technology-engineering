"""
LangChain Runnables using direct OCI SDK calls for GenAI models
Pure OCI SDK wrapped as LangChain Runnables - no langchain-community dependencies
"""

from langchain_core.runnables import Runnable
from typing import Dict, Any, List
import oci
import json
from utils import config


class OciGenAIRunnable(Runnable):
    """
    Direct OCI GenAI model calls wrapped as LangChain Runnable
    """

    def __init__(self, purpose: str = "general"):
        self.purpose = purpose
        try:
            # Initialize OCI GenAI client with correct endpoint
            oci_config = oci.config.from_file()
            # Override endpoint to match the model's region
            oci_config['region'] = 'eu-frankfurt-1'
            self.genai_client = oci.generative_ai_inference.GenerativeAiInferenceClient(oci_config)

            # Set correct service endpoint
            self.genai_client.base_client.endpoint = config.SERVICE_ENDPOINT

            self.model_id = config.MODEL_ID
            self.service_endpoint = config.SERVICE_ENDPOINT
            self.compartment_id = config.COMPARTMENT_ID
            self.oci_available = True
            print(f"OCI GenAI Direct Runnable ({purpose}) initialized with endpoint: {config.SERVICE_ENDPOINT}")
        except Exception as e:
            print(f"OCI GenAI Direct Runnable ({purpose}) failed: {e}")
            self.genai_client = None
            self.oci_available = False

    def invoke(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call OCI GenAI model directly
        """
        prompt = input_data.get("prompt", "")
        max_tokens = input_data.get("max_tokens", 500)
        temperature = input_data.get("temperature", 0.7)

        if not self.oci_available:
            return {
                "success": False,
                "error": "OCI GenAI not available",
                "response": "",
                "method": "error"
            }

        try:
            # Create chat request using Oracle demo format for OpenAI GPT OSS 120B
            content = oci.generative_ai_inference.models.TextContent()
            content.text = prompt

            message = oci.generative_ai_inference.models.Message()
            message.role = "USER"
            message.content = [content]

            chat_request = oci.generative_ai_inference.models.GenericChatRequest()
            chat_request.api_format = oci.generative_ai_inference.models.BaseChatRequest.API_FORMAT_GENERIC
            chat_request.messages = [message]
            chat_request.max_tokens = max_tokens
            chat_request.temperature = temperature
            chat_request.frequency_penalty = 0
            chat_request.presence_penalty = 0
            chat_request.top_p = 1
            chat_request.top_k = 0

            chat_detail = oci.generative_ai_inference.models.ChatDetails()
            chat_detail.serving_mode = oci.generative_ai_inference.models.OnDemandServingMode(model_id=self.model_id)
            chat_detail.chat_request = chat_request
            chat_detail.compartment_id = self.compartment_id

            # Call OCI GenAI
            response = self.genai_client.chat(chat_detail)

            # Extract response text
            response_text = ""
            if hasattr(response.data, 'chat_response') and response.data.chat_response:
                if hasattr(response.data.chat_response, 'choices') and response.data.chat_response.choices:
                    choice = response.data.chat_response.choices[0]
                    if hasattr(choice, 'message') and choice.message:
                        if hasattr(choice.message, 'content') and choice.message.content:
                            for content in choice.message.content:
                                if hasattr(content, 'text'):
                                    response_text += content.text

            return {
                "success": True,
                "response": response_text.strip(),
                "method": "oci_direct",
                "model_id": self.model_id
            }

        except Exception as e:
            error_msg = str(e)
            print(f"OCI GenAI Direct call failed ({self.purpose}): {error_msg}")

            # Check for specific error types
            if "does not support" in error_msg:
                return {
                    "success": False,
                    "error": f"Model {self.model_id} API format incompatible",
                    "response": "",
                    "method": "model_error"
                }

            return {
                "success": False,
                "error": error_msg,
                "response": "",
                "method": "call_error"
            }


class RouterRunnable(Runnable):
    """
    Intelligent routing using direct OCI GenAI calls
    """

    def __init__(self):
        self.genai_runnable = OciGenAIRunnable("router")

    def invoke(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route user query and return routing decision
        """
        user_question = input_data.get("question", "")
        context = input_data.get("context", {})

        # Create routing prompt
        prompt = f"""You are an intelligent router for a data dashboard. Analyze the user query and decide which tool to use.

Tools Available:
1. DATA_QUERY: For getting NEW data from database (show orders, get customers, list products, etc.)
2. CHART_EDIT: For creating ANY charts or visualizations (make chart, graph, pie chart, bar chart, etc.) - Will automatically get data if needed
3. INSIGHT_QA: For analyzing current data (trends, patterns, outliers)

IMPORTANT: If user asks for ANY chart/graph/visualization, always choose CHART_EDIT regardless of whether data exists or not.

Context:
- Has existing data: {context.get('has_data', False)}
- Has existing chart: {context.get('has_chart', False)}

User Query: "{user_question}"

Respond with ONLY a JSON object:
{{"route": "DATA_QUERY|CHART_EDIT|INSIGHT_QA", "reasoning": "Brief explanation", "confidence": 0.0-1.0}}"""

        if not self.genai_runnable.oci_available:
            return self._fallback_route(user_question)

        # Call OCI GenAI
        genai_input = {
            "prompt": prompt,
            "max_tokens": 200,
            "temperature": 0.3
        }

        result = self.genai_runnable.invoke(genai_input)

        if result.get("success"):
            try:
                # Parse JSON response
                route_data = json.loads(result["response"])
                return {
                    "route": route_data.get("route", "DATA_QUERY"),
                    "reasoning": route_data.get("reasoning", "GenAI routing"),
                    "confidence": route_data.get("confidence", 0.9),
                    "method": "oci_genai"
                }
            except json.JSONDecodeError:
                print(f"Failed to parse GenAI response: {result['response']}")
                return self._fallback_route(user_question)
        else:
            print(f"GenAI routing failed: {result.get('error')}")
            return self._fallback_route(user_question)

    def _fallback_route(self, user_question: str) -> Dict[str, Any]:
        """Simple rule-based fallback routing"""
        user_lower = user_question.lower()

        if any(word in user_lower for word in ["show", "get", "find", "list", "data"]):
            return {
                "route": "DATA_QUERY",
                "reasoning": "Fallback: Detected data request",
                "confidence": 0.5,
                "method": "fallback"
            }
        elif any(word in user_lower for word in ["chart", "pie", "bar", "line", "graph"]):
            return {
                "route": "CHART_EDIT",
                "reasoning": "Fallback: Detected chart modification",
                "confidence": 0.5,
                "method": "fallback"
            }
        else:
            return {
                "route": "INSIGHT_QA",
                "reasoning": "Fallback: Default to analysis",
                "confidence": 0.3,
                "method": "fallback"
            }


class VizGeneratorRunnable(Runnable):
    """
    Generate visualization configs using direct OCI GenAI calls
    """

    def __init__(self):
        self.genai_runnable = OciGenAIRunnable("viz_generator")

    def invoke(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate chart config from data and user question
        """
        data = input_data.get("data", [])
        question = input_data.get("question", "")

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
Data Columns: {columns}
Data Sample (first 2 rows): {data[:2]}
Total Rows: {len(data)}

Respond with ONLY a JSON object:
{{"chart_type": "bar|line|pie|scatter", "x_axis": "column_name", "y_axis": "column_name", "title": "Chart Title", "caption": "Brief insight"}}"""

        if not self.genai_runnable.oci_available:
            return self._fallback_config(data, question)

        # Call OCI GenAI
        genai_input = {
            "prompt": prompt,
            "max_tokens": 300,
            "temperature": 0.3
        }

        result = self.genai_runnable.invoke(genai_input)

        if result.get("success"):
            try:
                # Parse JSON response
                config_data = json.loads(result["response"])
                return {
                    "success": True,
                    "config": config_data,
                    "method": "oci_genai"
                }
            except json.JSONDecodeError:
                print(f"Failed to parse viz config: {result['response']}")
                return self._fallback_config(data, question)
        else:
            print(f"Viz generation failed: {result.get('error')}")
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


class InsightQARunnable(Runnable):
    """
    Generate insights using direct OCI GenAI calls
    """

    def __init__(self):
        self.genai_runnable = OciGenAIRunnable("insight_qa")

    def invoke(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate insights about the current data
        """
        data = input_data.get("data", [])
        question = input_data.get("question", "")

        if not data:
            return {
                "success": False,
                "error": "No data available for analysis",
                "response_type": "text_response"
            }

        # Create analysis prompt
        data_summary = {
            "total_rows": len(data),
            "columns": list(data[0].keys()) if data else [],
            "sample_data": data[:3]
        }

        prompt = f"""Analyze this data and answer the user's question with insights.

User Question: "{question}"

Data Summary:
- Total rows: {data_summary['total_rows']}
- Columns: {data_summary['columns']}
- Sample data: {data_summary['sample_data']}

Provide a concise analysis with specific insights, trends, or patterns you observe in the data.
"""

        if not self.genai_runnable.oci_available:
            return self._fallback_insight(data, question)

        # Call OCI GenAI
        genai_input = {
            "prompt": prompt,
            "max_tokens": 400,
            "temperature": 0.7
        }

        result = self.genai_runnable.invoke(genai_input)

        if result.get("success"):
            return {
                "success": True,
                "text_response": result["response"],
                "data": data,
                "response_type": "text_response",
                "method": "oci_genai"
            }
        else:
            print(f"⚠️ Insight generation failed: {result.get('error')}")
            return self._fallback_insight(data, question)

    def _fallback_insight(self, data: List[Dict], question: str) -> Dict[str, Any]:
        """Generate simple fallback insights"""
        if not data:
            return {
                "success": True,
                "text_response": "No data available for analysis.",
                "response_type": "text_response",
                "method": "fallback"
            }

        insights = [
            f"Dataset contains {len(data)} records",
            f"Available fields: {', '.join(data[0].keys()) if data else 'None'}"
        ]

        # Simple numeric analysis
        for field in data[0].keys() if data else []:
            try:
                values = [float(row.get(field, 0)) for row in data[:10]]
                if values:
                    avg_val = sum(values) / len(values)
                    insights.append(f"{field} average: {avg_val:.2f}")
            except (ValueError, TypeError):
                pass

        return {
            "success": True,
            "text_response": "\n".join(insights),
            "data": data,
            "response_type": "text_response",
            "method": "fallback"
        }