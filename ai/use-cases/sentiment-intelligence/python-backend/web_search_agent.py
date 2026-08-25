"""
Web Search Agent for Sentiment Intelligence.
Performs web searches via DuckDuckGo and scrapes top results to gather
customer reviews, forum posts, and news articles for sentiment analysis.
"""

import asyncio
import hashlib
import logging
import re
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from ddgs import DDGS

from config import settings
from web_source_agent import WebSourceAgent

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# Domain configuration
# -------------------------------------------------------------------

EXCLUDED_DOMAINS = {
    "slideshare.net",
    "slideplayer.com",
    "template.net",
    "powerpoint.com",
    "prezi.com",
    "pinterest.com",
    "youtube.com",
    "tiktok.com",
    "instagram.com",
    "facebook.com",
}

AUTHORITY_SCORES = {
    "trustpilot.com": 0.35,
    "g2.com": 0.30,
    "capterra.com": 0.30,
    "reddit.com": 0.25,
    "glassdoor.com": 0.25,
    "yelp.com": 0.25,
    "bbb.org": 0.22,
    "consumeraffairs.com": 0.22,
    "sitejabber.com": 0.22,
    "techcrunch.com": 0.20,
    "reuters.com": 0.20,
    "bloomberg.com": 0.20,
    "theverge.com": 0.20,
    "bbc.com": 0.20,
    "cnbc.com": 0.20,
    "forbes.com": 0.18,
    "nytimes.com": 0.18,
    "theguardian.com": 0.18,
    "wired.com": 0.18,
    "arstechnica.com": 0.18,
}

DOMAIN_NAMES = {
    "trustpilot.com": "Trustpilot",
    "g2.com": "G2",
    "capterra.com": "Capterra",
    "reddit.com": "Reddit",
    "glassdoor.com": "Glassdoor",
    "yelp.com": "Yelp",
    "bbb.org": "Better Business Bureau",
    "consumeraffairs.com": "ConsumerAffairs",
    "sitejabber.com": "Sitejabber",
    "techcrunch.com": "TechCrunch",
    "reuters.com": "Reuters",
    "bloomberg.com": "Bloomberg",
    "theverge.com": "The Verge",
    "bbc.com": "BBC",
    "cnbc.com": "CNBC",
    "forbes.com": "Forbes",
    "nytimes.com": "NY Times",
    "theguardian.com": "The Guardian",
    "wired.com": "Wired",
    "arstechnica.com": "Ars Technica",
}

MAX_SCRAPE_LENGTH = 8000  # characters per scraped page
SEARCH_RESULTS_PER_QUERY = settings.SEARCH_RESULTS_PER_QUERY
MAX_SEARCH_QUERIES = settings.MAX_SEARCH_QUERIES
MAX_TOTAL_RESULTS = settings.MAX_WEB_SEARCH_RESULTS
MAX_SCRAPE_TARGETS = settings.MAX_SCRAPE_TARGETS
MAX_RESULTS_PER_DOMAIN = 2  # keep scrape targets diverse across sites
SEARCH_CONCURRENCY = max(1, settings.WEB_SEARCH_CONCURRENCY)
SCRAPE_CONCURRENCY = max(1, settings.WEB_SCRAPE_CONCURRENCY)
SCRAPE_TIMEOUT = 12  # seconds per page


