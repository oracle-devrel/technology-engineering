"""
Conversation History Manager for Multi-Turn Conversational Flow
Tracks context across multiple GenAI calls for intelligent responses
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json


@dataclass
class ConversationTurn:
    """Single conversation turn with full context"""
    user_query: str
    route: str
    data: Optional[List[Dict]]
    chart_config: Optional[Dict]
    response_type: str
    agent_response: str
    generated_sql: Optional[str]
    chart_base64: Optional[str]
    timestamp: datetime
    success: bool
    method: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat(),
            'data_summary': {
                'count': len(self.data) if self.data else 0,
                'columns': list(self.data[0].keys()) if self.data else [],
                'sample': self.data[:2] if self.data else []
            } if self.data else None
        }

    def to_context_string(self) -> str:
        """Convert to concise context string for prompts"""
        context_parts = [
            f"Q: {self.user_query}",
            f"Route: {self.route}",
            f"Response: {self.agent_response[:100]}..." if len(self.agent_response) > 100 else f"Response: {self.agent_response}"
        ]

        if self.data:
            context_parts.append(f"Data: {len(self.data)} rows with columns {list(self.data[0].keys())}")

        if self.chart_config:
            chart_type = self.chart_config.get('chart_type', 'unknown')
            context_parts.append(f"Chart: {chart_type} chart created")

        return " | ".join(context_parts)


class ConversationManager:
    """
    Manages conversation history and context for multi-turn interactions
    """

    def __init__(self, max_history: int = 10):
        self.conversation_history: List[ConversationTurn] = []
        self.max_history = max_history
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    def add_turn(self,
                 user_query: str,
                 route: str,
                 result: Dict[str, Any]) -> None:
        """Add a new conversation turn"""

        turn = ConversationTurn(
            user_query=user_query,
            route=route,
            data=result.get('data'),
            chart_config=result.get('chart_config'),
            response_type=result.get('response_type', 'unknown'),
            agent_response=result.get('agent_response', ''),
            generated_sql=result.get('generated_sql'),
            chart_base64=result.get('chart_base64'),
            timestamp=datetime.now(),
            success=result.get('success', False),
            method=result.get('method', 'unknown')
        )

        self.conversation_history.append(turn)

        # Keep only recent history
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]

        print(f" Added conversation turn: {user_query} → {route}")

    def get_context_for_prompt(self, context_window: int = 3) -> str:
        """
        Get formatted conversation context for GenAI prompts
        """
        if not self.conversation_history:
            return "No previous conversation history."

        recent_turns = self.conversation_history[-context_window:] if context_window else self.conversation_history

        context_lines = ["Previous conversation context:"]
        for i, turn in enumerate(recent_turns, 1):
            context_lines.append(f"{i}. {turn.to_context_string()}")

        return "\n".join(context_lines)

    def get_current_data(self) -> Optional[List[Dict]]:
        """Get data from the most recent turn that has data"""
        for turn in reversed(self.conversation_history):
            if turn.data and turn.success:
                return turn.data
        return None

    def get_current_chart_config(self) -> Optional[Dict]:
        """Get chart config from the most recent turn that has a chart"""
        for turn in reversed(self.conversation_history):
            if turn.chart_config and turn.success:
                return turn.chart_config
        return None

    def get_current_chart_base64(self) -> Optional[str]:
        """Get the most recent chart image"""
        for turn in reversed(self.conversation_history):
            if turn.chart_base64 and turn.success:
                return turn.chart_base64
        return None

    def has_data_context(self) -> bool:
        """Check if we have data in recent context"""
        return self.get_current_data() is not None

    def has_chart_context(self) -> bool:
        """Check if we have a chart in recent context"""
        return self.get_current_chart_config() is not None

    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary of current data context"""
        data = self.get_current_data()
        if not data:
            return {"has_data": False}

        return {
            "has_data": True,
            "row_count": len(data),
            "columns": list(data[0].keys()) if data else [],
            "sample_row": data[0] if data else None
        }

    def get_chart_summary(self) -> Dict[str, Any]:
        """Get summary of current chart context"""
        chart_config = self.get_current_chart_config()
        if not chart_config:
            return {"has_chart": False}

        return {
            "has_chart": True,
            "chart_type": chart_config.get("chart_type", "unknown"),
            "x_axis": chart_config.get("x_axis", "unknown"),
            "y_axis": chart_config.get("y_axis", "unknown"),
            "title": chart_config.get("title", "")
        }

    def clear_history(self) -> None:
        """Clear conversation history"""
        self.conversation_history = []
        print(" Conversation history cleared")

    def export_history(self) -> List[Dict]:
        """Export conversation history as JSON-serializable format"""
        return [turn.to_dict() for turn in self.conversation_history]

    def get_recent_queries(self, count: int = 5) -> List[str]:
        """Get recent user queries for context"""
        recent_turns = self.conversation_history[-count:] if count else self.conversation_history
        return [turn.user_query for turn in recent_turns]

    def get_last_successful_sql(self) -> Optional[str]:
        """Get the most recent successful SQL query"""
        for turn in reversed(self.conversation_history):
            if turn.generated_sql and turn.success and turn.route == "DATA_QUERY":
                return turn.generated_sql
        return None

    def should_use_existing_data(self, user_query: str) -> bool:
        """
        Determine if the query can use existing data or needs new data
        """
        query_lower = user_query.lower()

        # Keywords that suggest working with existing data
        chart_keywords = ["chart", "graph", "plot", "visualize", "show", "display"]
        edit_keywords = ["change", "modify", "edit", "update", "make it", "convert to"]
        analysis_keywords = ["analyze", "explain", "what does", "tell me about", "insights", "trends"]

        has_data = self.has_data_context()

        # If we have data and query suggests chart/analysis work
        if has_data and any(keyword in query_lower for keyword in chart_keywords + edit_keywords + analysis_keywords):
            return True

        # If query explicitly asks for new data
        new_data_keywords = ["get", "find", "show me", "list", "select", "data"]
        specific_requests = ["orders", "customers", "products", "sales"]

        if any(keyword in query_lower for keyword in new_data_keywords + specific_requests):
            return False

        return has_data  # Default to using existing data if available