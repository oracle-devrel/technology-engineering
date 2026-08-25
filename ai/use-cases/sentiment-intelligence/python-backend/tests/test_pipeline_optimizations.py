import asyncio
import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from agents import web_search_agent
from config import settings
from orchestrator import SentimentOrchestrator
from agents.sentiment_agent import SentimentAgent
from agents.web_search_agent import WebSearchAgent


class SentimentConcurrencyTests(unittest.IsolatedAsyncioTestCase):
    async def test_analysis_is_bounded_and_keeps_requested_scope(self):
        agent = SentimentAgent()
        rows = [
            (index, f"review {index}", "Source", f"Author {index}", "Product")
            for index in range(1, 6)
        ]
        active = 0
        max_active = 0
        lock = threading.Lock()

        def analyze(row):
            nonlocal active, max_active
            with lock:
                active += 1
                max_active = max(max_active, active)
            time.sleep(0.03)
            with lock:
                active -= 1
            return {
                "review_id": row[0],
                "sentiment": "Positive",
                "score": 0.5,
                "_label": f"review {row[0]}",
            }

        fetch = Mock(return_value=rows)
        progress = []
        with (
            patch.object(settings, "SENTIMENT_CONCURRENCY", 2),
            patch.object(agent, "_fetch_reviews", fetch),
            patch.object(agent, "_analyze_and_persist_review", analyze),
        ):
            results = await agent.analyze_reviews(
                review_ids=[1, 2, 3, 4, 5],
                brand="Example",
                progress_callback=progress.append,
            )

        fetch.assert_called_once_with([1, 2, 3, 4, 5], "Example")
        self.assertEqual(2, max_active)
        self.assertEqual([1, 2, 3, 4, 5], [result["review_id"] for result in results])
        self.assertEqual(5, progress[-1]["current"])


class WebSearchConcurrencyTests(unittest.IsolatedAsyncioTestCase):
    async def test_searches_run_with_bounded_concurrency(self):
        active = 0
        max_active = 0
        lock = threading.Lock()

        class FakeDDGS:
            def text(self, query, max_results, backend):
                nonlocal active, max_active
                with lock:
                    active += 1
                    max_active = max(max_active, active)
                time.sleep(0.03)
                with lock:
                    active -= 1
                return [{"href": f"https://example.com/{query}", "title": query, "body": query}]

        agent = WebSearchAgent.__new__(WebSearchAgent)
        intents = [
            {"query": f"query-{index}", "intent": "test", "priority": index}
            for index in range(1, 5)
        ]
        with (
            patch.object(web_search_agent, "DDGS", FakeDDGS),
            patch.object(web_search_agent, "SEARCH_CONCURRENCY", 2),
        ):
            results = await agent._execute_searches(intents)

        self.assertEqual(4, len(results))
        self.assertEqual(2, max_active)


class OrchestratorScopeTests(unittest.IsolatedAsyncioTestCase):
    async def test_new_review_ids_and_brand_flow_to_downstream_agents(self):
        events = []
        orchestrator = SentimentOrchestrator.__new__(SentimentOrchestrator)
        orchestrator.progress_callback = events.append
        orchestrator.web_agent = SimpleNamespace(
            search=AsyncMock(
                return_value=[
                    {
                        "url": "https://example.com/review",
                        "title": "Review",
                        "snippet": "A sufficiently long review snippet.",
                        "domain": "example.com",
                    }
                ]
            )
        )
        orchestrator.sentiment_agent = SimpleNamespace(
            analyze_reviews=AsyncMock(
                return_value=[
                    {"review_id": 101, "sentiment": "Positive", "score": 0.8}
                ]
            )
        )
        empty_dashboard = {
            "sentiment_distribution": {
                "positive_pct": 100.0,
                "neutral_pct": 0.0,
                "negative_pct": 0.0,
                "total": 1,
            },
            "avg_score": 0.8,
            "top_aspects": [],
            "emotion_distribution": [],
            "source_breakdown": [],
        }
        orchestrator.analytics_agent = SimpleNamespace(
            get_dashboard_stats=AsyncMock(return_value=empty_dashboard)
        )
        orchestrator.action_agent = SimpleNamespace(
            generate_actions=AsyncMock(return_value=[])
        )
        orchestrator._ingest_reviews = AsyncMock(return_value=[101])
        orchestrator._enrich_and_persist_alerts = AsyncMock()
        orchestrator._persist_actions = AsyncMock()

        result = await orchestrator.run_analysis("quality", "Example", True)

        sentiment_call = orchestrator.sentiment_agent.analyze_reviews.await_args.kwargs
        self.assertEqual([101], sentiment_call["review_ids"])
        self.assertEqual("Example", sentiment_call["brand"])
        orchestrator.analytics_agent.get_dashboard_stats.assert_awaited_once_with(
            brand="Example"
        )
        self.assertEqual(1, result["reviews_analyzed"])
        self.assertIn("sentiment_analysis", result["stage_timings"])
        self.assertEqual("complete", events[-1]["type"])


if __name__ == "__main__":
    unittest.main()
