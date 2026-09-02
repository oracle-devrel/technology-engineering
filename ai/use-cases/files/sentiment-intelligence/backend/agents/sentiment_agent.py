"""
Sentiment Agent - analyzes customer reviews using DBMS_CLOUD_AI.GENERATE
inside Oracle Autonomous Database.

Actual table schema
-------------------
SCRAPED_REVIEWS: id, source, url, author, review_text, scraped_at, brand,
                 product, region, rating
SENTIMENT_RESULTS: id, review_id (FK), sentiment, score, aspects_json,
                   explanation, emotions, analyzed_at
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Callable, Optional

import oracledb

from config import settings
from database import get_db_connection

logger = logging.getLogger(__name__)

SENTIMENT_PROMPT_TEMPLATE = """Analyze the sentiment of this customer review. Return your analysis as a JSON object with these exact fields:

- "sentiment": one of "Positive", "Negative", or "Neutral"
- "score": a float from -1.0 (most negative) to 1.0 (most positive)
- "aspects": an array of objects, each with "aspect" (string), "sentiment" (string), and "score" (float)
- "explanation": a 1-2 sentence explanation of the overall sentiment
- "emotions": an array of emotion strings detected (e.g. "frustration", "satisfaction", "anger", "joy")

Review text:
\"\"\"
{review_text}
\"\"\"

