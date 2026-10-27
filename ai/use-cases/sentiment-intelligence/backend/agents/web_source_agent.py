"""
Web Source Agent for Sentiment Intelligence.
Uses OCI GenAI (Cohere) to generate intelligent search queries focused on
customer reviews, social media sentiment, forums, and news about a brand/product.
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

SYSTEM_PROMPT = """You are a Customer Sentiment Research Strategist. Your job is to generate
highly effective web search queries that will find authentic customer reviews, social media
discussions, forum posts, and news articles about a given brand or product.

Guidelines:
- Focus on finding REAL customer opinions and experiences, not marketing content.
- Target review platforms: Trustpilot, G2, Capterra, Yelp, Glassdoor.
- Target social/forum platforms: Reddit, Twitter/X, Quora, specialized forums.
- Target news: tech news sites, business news, consumer reports.
- Generate queries that capture BOTH positive and negative sentiment.
- Include queries for recent trends, complaints, and praise.
- Consider industry-specific review sources when relevant.

Output format: Return a JSON array of search query objects, each with:
{
  "query": "the search query string",
  "intent": "what this query aims to find",
  "priority": 1-5 (1 = highest priority)
}

Return between 5 and 10 queries, ordered by priority. Return ONLY valid JSON, no markdown fences."""


class WebSourceAgent:
    """Generates smart search queries for sentiment research using OCI GenAI."""

    def __init__(self, oci_compartment_id: Optional[str] = None):
        self.compartment_id = oci_compartment_id or settings.OCI_COMPARTMENT_ID
        self.endpoint = settings.OCI_GENAI_ENDPOINT
        self.model_id = settings.OCI_GENAI_MODEL

        try:
            oci_config = oci.config.from_file()
            self.client = GenerativeAiInferenceClient(
                config=oci_config,
                service_endpoint=self.endpoint,
                timeout=(10, settings.WEB_SOURCE_AGENT_TIMEOUT),
            )
            if not self.compartment_id:
                self.compartment_id = oci_config.get("tenancy")
            logger.info(
                "WebSourceAgent initialized with OCI GenAI endpoint=%s model=%s",
                self.endpoint,
                self.model_id,
            )
        except Exception as exc:
            logger.error("Failed to initialize OCI GenAI client: %s", exc, exc_info=True)
            raise RuntimeError(f"OCI GenAI client initialization failed: {exc}") from exc

    async def generate_search_queries(
        self,
        topic: str,
        brand: str = "",
        additional_context: str = "",
    ) -> list[dict]:
        """
        Generate a list of search query objects using OCI GenAI (Cohere).

        Args:
            topic: The subject to research (e.g., "product quality", "customer service").
            brand: The brand name to research.
            additional_context: Extra context to guide query generation.

        Returns:
            List of dicts with keys: query, intent, priority.
        """
        prompt = (
            f"Generate web search queries to research customer sentiment about: "
            f"Brand='{brand}', Topic='{topic}'.\n"
        )
        if additional_context:
            prompt += f"Additional context: {additional_context}\n"

        prompt += (
            "\nPreferred domains to target in queries:\n"
            "- trustpilot.com (consumer reviews)\n"
            "- g2.com (software/B2B reviews)\n"
            "- capterra.com (software reviews)\n"
            "- reddit.com (community discussions)\n"
            "- glassdoor.com (employee/company reviews)\n"
            "- yelp.com (local business reviews)\n"
            "- news sites (TechCrunch, Reuters, Bloomberg, The Verge)\n"
            "\nGenerate the search queries now."
        )

        logger.info("Generating search queries for brand='%s' topic='%s'", brand, topic)

        try:
            chat_request = CohereChatRequest(
                message=prompt,
                max_tokens=2048,
                temperature=0.3,
                preamble_override=SYSTEM_PROMPT,
            )
            chat_details = ChatDetails(
                serving_mode=OnDemandServingMode(model_id=self.model_id),
                compartment_id=self.compartment_id,
                chat_request=chat_request,
            )

            # OCI's Python SDK is synchronous. Run it off the event loop so SSE
            # progress and other API requests remain responsive while it waits.
            response = await asyncio.to_thread(
                self.client.chat,
                chat_details,
            )
            text = response.data.chat_response.text

            logger.debug("OCI GenAI raw response: %s", text[:500])

            queries = self._parse_queries(text)
            if not queries:
                logger.warning("LLM returned no parseable queries, using fallback.")
                return self._fallback_queries(topic, brand)
            logger.info("Generated %d search queries.", len(queries))
            return queries

        except Exception as exc:
            logger.error(
                "Failed to generate search queries via OCI GenAI: %s", exc, exc_info=True
            )
            return self._fallback_queries(topic, brand)

    def _parse_queries(self, text: str) -> list[dict]:
        """Parse the JSON array of queries from the LLM response."""
        # Strip markdown code fences if present
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines)

        try:
            queries = json.loads(cleaned)
            if isinstance(queries, list):
                # Validate each query has the expected keys
                validated = []
                for q in queries:
                    if isinstance(q, dict) and "query" in q:
                        validated.append(
                            {
                                "query": q["query"],
                                "intent": q.get("intent", "general sentiment"),
                                "priority": q.get("priority", 3),
                            }
                        )
                return sorted(validated, key=lambda x: x["priority"])
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM response as JSON, using fallback.")

        return []

    def _fallback_queries(self, topic: str, brand: str) -> list[dict]:
        """Return default search queries when LLM generation fails."""
        logger.info("Using fallback search queries for brand='%s' topic='%s'", brand, topic)
        return [
            {
                "query": f"{brand} {topic} customer reviews",
                "intent": "General customer reviews",
                "priority": 1,
            },
            {
                "query": f"{brand} {topic} site:trustpilot.com",
                "intent": "Trustpilot reviews",
                "priority": 1,
            },
            {
                "query": f"{brand} {topic} site:reddit.com",
                "intent": "Reddit discussions",
                "priority": 2,
            },
            {
                "query": f"{brand} {topic} complaints OR problems OR issues",
                "intent": "Negative sentiment discovery",
                "priority": 2,
            },
            {
                "query": f"{brand} {topic} review 2025 2026",
                "intent": "Recent reviews",
                "priority": 3,
            },
            {
                "query": f"{brand} {topic} site:g2.com OR site:capterra.com",
                "intent": "B2B review platforms",
                "priority": 3,
            },
            {
                "query": f'"{brand}" {topic} customer experience feedback',
                "intent": "Customer experience feedback",
                "priority": 4,
            },
        ]
