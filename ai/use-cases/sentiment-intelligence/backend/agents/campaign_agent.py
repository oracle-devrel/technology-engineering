"""
Campaign Agent for Sentiment Intelligence.
Uses OCI GenAI (Cohere) to generate personalized marketing email variants
based on sentiment analysis insights for a brand.
"""

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

SYSTEM_PROMPT = """You are a Marketing Content Strategist specializing in data-driven campaigns.
Given customer sentiment analysis data for a brand, generate personalized marketing email variants
that address real customer feelings and feedback.

You will receive:
- Brand name and campaign objective
- Sentiment analysis data (positive/negative distribution, top aspects, emotions, alerts)
- Desired communication tone

Generate exactly 3 email variants. For each variant, provide:
- variant_label: "A", "B", or "C"
- subject: A compelling email subject line (max 60 chars)
- body: Email body text (2-3 short paragraphs, natural and engaging)
- predicted_open_rate: Estimated open rate as a number (e.g., 32.5)
- rationale: One sentence explaining why this variant should work

The FIRST variant (A) should be your best recommendation.
Each variant should take a different angle but all should reference real insights from the data.
Make the content feel authentic and data-informed, not generic.

Return a JSON array of 3 variant objects. Return ONLY valid JSON, no markdown fences."""


CAMPAIGN_OBJECTIVES = {
    "customer_reactivation": "Win back lapsed customers based on sentiment insights",
    "new_product_launch": "Announce a new product addressing customer feedback",
    "loyalty_reminder": "Engage loyal customers with personalized appreciation",
    "seasonal_sale": "Drive seasonal sales with sentiment-informed messaging",
    "feedback_request": "Request customer feedback building on sentiment trends",
}

TONES = {
    "warm_personal": "Warm & Personal",
    "urgent_exclusive": "Urgent & Exclusive",
    "playful_casual": "Playful & Casual",
    "professional_confident": "Professional & Confident",
}