class WebSearchAgent:
    """Searches the web for customer sentiment content and optionally scrapes top results."""

    def __init__(self, oci_compartment_id: Optional[str] = None):
        self.source_agent = WebSourceAgent(oci_compartment_id=oci_compartment_id)
        logger.info("WebSearchAgent initialized.")

    async def search(
        self,
        query: str,
        hypothesis: str = "",
        scrape_content: bool = True,
        max_results: int = MAX_TOTAL_RESULTS,
    ) -> list[dict]:
        """
        Full pipeline: generate intents -> search DDGS -> filter/score -> optionally scrape.

        Args:
            query: The raw search topic string.
            hypothesis: A hypothesis about expected sentiment (used for query gen).
            scrape_content: Whether to scrape the top results for full text.
            max_results: Cap on total results returned.

        Returns:
            List of result dicts with keys:
                url, title, snippet, domain, domain_name, authority_score,
                relevance_score, scraped_text (if scrape_content=True),
                source_hash, searched_at
        """
        brand_topic = query

        # Step 1 - Generate smart search intents via OCI GenAI
        logger.info("Generating search intents for: %s", brand_topic)
        search_intents = await self.source_agent.generate_search_queries(
            topic=brand_topic,
            additional_context=hypothesis,
        )
        search_intents = search_intents[:MAX_SEARCH_QUERIES]
        logger.info("Received %d search intents.", len(search_intents))

        # Step 2 - Execute DDGS searches
        all_results = await self._execute_searches(search_intents)
        logger.info("Raw DDGS results collected: %d", len(all_results))

        # Step 2b - Fallback: if LLM-generated queries returned nothing, try simple direct queries
        if not all_results:
            logger.warning("All DDGS queries returned 0 results. Trying fallback direct queries...")
            fallback_intents = self._direct_fallback_queries(brand_topic)[
                :MAX_SEARCH_QUERIES
            ]
            all_results = await self._execute_searches(fallback_intents)
            logger.info("Fallback DDGS results collected: %d", len(all_results))

        # Step 3 - Deduplicate, filter, score
        scored = self._filter_and_score(all_results)
        scored = scored[:max_results]
        logger.info("Filtered + scored results: %d", len(scored))

        # Step 4 - Optionally scrape top results
        if scrape_content and scored:
            targets = scored[:MAX_SCRAPE_TARGETS]
            logger.info("Scraping top %d results...", len(targets))
            await self._scrape_results(targets)

        return scored

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _execute_searches(self, intents: list[dict]) -> list[dict]:
        """Run DuckDuckGo searches with bounded concurrency and aggregate results."""
        all_results: list[dict] = []
        seen_urls: set[str] = set()

        semaphore = asyncio.Semaphore(SEARCH_CONCURRENCY)

        async def execute_one(index: int, intent: dict) -> list[dict]:
            query_str = intent["query"]
            try:
                async with semaphore:
                    logger.info(
                        "DDGS query [%d/%d]: '%s'",
                        index + 1,
                        len(intents),
                        query_str,
                    )
                    # A fresh instance per query avoids sharing a blocking HTTP
                    # session across worker threads.
                    ddgs = DDGS()
                    results = await asyncio.to_thread(
                        ddgs.text,
                        query=query_str,
                        max_results=SEARCH_RESULTS_PER_QUERY,
                        backend="html",
                    )
                normalized = []
                for result in results or []:
                    normalized.append(
                        {
                            "url": result.get("href", result.get("link", "")),
                            "title": result.get("title", ""),
                            "snippet": result.get("body", result.get("snippet", "")),
                            "intent": intent.get("intent", ""),
                            "intent_priority": intent.get("priority", 3),
                        }
                    )
                logger.info(
                    "DDGS query [%d/%d] returned %d results.",
                    index + 1,
                    len(intents),
                    len(normalized),
                )
                return normalized
            except Exception as exc:
                logger.error("DDGS search failed for '%s': %s", query_str, exc, exc_info=True)
                return []

        batches = await asyncio.gather(
            *(execute_one(i, intent) for i, intent in enumerate(intents))
        )

        # Merge in intent priority order for deterministic ranking and dedupe.
        for batch in batches:
            for result in batch:
                url = result["url"]
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_results.append(result)

        return all_results

    @staticmethod
    def _direct_fallback_queries(brand_topic: str) -> list[dict]:
        """Simple direct queries used when LLM-generated queries all return 0 results."""
        # Extract brand name (first word or two before common keywords)
        brand = brand_topic.split(" customer ")[0].split(" review")[0].strip()
        return [
            {"query": f"{brand} reviews", "intent": "Direct review search", "priority": 1},
            {"query": f"{brand} customer experience", "intent": "Customer experience", "priority": 1},
            {"query": f"{brand} complaints", "intent": "Negative sentiment", "priority": 2},
            {"query": f"{brand} opinions reddit", "intent": "Reddit opinions", "priority": 2},
            {"query": f"{brand} trustpilot", "intent": "Trustpilot reviews", "priority": 2},
        ]

    def _filter_and_score(self, results: list[dict]) -> list[dict]:
        """Remove excluded domains, compute scores, sort by relevance."""
        scored: list[dict] = []

        for r in results:
            url = r["url"]
            domain = self._extract_domain(url)

            # Skip excluded domains
            if any(excl in domain for excl in EXCLUDED_DOMAINS):
                continue

            authority = 0.10  # default
            for auth_domain, auth_score in AUTHORITY_SCORES.items():
                if auth_domain in domain:
                    authority = auth_score
                    break

            # Combine authority with intent priority (lower priority number = higher score)
            priority_bonus = max(0, (6 - r.get("intent_priority", 3)) * 0.05)
            relevance_score = round(authority + priority_bonus, 3)

            domain_name = domain
            for dn_key, dn_val in DOMAIN_NAMES.items():
                if dn_key in domain:
                    domain_name = dn_val
                    break

            source_hash = hashlib.sha256(url.encode()).hexdigest()[:16]

            scored.append(
                {
                    "url": url,
                    "title": r["title"],
                    "snippet": r["snippet"],
                    "domain": domain,
                    "domain_name": domain_name,
                    "authority_score": authority,
                    "relevance_score": relevance_score,
                    "intent": r.get("intent", ""),
                    "source_hash": source_hash,
                    "searched_at": datetime.now(timezone.utc).isoformat(),
                    "scraped_text": None,
                }
            )

        scored.sort(key=lambda x: x["relevance_score"], reverse=True)

        # Cap results per domain so a single high-authority but scrape-hostile
        # site (e.g. Trustpilot 403s all bots) cannot monopolize the limited
        # scrape slots and starve the pipeline of ingestible reviews.
        diversified: list[dict] = []
        per_domain: dict[str, int] = {}
        for item in scored:
            d = item["domain"]
            if per_domain.get(d, 0) >= MAX_RESULTS_PER_DOMAIN:
                continue
            per_domain[d] = per_domain.get(d, 0) + 1
            diversified.append(item)
        return diversified

    async def _scrape_results(self, results: list[dict]) -> None:
        """Scrape result URLs concurrently with one reusable HTTP client."""
        semaphore = asyncio.Semaphore(SCRAPE_CONCURRENCY)
        async with httpx.AsyncClient(
            timeout=SCRAPE_TIMEOUT,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                ),
                "Accept": (
                    "text/html,application/xhtml+xml,application/xml;q=0.9,"
                    "image/avif,image/webp,*/*;q=0.8"
                ),
                "Accept-Language": "en-US,en;q=0.9",
            },
        ) as client:
            tasks = [self._scrape_one(r, client, semaphore) for r in results]
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _scrape_one(
        self,
        result: dict,
        client: httpx.AsyncClient,
        semaphore: asyncio.Semaphore,
    ) -> None:
        """Scrape a single URL and update the result dict in-place."""
        url = result["url"]
        try:
            async with semaphore:
                resp = await client.get(url)
                resp.raise_for_status()

                soup = BeautifulSoup(resp.text, "lxml")

                # Remove noise elements
                for tag in soup(["script", "style", "nav", "header", "footer", "aside", "noscript", "iframe"]):
                    tag.decompose()

                text = soup.get_text(separator="\n", strip=True)
                # Collapse whitespace
                text = re.sub(r"\n{3,}", "\n\n", text)
                text = text[:MAX_SCRAPE_LENGTH]

                result["scraped_text"] = text
                logger.debug("Scraped %d chars from %s", len(text), url)

        except Exception as exc:
            logger.warning("Failed to scrape %s: %s", url, exc)
            result["scraped_text"] = None

    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract the domain from a URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except Exception:
            return ""
