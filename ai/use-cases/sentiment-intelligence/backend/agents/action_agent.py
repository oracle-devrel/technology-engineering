"""
Action Agent for Sentiment Intelligence.
Uses OCI GenAI (Cohere) to generate marketing action recommendations
based on sentiment analysis results and detected alerts.
"""

import asyncio
import json
import logging
from typing import Optional

import oci
from oci.generative_ai_inference import GenerativeAiInferenceClient
from oci.generative_ai_inference.models import (
    CohereChatRequest,
    OnDemandServingMode,
    ChatDetails,
)

from config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Marketing Strategy Advisor specializing in customer sentiment response.
Given sentiment analysis data, detected alerts, and optional web context, generate
prioritized, actionable marketing recommendations.

Categories for actions:
- crisis_response: Urgent actions for negative sentiment spikes or PR issues.
- campaign: Marketing campaigns to leverage positive sentiment or counter negative trends.
- product_improvement: Product/service changes suggested by customer feedback.
- engagement: Community engagement, social media responses, customer outreach.

For each recommendation, provide:
- action_text: A clear, specific action (1-2 sentences)
- priority: "critical", "high", "medium", or "low"
- impact: Expected impact description (1 sentence)
- category: One of the categories above
- estimated_effort: "low", "medium", or "high"