class CampaignAgent:
    """Generates personalized marketing campaign variants using OCI GenAI."""

    def __init__(self, oci_compartment_id: Optional[str] = None):
        self.compartment_id = oci_compartment_id or settings.OCI_COMPARTMENT_ID
        self.endpoint = settings.OCI_GENAI_ENDPOINT
        self.model_id = settings.OCI_GENAI_MODEL

        try:
            oci_config = oci.config.from_file()
            self.client = GenerativeAiInferenceClient(
                config=oci_config,
                service_endpoint=self.endpoint,
            )
            if not self.compartment_id:
                self.compartment_id = oci_config.get("tenancy")
            logger.info(
                "CampaignAgent initialized with OCI GenAI endpoint=%s model=%s",
                self.endpoint,
                self.model_id,
            )
        except Exception as exc:
            logger.error("Failed to initialize OCI GenAI client: %s", exc, exc_info=True)
            raise RuntimeError(f"OCI GenAI client initialization failed: {exc}") from exc

    async def generate_campaign(
        self,
        brand: str,
        campaign_objective: str = "customer_reactivation",
        tone: str = "warm_personal",
        sentiment_context: Optional[dict] = None,
    ) -> list[dict]:
        """
        Generate 3 marketing email variants informed by sentiment data.

        Args:
            brand: Brand name.
            campaign_objective: Key from CAMPAIGN_OBJECTIVES.
            tone: Key from TONES.
            sentiment_context: Dashboard stats dict from AnalyticsAgent.

        Returns:
            List of variant dicts with keys:
                variant_label, subject, body, predicted_open_rate, rationale, tone
        """
        if sentiment_context is None:
            sentiment_context = {}

        prompt = self._build_prompt(brand, campaign_objective, tone, sentiment_context)
        logger.info("Generating campaign variants for brand='%s' objective='%s'", brand, campaign_objective)

        try:
            chat_request = CohereChatRequest(
                message=prompt,
                max_tokens=3000,
                temperature=0.6,
                preamble_override=SYSTEM_PROMPT,
            )
            chat_details = ChatDetails(
                serving_mode=OnDemandServingMode(model_id=self.model_id),
                compartment_id=self.compartment_id,
                chat_request=chat_request,
            )

            response = self.client.chat(chat_details)
            text = response.data.chat_response.text

            logger.debug("OCI GenAI campaign response (first 500 chars): %s", text[:500])

            variants = self._parse_variants(text, tone)
            logger.info("Generated %d campaign variants.", len(variants))
            return variants

        except Exception as exc:
            logger.error("Failed to generate campaign via OCI GenAI: %s", exc, exc_info=True)
            return self._fallback_variants(brand, campaign_objective, tone)

    def _build_prompt(self, brand: str, objective: str, tone: str, context: dict) -> str:
        """Build the prompt with brand info, objective, tone, and sentiment data."""
        obj_desc = CAMPAIGN_OBJECTIVES.get(objective, objective)
        tone_desc = TONES.get(tone, tone)

        parts = [
            f"Generate 3 marketing email variants for the brand '{brand}'.\n",
            f"=== CAMPAIGN BRIEF ===",
            f"Objective: {obj_desc}",
            f"Desired tone: {tone_desc}",
            "",
        ]

        # Sentiment overview
        dist = context.get("sentiment_distribution", {})
        if dist:
            parts.append("=== SENTIMENT OVERVIEW ===")
            parts.append(f"Total reviews analyzed: {dist.get('total', 0)}")
            parts.append(f"Positive: {dist.get('positive_pct', 0)}%")
            parts.append(f"Neutral: {dist.get('neutral_pct', 0)}%")
            parts.append(f"Negative: {dist.get('negative_pct', 0)}%")
            parts.append(f"Average score: {context.get('avg_score', 0):.3f} (scale: -1.0 to 1.0)")
            parts.append("")

        # Top aspects
        aspects = context.get("top_aspects", [])
        if aspects:
            parts.append("=== WHAT CUSTOMERS TALK ABOUT ===")
            for asp in aspects[:8]:
                parts.append(
                    f"- {asp['aspect']}: {asp['sentiment']} (score {asp['avg_score']:.2f}, {asp['count']} mentions)"
                )
            parts.append("")

        # Emotions
        emotions = context.get("emotion_distribution", [])
        if emotions:
            parts.append("=== CUSTOMER EMOTIONS ===")
            for em in emotions[:6]:
                parts.append(f"- {em['emotion']}: {em['count']} occurrences")
            parts.append("")

        # Source breakdown
        sources = context.get("source_breakdown", [])
        if sources:
            parts.append("=== REVIEW SOURCES ===")
            for src in sources[:5]:
                parts.append(f"- {src['source']}: {src['count']} reviews")
            parts.append("")

        # Alerts
        alerts = context.get("alerts", [])
        if alerts:
            parts.append("=== ACTIVE ALERTS ===")
            for alert in alerts[:3]:
                parts.append(f"- [{alert.get('severity', 'info').upper()}] {alert.get('title', '')}")
            parts.append("")

        parts.append(
            "Use the sentiment insights above to craft emails that feel data-informed and authentic. "
            "Reference specific aspects, emotions, or trends where relevant. "
            "Generate the 3 email variants now."
        )
        return "\n".join(parts)

    def _parse_variants(self, text: str, tone: str) -> list[dict]:
        """Parse the JSON array of variants from the LLM response."""
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines)

        try:
            variants = json.loads(cleaned)
            if isinstance(variants, list):
                return self._validate_variants(variants, tone)
        except json.JSONDecodeError:
            start = cleaned.find("[")
            end = cleaned.rfind("]") + 1
            if start >= 0 and end > start:
                try:
                    variants = json.loads(cleaned[start:end])
                    if isinstance(variants, list):
                        return self._validate_variants(variants, tone)
                except json.JSONDecodeError:
                    pass

        logger.warning("Failed to parse campaign variants JSON.")
        return []

    def _validate_variants(self, variants: list, tone: str) -> list[dict]:
        """Validate and normalize variant objects."""
        labels = ["A", "B", "C"]
        validated = []
        for i, v in enumerate(variants[:3]):
            if not isinstance(v, dict) or "subject" not in v:
                continue
            validated.append({
                "variant_label": v.get("variant_label", labels[i] if i < 3 else str(i + 1)),
                "subject": str(v.get("subject", "")),
                "body": str(v.get("body", "")),
                "tone": TONES.get(tone, tone),
                "predicted_open_rate": float(v.get("predicted_open_rate", 20 + i * 5)),
                "rationale": str(v.get("rationale", "")),
            })
        return validated

    def _fallback_variants(self, brand: str, objective: str, tone: str) -> list[dict]:
        """Generate generic fallback variants when OCI GenAI call fails."""
        logger.info("Using fallback campaign variants.")
        tone_desc = TONES.get(tone, tone)
        return [
            {
                "variant_label": "A",
                "subject": f"We've been listening, {brand} community",
                "body": (
                    f"At {brand}, your voice matters. We've analyzed thousands of customer reviews "
                    f"and the feedback is clear — you love our commitment to quality, and we're "
                    f"doubling down on what makes us great.\n\n"
                    f"Stay tuned for exciting updates inspired by your input. "
                    f"As a thank you for being part of our community, enjoy an exclusive preview."
                ),
                "tone": tone_desc,
                "predicted_open_rate": 28.5,
                "rationale": "Acknowledges customer feedback directly, creating a sense of being heard.",
            },
            {
                "variant_label": "B",
                "subject": f"Your feedback shaped what's next at {brand}",
                "body": (
                    f"Every review, every comment, every piece of feedback — we read them all. "
                    f"And we've been busy turning your insights into action.\n\n"
                    f"From product improvements to new experiences, discover how {brand} is "
                    f"evolving based on what matters most to you."
                ),
                "tone": tone_desc,
                "predicted_open_rate": 24.2,
                "rationale": "Positions the brand as responsive and customer-centric.",
            },
            {
                "variant_label": "C",
                "subject": f"Something new from {brand} — just for you",
                "body": (
                    f"We know what our customers love — and what they wish was better. "
                    f"That's why we're excited to share something special.\n\n"
                    f"Based on real customer insights, we've crafted an experience "
                    f"that addresses your top requests. Check it out."
                ),
                "tone": tone_desc,
                "predicted_open_rate": 21.8,
                "rationale": "Creates curiosity while signaling data-driven improvements.",
            },
        ]
