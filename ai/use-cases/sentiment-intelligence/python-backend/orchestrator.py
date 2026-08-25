"""
Orchestrator for Sentiment Intelligence.
Coordinates the 6-step agentic workflow:
  1. Web Scout   — search & scrape customer reviews from the web
  2. Ingestion   — store scraped content in Oracle DB (scraped_reviews)
  3. Sentiment   — analyze reviews IN-DATABASE via DBMS_CLOUD_AI.GENERATE
  4. Analytics   — compute trends & dashboard statistics
  5. Actions     — generate marketing action recommendations
  6. Complete    — compile and return final results
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Callable, Optional

import oracledb

from config import settings
from database import get_db_connection
from web_search_agent import WebSearchAgent
from sentiment_agent import SentimentAgent
from analytics_agent import AnalyticsAgent
from action_agent import ActionAgent

logger = logging.getLogger(__name__)


class SentimentOrchestrator:
    """Runs the full 6-step sentiment analysis pipeline with SSE progress streaming."""

    TOTAL_STEPS = 6

    def __init__(self, progress_callback: Optional[Callable] = None):
        self.progress_callback = progress_callback
        self.web_agent = WebSearchAgent()
        self.sentiment_agent = SentimentAgent()
        self.analytics_agent = AnalyticsAgent()
        self.action_agent = ActionAgent()

    async def run_analysis(self, topic: str, brand: str, use_web_search: bool = True) -> dict:
        started_at = datetime.now(timezone.utc)
        web_results = []
        ingested_ids: list[int] = []
        ingested_count = 0
        sentiment_results = []
        dashboard = {}
        alerts = []
        actions = []
        stage_timings: dict[str, float] = {}

        try:
            # ── STEP 1: Web Scout ─────────────────────────────────────
            step_started = time.perf_counter()
            await self._emit({"type": "step_start", "step": "web_scout", "stepNumber": 1, "totalSteps": self.TOTAL_STEPS, "message": "Searching web for customer reviews and discussions..."})
            if use_web_search:
                try:
                    web_results = await self.web_agent.search(
                        query=f"{brand} {topic} customer reviews",
                        hypothesis=f"Customer sentiment about {brand} {topic}",
                        scrape_content=True,
                    )
                except Exception as exc:
                    logger.error("Web search failed: %s", exc)
                    await self._emit({"type": "step_warning", "step": "web_scout", "message": f"Web search error: {exc}. Continuing with existing data."})
            stage_timings["web_scout"] = round(time.perf_counter() - step_started, 2)
            await self._emit({"type": "step_complete", "step": "web_scout", "stepNumber": 1, "totalSteps": self.TOTAL_STEPS, "message": f"Found {len(web_results)} web sources.", "duration": stage_timings["web_scout"], "data": {"source_count": len(web_results)}})

            # ── STEP 2: Ingestion ─────────────────────────────────────
            step_started = time.perf_counter()
            await self._emit({"type": "step_start", "step": "ingestion", "stepNumber": 2, "totalSteps": self.TOTAL_STEPS, "message": "Ingesting scraped reviews into Oracle Database..."})
            if web_results:
                try:
                    ingested_ids = await self._ingest_reviews(web_results, brand, topic)
                    ingested_count = len(ingested_ids)
                except Exception as exc:
                    logger.error("Ingestion failed: %s", exc)
                    await self._emit({"type": "step_warning", "step": "ingestion", "message": f"Ingestion error: {exc}"})
            stage_timings["ingestion"] = round(time.perf_counter() - step_started, 2)
            await self._emit({"type": "step_complete", "step": "ingestion", "stepNumber": 2, "totalSteps": self.TOTAL_STEPS, "message": f"Ingested {ingested_count} new reviews.", "duration": stage_timings["ingestion"], "data": {"ingested_count": ingested_count}})

            # ── STEP 3: Sentiment Analysis (IN-DATABASE!) ─────────────
            step_started = time.perf_counter()
            await self._emit({"type": "step_start", "step": "sentiment_analysis", "stepNumber": 3, "totalSteps": self.TOTAL_STEPS, "message": "Running in-database sentiment analysis via OCI GenAI..."})
            try:
                sentiment_results = await self.sentiment_agent.analyze_reviews(
                    review_ids=ingested_ids or None,
                    brand=brand,
                    progress_callback=self.progress_callback,
                )
            except Exception as exc:
                logger.error("Sentiment analysis failed: %s", exc)
                await self._emit({"type": "step_warning", "step": "sentiment_analysis", "message": f"Sentiment error: {exc}"})
            analyzed_count = sum(not result.get("error") for result in sentiment_results)
            failed_count = len(sentiment_results) - analyzed_count
            stage_timings["sentiment_analysis"] = round(time.perf_counter() - step_started, 2)
            sentiment_message = f"Analyzed {analyzed_count} reviews."
            if failed_count:
                sentiment_message += f" {failed_count} failed."
            await self._emit({"type": "step_complete", "step": "sentiment_analysis", "stepNumber": 3, "totalSteps": self.TOTAL_STEPS, "message": sentiment_message, "duration": stage_timings["sentiment_analysis"], "data": {"analyzed_count": analyzed_count, "failed_count": failed_count}})

            # ── STEP 4: Analytics ─────────────────────────────────────
            step_started = time.perf_counter()
            await self._emit({"type": "step_start", "step": "analytics", "stepNumber": 4, "totalSteps": self.TOTAL_STEPS, "message": "Computing sentiment trends and dashboard statistics..."})
            try:
                dashboard = await self.analytics_agent.get_dashboard_stats(brand=brand)
                alerts = self._detect_alerts(dashboard, sentiment_results)
            except Exception as exc:
                logger.error("Analytics failed: %s", exc)
                await self._emit({"type": "step_warning", "step": "analytics", "message": f"Analytics error: {exc}"})
            stage_timings["analytics"] = round(time.perf_counter() - step_started, 2)
            await self._emit({"type": "step_complete", "step": "analytics", "stepNumber": 4, "totalSteps": self.TOTAL_STEPS, "message": f"Dashboard updated. {len(alerts)} alert(s).", "duration": stage_timings["analytics"], "data": {"alert_count": len(alerts)}})

            # ── STEP 5: Action Recommendations ────────────────────────
            step_started = time.perf_counter()
            await self._emit({"type": "step_start", "step": "actions", "stepNumber": 5, "totalSteps": self.TOTAL_STEPS, "message": "Generating marketing action recommendations..."})

            # Alert enrichment/persistence and recommendation generation are
            # independent after analytics, so run them concurrently.
            alert_task = None
            if alerts:
                alert_task = asyncio.create_task(
                    self._enrich_and_persist_alerts(alerts, brand)
                )

            try:
                web_context = self._build_web_context(web_results)
                action_alerts = [
                    {
                        key: value
                        for key, value in alert.items()
                        if key not in {"aspect_names", "sources_data"}
                    }
                    for alert in alerts
                ]
                actions = await self.action_agent.generate_actions(
                    sentiment_summary=dashboard,
                    alerts=action_alerts,
                    web_context=web_context,
                )
            except Exception as exc:
                logger.error("Action generation failed: %s", exc)
                await self._emit({"type": "step_warning", "step": "actions", "message": f"Action error: {exc}"})

            # Persist actions to DB
            if actions:
                try:
                    await self._persist_actions(actions, brand)
                except Exception as exc:
                    logger.error("Failed to persist actions: %s", exc)

            if alert_task:
                try:
                    await alert_task
                except Exception as exc:
                    logger.error("Failed to enrich or persist alerts: %s", exc)

            stage_timings["actions"] = round(time.perf_counter() - step_started, 2)
            await self._emit({"type": "step_complete", "step": "actions", "stepNumber": 5, "totalSteps": self.TOTAL_STEPS, "message": f"Generated {len(actions)} actions.", "duration": stage_timings["actions"], "data": {"action_count": len(actions)}})

            # ── STEP 6: Complete ──────────────────────────────────────
            elapsed = (datetime.now(timezone.utc) - started_at).total_seconds()
            final_result = {
                "topic": topic,
                "brand": brand,
                "elapsed_seconds": round(elapsed, 1),
                "web_sources": len(web_results),
                "reviews_ingested": ingested_count,
                "reviews_analyzed": analyzed_count,
                "reviews_failed": failed_count,
                "stage_timings": stage_timings,
                "dashboard": dashboard,
                "alerts": alerts,
                "actions": actions,
                "sentiment_results": sentiment_results[:20],
            }
            await self._emit({"type": "complete", "step": "complete", "stepNumber": 6, "totalSteps": self.TOTAL_STEPS, "message": f"Analysis complete in {elapsed:.1f}s.", "result": final_result})
            return final_result

        except Exception as exc:
            logger.error("Pipeline failed: %s", exc, exc_info=True)
            await self._emit({"type": "error", "message": f"Pipeline failed: {exc}", "error": str(exc)})
            raise

    # ------------------------------------------------------------------

    async def _ingest_reviews(
        self,
        web_results,
        brand: str,
        topic: str,
    ) -> list[int]:
        """Insert web results off the event loop and return new review IDs."""
        return await asyncio.to_thread(
            self._ingest_reviews_sync,
            web_results,
            brand,
            topic,
        )

    def _ingest_reviews_sync(
        self,
        web_results,
        brand: str,
        topic: str,
    ) -> list[int]:
        """Insert scraped web results, deduplicating by URL."""
        conn: Optional[oracledb.Connection] = None
        inserted_ids: list[int] = []
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            for result in web_results:
                if isinstance(result, dict):
                    url = result.get("url", "") or ""
                    title = result.get("title", "") or ""
                    snippet = result.get("snippet", "") or ""
                    domain = result.get("domain", "") or ""
                    scraped_text = (
                        result.get("scraped_text")
                        or result.get("full_content")
                        or ""
                    )
                else:
                    url = getattr(result, "url", "") or ""
                    title = getattr(result, "title", "") or ""
                    snippet = getattr(result, "snippet", "") or ""
                    domain = getattr(result, "domain", "") or ""
                    scraped_text = (
                        getattr(result, "scraped_text", "")
                        or getattr(result, "full_content", "")
                        or ""
                    )

                review_text = scraped_text or snippet
                if not review_text or len(review_text.strip()) < 20:
                    continue

                normalized_url = url[:1000]
                cursor.execute(
                    "SELECT id FROM scraped_reviews WHERE url = :url FETCH FIRST 1 ROW ONLY",
                    {"url": normalized_url},
                )
                if cursor.fetchone():
                    continue

                new_id = cursor.var(oracledb.NUMBER)
                cursor.execute(
                    """
                    INSERT INTO scraped_reviews (source, url, author, review_text, brand, product, region, scraped_at)
                    VALUES (:source, :url, :author, :review_text, :brand, :product, NULL, SYSTIMESTAMP)
                    RETURNING id INTO :new_id
                    """,
                    {
                        "source": (domain or "Web")[:100],
                        "url": normalized_url,
                        "author": (title or "")[:200],
                        "review_text": review_text[:4000],
                        "brand": brand[:200],
                        "product": topic[:200],
                        "new_id": new_id,
                    },
                )
                inserted_ids.append(int(new_id.getvalue()))

            conn.commit()
        except Exception:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
        return inserted_ids

    def _detect_alerts(self, dashboard: dict, sentiment_results: list) -> list[dict]:
        alerts = []
        dist = dashboard.get("sentiment_distribution", {})
        neg_pct = dist.get("negative_pct", 0)
        avg_score = dashboard.get("avg_score", 0)
        total = dist.get("total", 0)

        if neg_pct > 50:
            alerts.append({
                "type": "high_negative",
                "severity": "critical",
                "title": f"Critical negative sentiment ({neg_pct:.1f}%)",
                "description": (
                    f"{neg_pct:.1f}% of {total} analyzed reviews are negative — "
                    f"a critical level that warrants immediate response."
                ),
            })
        elif neg_pct > 30:
            alerts.append({
                "type": "high_negative",
                "severity": "warning",
                "title": f"Elevated negative sentiment ({neg_pct:.1f}%)",
                "description": (
                    f"{neg_pct:.1f}% of {total} analyzed reviews are negative, "
                    f"above the 30% warning threshold."
                ),
            })

        if avg_score < -0.3:
            alerts.append({
                "type": "low_score",
                "severity": "critical",
                "title": f"Average sentiment {avg_score:.2f} (well below neutral)",
                "description": (
                    f"Mean sentiment score across {total} reviews is {avg_score:.2f} "
                    f"on a -1.0 to +1.0 scale. Customers are persistently dissatisfied."
                ),
            })

        aspects = dashboard.get("top_aspects", [])
        neg_aspects = [a for a in aspects if a.get("sentiment") == "Negative" and a.get("count", 0) >= 3]
        if neg_aspects:
            top = neg_aspects[:3]
            names = [a["aspect"] for a in top]
            names_str = ", ".join(names)
            total_mentions = sum(a["count"] for a in top)
            alerts.append({
                "type": "negative_aspects",
                "severity": "warning",
                "title": f"Recurring complaints: {names_str}",
                "description": (
                    f"{total_mentions} negative mentions across {len(top)} themes "
                    f"({names_str}). Investigate root causes."
                ),
                "aspect_names": names,
            })

        return alerts

    async def _enrich_alerts_with_sources(self, alerts: list[dict], brand: str) -> None:
        """Attach contributing review URLs to each alert by querying SCRAPED_REVIEWS.

        For aspect-specific alerts, filters reviews whose aspects_json mentions
        the named aspect. Other alerts get the most-negative reviews for the brand.
        """
        await asyncio.to_thread(
            self._enrich_alerts_with_sources_sync,
            alerts,
            brand,
        )

    def _enrich_alerts_with_sources_sync(
        self,
        alerts: list[dict],
        brand: str,
    ) -> None:
        if not alerts:
            return

        conn: Optional[oracledb.Connection] = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT r.id, r.url, r.source, r.author, s.score, s.aspects_json
                FROM scraped_reviews r
                JOIN sentiment_results s ON s.review_id = r.id
                WHERE r.brand = :brand
                  AND s.sentiment = 'Negative'
                  AND r.url IS NOT NULL
                ORDER BY s.score ASC
                FETCH FIRST 30 ROWS ONLY
                """,
                {"brand": brand},
            )

            neg_reviews: list[dict] = []
            for row in cursor.fetchall():
                _rid, url, source, author, score, aspects_clob = row
                if not url:
                    continue
                aspects_text = aspects_clob.read() if hasattr(aspects_clob, "read") else aspects_clob
                try:
                    aspects = json.loads(str(aspects_text)) if aspects_text else []
                except (json.JSONDecodeError, TypeError):
                    aspects = []
                aspect_names_lower = [
                    str(a.get("aspect", "")).lower()
                    for a in aspects if isinstance(a, dict)
                ]
                neg_reviews.append({
                    "url": url,
                    "domain": source or "Web",
                    "title": (author or "")[:120] or url,
                    "score": float(score) if score is not None else None,
                    "_aspects_lower": aspect_names_lower,
                })

            for alert in alerts:
                aspect_names = [str(n).lower() for n in alert.get("aspect_names", [])]
                if aspect_names:
                    matching = [
                        r for r in neg_reviews
                        if any(an in ra or ra in an
                               for an in aspect_names
                               for ra in r["_aspects_lower"])
                    ]
                    relevant = matching if matching else neg_reviews
                else:
                    relevant = neg_reviews

                seen, sources_data = set(), []
                for r in relevant:
                    if r["url"] in seen:
                        continue
                    seen.add(r["url"])
                    sources_data.append({
                        "url": r["url"],
                        "domain": r["domain"],
                        "title": r["title"],
                        "score": r["score"],
                    })
                    if len(sources_data) >= 8:
                        break

                alert["sources_data"] = sources_data
                alert["source_count"] = len(sources_data)

                # Drop helper field before persistence
                alert.pop("aspect_names", None)

        except Exception as exc:
            logger.warning("Failed to enrich alerts with sources: %s", exc)
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    async def _enrich_and_persist_alerts(
        self,
        alerts: list[dict],
        brand: str,
    ) -> None:
        """Enrich alerts with sources, then persist them in dependency order."""
        await self._enrich_alerts_with_sources(alerts, brand)
        await self._persist_alerts(alerts, brand)

    def _build_web_context(self, web_results) -> str:
        if not web_results:
            return ""
        parts = []
        for r in web_results[:5]:
            title = getattr(r, "title", "") if not isinstance(r, dict) else r.get("title", "")
            domain = getattr(r, "domain", "") if not isinstance(r, dict) else r.get("domain", "")
            snippet = getattr(r, "snippet", "") if not isinstance(r, dict) else r.get("snippet", "")
            parts.append(f"- [{domain}] {title}: {snippet[:200]}")
        return "\n".join(parts)

    async def _persist_alerts(self, alerts: list[dict], brand: str) -> None:
        """Insert detected alerts into sentiment_alerts with brand and source URLs."""
        await asyncio.to_thread(self._persist_alerts_sync, alerts, brand)

    def _persist_alerts_sync(self, alerts: list[dict], brand: str) -> None:
        """Synchronous alert persistence implementation."""
        conn: Optional[oracledb.Connection] = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            for a in alerts:
                sources_data = a.get("sources_data", []) or []
                domain_summary = ", ".join(
                    sorted({str(s.get("domain", "")) for s in sources_data if s.get("domain")})
                )[:500]
                source_urls_json = json.dumps(sources_data) if sources_data else None

                cursor.execute(
                    """
                    INSERT INTO sentiment_alerts (
                        alert_type, title, description, severity,
                        source_count, sources, source_urls,
                        detected_at, brand
                    )
                    VALUES (
                        :atype, :title, :descr, :severity,
                        :src_count, :sources, :source_urls,
                        SYSTIMESTAMP, :brand
                    )
                    """,
                    {
                        "atype": a.get("type", "general")[:100],
                        "title": a.get("title", a.get("message", ""))[:200],
                        "descr": a.get("description", a.get("message", ""))[:4000],
                        "severity": a.get("severity", "medium")[:50],
                        "src_count": int(a.get("source_count", 0) or 0),
                        "sources": domain_summary,
                        "source_urls": source_urls_json,
                        "brand": brand[:200],
                    },
                )
            conn.commit()
            logger.info("Persisted %d alerts for brand '%s'.", len(alerts), brand)
        except Exception as exc:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    async def _persist_actions(self, actions: list[dict], brand: str) -> None:
        """Insert action recommendations into action_recommendations with brand."""
        await asyncio.to_thread(self._persist_actions_sync, actions, brand)

    def _persist_actions_sync(self, actions: list[dict], brand: str) -> None:
        """Synchronous action persistence implementation."""
        conn: Optional[oracledb.Connection] = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            for a in actions:
                cursor.execute(
                    """
                    INSERT INTO action_recommendations (action_text, priority, impact, category, status, created_at, brand)
                    VALUES (:action_text, :priority, :impact, :category, 'pending', SYSTIMESTAMP, :brand)
                    """,
                    {
                        "action_text": str(a.get("action_text", ""))[:4000],
                        "priority": str(a.get("priority", "medium"))[:50],
                        "impact": str(a.get("impact", ""))[:4000],
                        "category": str(a.get("category", "engagement"))[:100],
                        "brand": brand[:200],
                    },
                )
            conn.commit()
            logger.info("Persisted %d actions for brand '%s'.", len(actions), brand)
        except Exception as exc:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    async def _emit(self, event: dict) -> None:
        if self.progress_callback:
            try:
                self.progress_callback(event)
            except Exception as exc:
                logger.warning("Progress callback failed: %s", exc)