Return a JSON array of 5-8 recommendations ordered by priority. Return ONLY valid JSON, no markdown fences."""


class ActionAgent:
    """Generates marketing action recommendations based on sentiment analysis."""

    def __init__(self, oci_compartment_id: Optional[str] = None):
        self.compartment_id = oci_compartment_id or settings.OCI_COMPARTMENT_ID
        self.endpoint = settings.OCI_GENAI_ENDPOINT
        self.model_id = settings.OCI_GENAI_MODEL

        try:
            oci_config = oci.config.from_file()
            self.client = GenerativeAiInferenceClient(
                config=oci_config,
                service_endpoint=self.endpoint,
                timeout=(10, settings.ACTION_AGENT_TIMEOUT),
            )
            if not self.compartment_id:
                self.compartment_id = oci_config.get("tenancy")
            logger.info(
                "ActionAgent initialized with OCI GenAI endpoint=%s model=%s",
                self.endpoint,
                self.model_id,
            )
        except Exception as exc:
            logger.error("Failed to initialize OCI GenAI client: %s", exc, exc_info=True)
            raise RuntimeError(f"OCI GenAI client initialization failed: {exc}") from exc

    async def generate_actions(
        self,
        sentiment_summary: dict,
        alerts: Optional[list] = None,
        web_context: str = "",
    ) -> list[dict]:
        """
        Generate prioritized action recommendations.

        Args:
            sentiment_summary: Dashboard stats dict from AnalyticsAgent.
            alerts: List of alert dicts (type, severity, message).
            web_context: Additional web context string.

        Returns:
            List of action dicts with keys:
                action_text, priority, impact, category, estimated_effort
        """
        if alerts is None:
            alerts = []

        prompt = self._build_prompt(sentiment_summary, alerts, web_context)

        logger.info("Generating action recommendations...")

        try:
            chat_request = CohereChatRequest(
                message=prompt,
                max_tokens=3000,
                temperature=0.4,
                preamble_override=SYSTEM_PROMPT,
            )
            chat_details = ChatDetails(
                serving_mode=OnDemandServingMode(model_id=self.model_id),
                compartment_id=self.compartment_id,
                chat_request=chat_request,
            )

            # The OCI SDK call is blocking, so keep it off the FastAPI event loop.
            response = await asyncio.to_thread(
                self.client.chat,
                chat_details,
            )
            text = response.data.chat_response.text

            logger.debug("OCI GenAI action response (first 500 chars): %s", text[:500])

            actions = self._parse_actions(text)
            logger.info("Generated %d action recommendations.", len(actions))
            return actions

        except Exception as exc:
            logger.error("Failed to generate actions via OCI GenAI: %s", exc, exc_info=True)
            return self._fallback_actions(sentiment_summary, alerts)

    def _build_prompt(self, summary: dict, alerts: list, web_context: str) -> str:
        """Build the prompt with sentiment data, alerts, and web context."""
        dist = summary.get("sentiment_distribution", {})
        parts = [
            "Analyze the following customer sentiment data and generate action recommendations.\n",
            "=== SENTIMENT OVERVIEW ===",
            f"Total reviews analyzed: {dist.get('total', 0)}",
            f"Positive: {dist.get('positive_pct', 0)}%",
            f"Neutral: {dist.get('neutral_pct', 0)}%",
            f"Negative: {dist.get('negative_pct', 0)}%",
            f"Average score: {summary.get('avg_score', 0):.3f} (scale: -1.0 to 1.0)",
            "",
        ]

        # Top aspects
        aspects = summary.get("top_aspects", [])
        if aspects:
            parts.append("=== TOP ASPECTS MENTIONED ===")
            for asp in aspects[:10]:
                parts.append(
                    f"- {asp['aspect']}: {asp['sentiment']} (avg score {asp['avg_score']:.2f}, mentioned {asp['count']} times)"
                )
            parts.append("")

        # Emotions
        emotions = summary.get("emotion_distribution", [])
        if emotions:
            parts.append("=== DETECTED EMOTIONS ===")
            for em in emotions[:8]:
                parts.append(f"- {em['emotion']}: {em['count']} occurrences")
            parts.append("")

        # Source breakdown
        sources = summary.get("source_breakdown", [])
        if sources:
            parts.append("=== SOURCES ===")
            for src in sources[:8]:
                parts.append(
                    f"- {src['source']}: {src['count']} reviews, avg score {src['avg_score']:.2f}"
                )
            parts.append("")

        # Alerts
        if alerts:
            parts.append("=== ACTIVE ALERTS ===")
            for alert in alerts:
                summary = (
                    alert.get("description")
                    or alert.get("title")
                    or alert.get("message", "")
                )
                parts.append(
                    f"- [{alert.get('severity', 'info').upper()}] {summary}"
                )
            parts.append("")

        # Web context
        if web_context:
            parts.append("=== ADDITIONAL WEB CONTEXT ===")
            parts.append(web_context[:2000])
            parts.append("")

        parts.append("Generate action recommendations now.")
        return "\n".join(parts)

    def _parse_actions(self, text: str) -> list[dict]:
        """Parse the JSON array of actions from the LLM response."""
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines)

        try:
            actions = json.loads(cleaned)
            if isinstance(actions, list):
                return self._validate_actions(actions)
        except json.JSONDecodeError:
            # Try to find JSON array in the text
            start = cleaned.find("[")
            end = cleaned.rfind("]") + 1
            if start >= 0 and end > start:
                try:
                    actions = json.loads(cleaned[start:end])
                    if isinstance(actions, list):
                        return self._validate_actions(actions)
                except json.JSONDecodeError:
                    pass

        logger.warning("Failed to parse action recommendations JSON.")
        return []

    def _validate_actions(self, actions: list) -> list[dict]:
        """Validate and normalize action objects."""
        valid_priorities = {"critical", "high", "medium", "low"}
        valid_categories = {"crisis_response", "campaign", "product_improvement", "engagement"}
        valid_efforts = {"low", "medium", "high"}

        validated = []
        for a in actions:
            if not isinstance(a, dict) or "action_text" not in a:
                continue

            priority = str(a.get("priority", "medium")).lower()
            if priority not in valid_priorities:
                priority = "medium"

            category = str(a.get("category", "engagement")).lower()
            if category not in valid_categories:
                category = "engagement"

            effort = str(a.get("estimated_effort", "medium")).lower()
            if effort not in valid_efforts:
                effort = "medium"

            validated.append(
                {
                    "action_text": str(a["action_text"]),
                    "priority": priority,
                    "impact": str(a.get("impact", "Improves customer satisfaction.")),
                    "category": category,
                    "estimated_effort": effort,
                }
            )

        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        validated.sort(key=lambda x: priority_order.get(x["priority"], 2))
        return validated

    def _fallback_actions(self, summary: dict, alerts: list) -> list[dict]:
        """Generate generic fallback actions when LLM call fails."""
        logger.info("Using fallback action recommendations.")
        dist = summary.get("sentiment_distribution", {})
        neg_pct = dist.get("negative_pct", 0)

        actions = [
            {
                "action_text": "Review and respond to the most recent negative customer reviews to show brand responsiveness.",
                "priority": "high",
                "impact": "Demonstrates customer care and can turn detractors into promoters.",
                "category": "engagement",
                "estimated_effort": "low",
            },
            {
                "action_text": "Create a customer feedback summary report highlighting key themes from sentiment analysis.",
                "priority": "medium",
                "impact": "Provides data-driven insights for product and marketing teams.",
                "category": "product_improvement",
                "estimated_effort": "medium",
            },
            {
                "action_text": "Develop social media content that addresses the most common customer concerns identified.",
                "priority": "medium",
                "impact": "Proactively addresses issues and improves brand perception.",
                "category": "campaign",
                "estimated_effort": "medium",
            },
        ]

        if neg_pct > 40:
            actions.insert(
                0,
                {
                    "action_text": "URGENT: High negative sentiment detected. Initiate crisis communication review and escalate to leadership.",
                    "priority": "critical",
                    "impact": "Prevents further brand damage from unaddressed customer issues.",
                    "category": "crisis_response",
                    "estimated_effort": "high",
                },
            )

        if alerts:
            actions.append(
                {
                    "action_text": f"Address {len(alerts)} active alert(s) identified during sentiment monitoring.",
                    "priority": "high",
                    "impact": "Resolves flagged issues before they escalate.",
                    "category": "crisis_response",
                    "estimated_effort": "medium",
                }
            )

        return actions