Return ONLY the JSON object, no markdown fences or extra text."""


class SentimentAgent:
    """Analyze review sentiment through a database Select AI profile."""

    def __init__(self):
        self.profile_name = settings.SELECT_AI_PROFILE
        logger.info("SentimentAgent initialized (profile=%s)", self.profile_name)

    async def analyze_reviews(
        self,
        review_ids: Optional[list[int]] = None,
        brand: Optional[str] = None,
        progress_callback: Optional[Callable] = None,
    ) -> list[dict]:
        """Analyze reviews with bounded concurrent database inference.

        If ``review_ids`` is supplied, only those rows are considered. Otherwise
        the pending set is restricted to ``brand`` when provided, preventing one
        brand's run from consuming another brand's backlog.
        """
        rows = await asyncio.to_thread(self._fetch_reviews, review_ids, brand)
        total = len(rows)
        concurrency = max(1, settings.SENTIMENT_CONCURRENCY)
        logger.info(
            "Found %d reviews to analyze (brand=%r, workers=%d).",
            total,
            brand,
            concurrency,
        )

        if total == 0:
            self._notify_progress(
                progress_callback,
                {
                    "type": "sentiment_progress",
                    "current": 0,
                    "total": 0,
                    "message": "No new reviews to analyze.",
                },
            )
            return []

        semaphore = asyncio.Semaphore(concurrency)
        completed = 0
        self._notify_progress(
            progress_callback,
            {
                "type": "sentiment_progress",
                "current": 0,
                "total": total,
                "message": (
                    f"Analyzing {total} reviews with "
                    f"{min(concurrency, total)} workers..."
                ),
            },
        )

        async def analyze_one(row: tuple) -> dict:
            nonlocal completed
            async with semaphore:
                result = await asyncio.to_thread(
                    self._analyze_and_persist_review,
                    row,
                )
            completed += 1
            label = result.pop("_label", "review")
            self._notify_progress(
                progress_callback,
                {
                    "type": "sentiment_progress",
                    "current": completed,
                    "total": total,
                    "message": f"Analyzed {completed}/{total}: {label[:60]}",
                },
            )
            return result

        results = await asyncio.gather(*(analyze_one(row) for row in rows))
        succeeded = sum(not result.get("error") for result in results)
        logger.info("Sentiment analysis complete. %d/%d succeeded.", succeeded, total)
        return results

    async def analyze_single_review(self, review_text: str) -> dict:
        """Analyze one review without persisting it."""
        return await asyncio.to_thread(self._analyze_text, review_text)

    def _fetch_reviews(
        self,
        review_ids: Optional[list[int]],
        brand: Optional[str],
    ) -> list[tuple]:
        """Fetch review rows and materialize LOBs before closing the connection."""
        if review_ids is not None and not review_ids:
            return []

        conn: Optional[oracledb.Connection] = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            if review_ids is not None:
                unique_ids = list(
                    dict.fromkeys(int(review_id) for review_id in review_ids)
                )
                placeholders = ",".join(
                    f":id{index}" for index in range(len(unique_ids))
                )
                bind_vars = {
                    f"id{index}": review_id
                    for index, review_id in enumerate(unique_ids)
                }
                cursor.execute(
                    f"""
                    SELECT r.id, r.review_text, r.source, r.author, r.product
                    FROM scraped_reviews r
                    WHERE r.id IN ({placeholders})
                      AND NOT EXISTS (
                          SELECT 1
                          FROM sentiment_results s
                          WHERE s.review_id = r.id
                      )
                    ORDER BY r.id
                    """,
                    bind_vars,
                )
            else:
                brand_clause = "AND r.brand = :brand" if brand else ""
                bind_vars = {"brand": brand} if brand else {}
                cursor.execute(
                    f"""
                    SELECT r.id, r.review_text, r.source, r.author, r.product
                    FROM scraped_reviews r
                    WHERE NOT EXISTS (
                        SELECT 1
                        FROM sentiment_results s
                        WHERE s.review_id = r.id
                    )
                    {brand_clause}
                    ORDER BY r.scraped_at DESC
                    FETCH FIRST 50 ROWS ONLY
                    """,
                    bind_vars,
                )

            materialized = []
            for review_id, review_text_lob, source, author, product in cursor.fetchall():
                review_text = (
                    review_text_lob.read()
                    if hasattr(review_text_lob, "read")
                    else str(review_text_lob or "")
                )
                materialized.append(
                    (review_id, review_text, source, author, product)
                )
            return materialized
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _analyze_and_persist_review(self, row: tuple) -> dict:
        """Run one inference and insert its result on a worker-owned connection."""
        review_id, review_text, source, author, product = row
        label = (
            f"{author or source or ''} - {product or ''}".strip(" -")
            or f"review {review_id}"
        )
        conn: Optional[oracledb.Connection] = None
        try:
            conn = get_db_connection()
            conn.call_timeout = max(1, settings.SENTIMENT_AGENT_TIMEOUT) * 1000
            cursor = conn.cursor()
            sentiment_data = self._call_dbms_cloud_ai(cursor, review_text)
            sentiment_data["review_id"] = review_id
            self._insert_result(cursor, review_id, sentiment_data)
            conn.commit()
            sentiment_data["_label"] = label
            logger.info(
                "Review %d: %s (score=%.2f)",
                review_id,
                sentiment_data["sentiment"],
                sentiment_data["score"],
            )
            return sentiment_data
        except Exception as exc:
            if conn:
                conn.rollback()
            logger.error(
                "Failed to analyze review %d: %s",
                review_id,
                exc,
                exc_info=True,
            )
            return {
                "review_id": review_id,
                "sentiment": "Error",
                "score": 0.0,
                "aspects": [],
                "explanation": f"Analysis failed: {exc}",
                "emotions": [],
                "error": True,
                "_label": label,
            }
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _analyze_text(self, review_text: str) -> dict:
        """Run one non-persisted inference using a worker-owned connection."""
        conn: Optional[oracledb.Connection] = None
        try:
            conn = get_db_connection()
            conn.call_timeout = max(1, settings.SENTIMENT_AGENT_TIMEOUT) * 1000
            return self._call_dbms_cloud_ai(conn.cursor(), review_text)
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    @staticmethod
    def _notify_progress(
        progress_callback: Optional[Callable],
        event: dict,
    ) -> None:
        if not progress_callback:
            return
        try:
            progress_callback(event)
        except Exception as exc:
            logger.warning("Sentiment progress callback failed: %s", exc)

    def _call_dbms_cloud_ai(self, cursor, review_text: str) -> dict:
        """Call DBMS_CLOUD_AI.GENERATE through a bound SQL statement."""
        text = review_text
        if len(text) > 4000:
            text = text[:4000] + "... [truncated]"

        prompt = SENTIMENT_PROMPT_TEMPLATE.format(review_text=text)
        cursor.execute(
            """
            SELECT DBMS_CLOUD_AI.GENERATE(
                prompt       => :prompt,
                profile_name => :profile_name,
                action       => 'chat'
            ) AS result
            FROM dual
            """,
            {"prompt": prompt, "profile_name": self.profile_name},
        )
        row = cursor.fetchone()
        if not row or not row[0]:
            raise RuntimeError("DBMS_CLOUD_AI.GENERATE returned no result.")

        raw = row[0]
        if hasattr(raw, "read"):
            raw = raw.read()

        logger.debug("DBMS_CLOUD_AI response (500 chars): %s", str(raw)[:500])
        return self._parse_response(raw)

    def _parse_response(self, raw: str) -> dict:
        """Parse and normalize the JSON sentiment response."""
        text = str(raw).strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(
                line for line in lines if not line.strip().startswith("```")
            ).strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            start, end = text.find("{"), text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    data = json.loads(text[start:end])
                except json.JSONDecodeError:
                    data = {}
            else:
                data = {}

        sentiment = data.get("sentiment", "Neutral")
        if sentiment not in ("Positive", "Negative", "Neutral"):
            sentiment = "Neutral"

        try:
            score = max(-1.0, min(1.0, float(data.get("score", 0.0))))
        except (TypeError, ValueError):
            score = 0.0

        aspects = []
        for aspect in data.get("aspects") or []:
            if not isinstance(aspect, dict) or "aspect" not in aspect:
                continue
            try:
                aspect_score = max(
                    -1.0,
                    min(1.0, float(aspect.get("score", 0.0))),
                )
            except (TypeError, ValueError):
                aspect_score = 0.0
            aspect_sentiment = str(aspect.get("sentiment", "Neutral"))
            if aspect_sentiment not in ("Positive", "Negative", "Neutral"):
                aspect_sentiment = "Neutral"
            aspects.append(
                {
                    "aspect": str(aspect["aspect"]),
                    "sentiment": aspect_sentiment,
                    "score": aspect_score,
                }
            )

        emotions = [str(emotion) for emotion in data.get("emotions") or [] if emotion]
        return {
            "sentiment": sentiment,
            "score": score,
            "aspects": aspects,
            "explanation": str(
                data.get("explanation", "No explanation provided.")
            ),
            "emotions": emotions,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        }

    def _insert_result(self, cursor, review_id: int, data: dict) -> None:
        """Insert a sentiment result into SENTIMENT_RESULTS."""
        cursor.execute(
            """
            INSERT INTO sentiment_results (
                review_id, sentiment, score, aspects_json,
                explanation, emotions, analyzed_at
            )
            VALUES (
                :review_id, :sentiment, :score, :aspects_json,
                :explanation, :emotions, SYSTIMESTAMP
            )
            """,
            {
                "review_id": review_id,
                "sentiment": data["sentiment"],
                "score": data["score"],
                "aspects_json": json.dumps(data["aspects"]),
                "explanation": data["explanation"],
                "emotions": json.dumps(data["emotions"]),
            },
        )
