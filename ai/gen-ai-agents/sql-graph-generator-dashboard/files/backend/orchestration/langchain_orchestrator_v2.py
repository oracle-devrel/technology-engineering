"""
LangChain orchestrator using RunnableSequence for SQL Graph Dashboard
Router → branch(DATA_QUERY→OCI, CHART_EDIT→viz_edit, INSIGHT_QA→insight)
"""

from langchain_core.runnables import Runnable, RunnableLambda, RunnableBranch
from langchain_core.runnables.utils import Input, Output
from typing import Dict, Any, List, Optional
import base64
import json

from .oci_runnables import OciSqlAgentRunnable
from .oci_direct_runnables import RouterRunnable, VizGeneratorRunnable, InsightQARunnable
from .conversation_manager import ConversationManager
from tools.genai_chart_generator import GenAIChartGenerator


class ChartEditRunnable(Runnable):
    """
    Runnable for editing existing chart configurations
    """

    def invoke(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Modify existing chart based on user request
        """
        current_config = input_data.get("current_chart_config", {})
        question = input_data.get("question", "")
        data = input_data.get("data", [])

        # Simple chart type modifications
        if "pie" in question.lower():
            current_config["chart_type"] = "pie"
        elif "bar" in question.lower():
            current_config["chart_type"] = "bar"
        elif "line" in question.lower():
            current_config["chart_type"] = "line"
        elif "scatter" in question.lower():
            current_config["chart_type"] = "scatter"

        # Sorting modifications
        if "sort" in question.lower():
            if "desc" in question.lower() or "highest" in question.lower():
                current_config["sort_direction"] = "desc"
            else:
                current_config["sort_direction"] = "asc"

        return {
            "success": True,
            "config": current_config,
            "data": data,
            "method": "chart_edit",
            "response_type": "visualization"
        }


class InsightQARunnable(Runnable):
    """
    Runnable for generating insights about current data
    """

    def __init__(self):
        try:
            from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
            from langchain_core.messages import HumanMessage
            from utils import config

            self.genai_client = ChatOCIGenAI(
                model_id=config.MODEL_ID,
                service_endpoint=config.SERVICE_ENDPOINT,
                compartment_id=config.COMPARTMENT_ID,
                model_kwargs={
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 500
                }
            )
            self.oci_available = True
            print(" Insight QA Runnable initialized")
        except Exception as e:
            print(f"⚠️ Insight QA fallback mode: {e}")
            self.genai_client = None
            self.oci_available = False

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

        if self.oci_available:
            try:
                from langchain_core.messages import HumanMessage
                messages = [HumanMessage(content=prompt)]
                response = self.genai_client.invoke(messages)

                # Extract content
                if hasattr(response, 'content'):
                    insight_text = response.content
                else:
                    insight_text = str(response)

                return {
                    "success": True,
                    "text_response": insight_text,
                    "data": data,
                    "response_type": "text_response",
                    "method": "genai_analysis"
                }

            except Exception as e:
                print(f" Insight generation error: {e}")
                return self._fallback_insight(data, question)
        else:
            return self._fallback_insight(data, question)

    def _fallback_insight(self, data: List[Dict], question: str) -> Dict[str, Any]:
        """Generate simple fallback insights"""
        if not data:
            return {
                "success": True,
                "text_response": "No data available for analysis.",
                "response_type": "text_response"
            }

        insights = [
            f"Dataset contains {len(data)} records",
            f"Available fields: {', '.join(data[0].keys()) if data else 'None'}"
        ]

        # Simple numeric analysis
        numeric_fields = []
        for field in data[0].keys() if data else []:
            try:
                values = [float(row.get(field, 0)) for row in data[:10]]
                if values:
                    avg_val = sum(values) / len(values)
                    insights.append(f"{field} average: {avg_val:.2f}")
                    numeric_fields.append(field)
            except (ValueError, TypeError):
                pass

        if not numeric_fields:
            insights.append("No numeric fields found for statistical analysis.")

        return {
            "success": True,
            "text_response": "\n".join(insights),
            "data": data,
            "response_type": "text_response",
            "method": "fallback_analysis"
        }


class LangChainOrchestratorV2:
    """
    Clean LangChain orchestrator using RunnableSequence architecture
    """

    def __init__(self):
        print("🚀 Initializing LangChain Orchestrator V2...")

        # Initialize all runnables
        self.router = RouterRunnable()
        self.sql_agent = OciSqlAgentRunnable()
        self.viz_generator = VizGeneratorRunnable()
        self.chart_editor = ChartEditRunnable()
        self.insight_qa = InsightQARunnable()  # Now using direct OCI calls
        self.chart_generator = GenAIChartGenerator()

        # Conversation history manager
        self.conversation = ConversationManager()

        # Track current state (for backward compatibility)
        self.current_data = None
        self.current_chart_config = None

        print(" LangChain Orchestrator V2 initialized")

    def process_natural_language_query(self, user_question: str) -> Dict[str, Any]:
        """
        Main entry point - processes user query through the complete pipeline
        """
        try:
            print(f" Processing query: {user_question}")

            # Step 1: Route the query with conversation context
            route_input = {
                "question": user_question,
                "context": {
                    "has_data": self.conversation.has_data_context(),
                    "has_chart": self.conversation.has_chart_context(),
                    "conversation_history": self.conversation.get_context_for_prompt(3),
                    "data_summary": self.conversation.get_data_summary(),
                    "chart_summary": self.conversation.get_chart_summary()
                }
            }

            routing_result = self.router.invoke(route_input)
            route = routing_result.get("route", "DATA_QUERY")
            print(f" Router decision: {route} (confidence: {routing_result.get('confidence', 0.5)})")
            print(f" Reasoning: {routing_result.get('reasoning', 'No reasoning')}")

            # Step 2: Branch based on route
            if route == "DATA_QUERY":
                result = self._handle_data_query(user_question)
            elif route == "CHART_EDIT":
                result = self._handle_chart_edit(user_question)
            elif route == "INSIGHT_QA":
                result = self._handle_insight_qa(user_question)
            else:
                # Fallback to data query
                result = self._handle_data_query(user_question)

            # Step 3: Record this conversation turn
            self.conversation.add_turn(user_question, route, result)

            # Update backward compatibility state
            if result.get('data'):
                self.current_data = result['data']
            if result.get('chart_config'):
                self.current_chart_config = result['chart_config']

            return result

        except Exception as e:
            print(f" Orchestrator error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "response_type": "error"
            }

    def _handle_data_query(self, user_question: str) -> Dict[str, Any]:
        """
        Handle DATA_QUERY route: SQL Agent → Viz Generator → Chart Generator
        """
        try:
            # Step 1: Get data from OCI SQL Agent
            sql_input = {"question": user_question}
            sql_result = self.sql_agent.invoke(sql_input)

            if not sql_result.get("success", False):
                return {
                    "success": False,
                    "error": sql_result.get("error", "SQL query failed"),
                    "response_type": "error"
                }

            data = sql_result.get("data", [])
            if not data:
                return {
                    "success": True,
                    "query": user_question,
                    "agent_response": sql_result.get("agent_response", "No data found"),
                    "response_type": "text_response",
                    "text_response": sql_result.get("agent_response", "No data found"),
                    "data": []
                }

            # Update current state (conversation manager handles this)

            # DATA_QUERY only returns data - no automatic chart generation
            # Charts should only be created when explicitly requested via CHART_EDIT

            # Store data for conversation context
            self.current_data = data

            # Add to conversation history
            self.conversation.add_turn(user_question, "DATA_QUERY", {"data": data})

            # Return data without chart
            return {
                "success": True,
                "query": user_question,
                "agent_response": sql_result.get("agent_response", ""),
                "response_type": "data",
                "data": data,
                "generated_sql": sql_result.get("generated_sql"),
                "additional_info": sql_result.get("additional_info"),
                "method": "data_only"
            }

        except Exception as e:
            print(f" Data query handling error: {e}")
            return {
                "success": False,
                "error": str(e),
                "response_type": "error"
            }

    def _handle_chart_edit(self, user_question: str) -> Dict[str, Any]:
        """
        Handle CHART_EDIT route: modify existing chart
        """
        # Always get fresh data for chart requests to ensure we're using the right dataset
        print(" Getting fresh data for chart...")
        sql_input = {"question": user_question}
        sql_result = self.sql_agent.invoke(sql_input)

        if not sql_result.get("success", False):
            return {
                "success": False,
                "error": f"Failed to get data for chart: {sql_result.get('error', 'Unknown error')}",
                "response_type": "error"
            }

        current_data = sql_result.get("data", [])
        if not current_data:
            return {
                "success": False,
                "error": "No data available for chart creation",
                "response_type": "error"
            }

        # Store the new data
        self.current_data = current_data
        print(f" Retrieved {len(current_data)} rows for chart generation")

        # Get current chart config for potential reuse
        current_chart_config = self.conversation.get_current_chart_config()

        # If we have data but no chart config, create a new chart (don't redirect to data query)

        try:
            # Generate chart directly using GenAI Chart Generator
            chart_result = self.chart_generator.generate_chart(
                user_request=user_question,
                data=current_data,
                chart_params=current_chart_config or {}
            )

            if chart_result.get("success", False):
                # Store the chart config for future use
                self.current_chart_config = chart_result.get("chart_config", {})

                # Add to conversation history
                self.conversation.add_turn(user_question, "CHART_EDIT", {
                    "chart_config": chart_result.get("chart_config", {}),
                    "chart_base64": chart_result.get("chart_base64")
                })

                return {
                    "success": True,
                    "query": user_question,
                    "agent_response": f"Chart created: {user_question}",
                    "response_type": "visualization",
                    "data": current_data,
                    "chart_base64": chart_result.get("chart_base64"),
                    "chart_config": chart_result.get("chart_config", {}),
                    "method": f"chart_generated_+_{chart_result.get('method', 'unknown')}"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to update chart: {chart_result.get('error', 'Unknown error')}",
                    "response_type": "error"
                }

        except Exception as e:
            print(f" Chart edit handling error: {e}")
            return {
                "success": False,
                "error": str(e),
                "response_type": "error"
            }

    def _handle_insight_qa(self, user_question: str) -> Dict[str, Any]:
        """
        Handle INSIGHT_QA route: analyze current data
        """
        if not self.current_data:
            # No data to analyze, redirect to data query
            return self._handle_data_query(user_question)

        try:
            insight_input = {
                "question": user_question,
                "data": self.current_data
            }

            insight_result = self.insight_qa.invoke(insight_input)

            return {
                "success": insight_result.get("success", True),
                "query": user_question,
                "agent_response": insight_result.get("text_response", "No insights generated"),
                "response_type": "text_response",
                "text_response": insight_result.get("text_response", "No insights generated"),
                "data": self.current_data,
                "method": insight_result.get("method", "insight_analysis")
            }

        except Exception as e:
            print(f" Insight QA handling error: {e}")
            return {
                "success": False,
                "error": str(e),
                "response_type": "error"
            }

    def get_current_data(self) -> Optional[List[Dict]]:
        """Get current data for transparency"""
        return self.current_data

    def get_current_chart_config(self) -> Optional[Dict]:
        """Get current chart config for transparency"""
        return self.current_chart_config

    def clear_context(self):
        """Clear current context"""
        self.current_data = None
        self.current_chart_config = None
        print(" Context cleared")