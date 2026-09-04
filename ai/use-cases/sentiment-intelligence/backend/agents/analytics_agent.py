"""
Analytics Agent for Sentiment Intelligence.
Uses Select AI for NL2SQL and direct SQL for dashboard statistics.

Table schema reference:
  SCRAPED_REVIEWS:  id, source, url, author, review_text, scraped_at, brand, product, region, rating
  SENTIMENT_RESULTS: id, review_id (FK→scraped_reviews.id), sentiment, score, aspects_json, explanation, emotions, analyzed_at
  SENTIMENT_TRENDS:  id, week_label, week_start, positive_pct, neutral_pct, negative_pct, total_reviews, avg_score
  SENTIMENT_ALERTS:  id, alert_type, title, description, severity, source_count, sources, detected_at, brand
  ACTION_RECOMMENDATIONS: id, alert_id, action_text, priority, impact, category, status, created_at, brand
"""

import asyncio
import json
import logging
from typing import Optional

import oracledb

from database import get_db_connection, get_select_ai_profile

logger = logging.getLogger(__name__)


class AnalyticsAgent:
    """Runs analytics queries on sentiment data."""

    def __init__(self, select_ai_profile=None):
        self.profile = select_ai_profile
        self._uses_default_profile = select_ai_profile is None

    def _ensure_profile(self):
        # get_select_ai_profile also ensures that select_ai has a healthy
        # process/thread-local connection for the current request.
        if self._uses_default_profile:
            self.profile = get_select_ai_profile()

    async def query(self, question: str) -> dict:
        """Run a natural language query using Select AI NL2SQL."""
        self._ensure_profile()
        result = {"sql": None, "data": [], "narrative": None, "error": None}

        try:
            sql_result = self.profile.run_sql(prompt=question)
            if sql_result is not None:
                if hasattr(sql_result, "sql"):
                    result["sql"] = sql_result.sql
                if hasattr(sql_result, "rows"):
                    result["data"] = [list(row) for row in sql_result.rows]
                elif hasattr(sql_result, "to_json") and hasattr(sql_result, "columns"):
                    # select_ai 1.2.x returns a pandas DataFrame. Serializing via
                    # pandas converts NumPy scalars, timestamps, and NaN values into
                    # JSON-safe values for FastAPI.
                    result["data"] = json.loads(
                        sql_result.to_json(orient="records", date_format="iso")
                    )
                elif hasattr(sql_result, "data"):
                    result["data"] = sql_result.data
                elif isinstance(sql_result, list):
                    result["data"] = sql_result
            logger.info("NL2SQL returned %d rows.", len(result["data"]))
        except Exception as exc:
            logger.error("NL2SQL failed: %s", exc, exc_info=True)
            result["error"] = str(exc)

        try:
            narrative = self.profile.narrate(prompt=question)
            if narrative:
                result["narrative"] = str(narrative)
        except Exception as exc:
            logger.warning("Narrate failed: %s", exc)

        return result

    async def get_dashboard_stats(self, brand: Optional[str] = None) -> dict:
        """Compute current sentiment dashboard statistics via direct SQL.

        Args:
            brand: If provided, filter results to this brand only.
        """
        return await asyncio.to_thread(self._get_dashboard_stats_sync, brand)

    def _get_dashboard_stats_sync(self, brand: Optional[str] = None) -> dict:
        """Synchronous dashboard query implementation run in a worker thread."""
        conn: Optional[oracledb.Connection] = None
        stats = {
            "sentiment_distribution": {"positive_pct": 0.0, "neutral_pct": 0.0, "negative_pct": 0.0, "total": 0},
            "avg_score": 0.0,
            "source_breakdown": [],
            "top_aspects": [],
            "trends": [],
            "alerts": [],
            "actions": [],
            "recent_reviews": [],
            "emotion_distribution": [],
        }

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # ---- Brand filter helpers ----
            brand_bind = {"brand": brand} if brand else {}

            # ---- Sentiment Distribution ----
            sd_join = "JOIN scraped_reviews r ON s.review_id = r.id" if brand else ""
            sd_where = "WHERE r.brand = :brand" if brand else ""
            cursor.execute(f"""
                SELECT
                    COUNT(*) AS total,
                    ROUND(NVL(SUM(CASE WHEN s.sentiment='Positive' THEN 1 ELSE 0 END)/NULLIF(COUNT(*),0)*100,0),1),
                    ROUND(NVL(SUM(CASE WHEN s.sentiment='Neutral'  THEN 1 ELSE 0 END)/NULLIF(COUNT(*),0)*100,0),1),
                    ROUND(NVL(SUM(CASE WHEN s.sentiment='Negative' THEN 1 ELSE 0 END)/NULLIF(COUNT(*),0)*100,0),1),
                    ROUND(NVL(AVG(s.score),0),3)
                FROM sentiment_results s
                {sd_join}
                {sd_where}
            """, brand_bind)
            row = cursor.fetchone()
            if row:
                stats["sentiment_distribution"] = {
                    "positive_pct": float(row[1] or 0),
                    "neutral_pct": float(row[2] or 0),
                    "negative_pct": float(row[3] or 0),
                    "total": int(row[0] or 0),
                }
                stats["avg_score"] = float(row[4] or 0)

            # ---- Source Breakdown ----
            sb_where = "WHERE r.brand = :brand" if brand else ""
            cursor.execute(f"""
                SELECT r.source, COUNT(*) AS cnt, ROUND(AVG(s.score),3) AS avg_score
                FROM sentiment_results s
                JOIN scraped_reviews r ON s.review_id = r.id
                {sb_where}
                GROUP BY r.source
                ORDER BY cnt DESC
                FETCH FIRST 10 ROWS ONLY
            """, brand_bind)
            stats["source_breakdown"] = [
                {"source": row[0] or "Unknown", "count": int(row[1]), "avg_score": float(row[2] or 0)}
                for row in cursor.fetchall()
            ]

            # ---- Top Aspects (parsed from JSON) ----
            ta_join = "JOIN scraped_reviews r ON s.review_id = r.id" if brand else ""
            ta_where = "WHERE s.aspects_json IS NOT NULL AND r.brand = :brand" if brand else "WHERE s.aspects_json IS NOT NULL"
            cursor.execute(f"""
                SELECT s.aspects_json
                FROM sentiment_results s
                {ta_join}
                {ta_where}
                ORDER BY s.analyzed_at DESC
                FETCH FIRST 200 ROWS ONLY
            """, brand_bind)
            aspect_agg = {}
            for (raw,) in cursor.fetchall():
                if hasattr(raw, "read"):
                    raw = raw.read()
                try:
                    for asp in json.loads(str(raw)):
                        name = asp.get("aspect", "").lower().strip()
                        if not name:
                            continue
                        if name not in aspect_agg:
                            aspect_agg[name] = {"count": 0, "total_score": 0.0, "sentiments": []}
                        aspect_agg[name]["count"] += 1
                        aspect_agg[name]["total_score"] += float(asp.get("score", 0))
                        aspect_agg[name]["sentiments"].append(asp.get("sentiment", "Neutral"))
                except (json.JSONDecodeError, TypeError):
                    continue

            top_aspects = sorted(aspect_agg.items(), key=lambda x: x[1]["count"], reverse=True)[:15]
            stats["top_aspects"] = [
                {
                    "aspect": name.title(),
                    "count": info["count"],
                    "avg_score": round(info["total_score"] / max(info["count"], 1), 3),
                    "sentiment": max(set(info["sentiments"]), key=info["sentiments"].count) if info["sentiments"] else "Neutral",
                }
                for name, info in top_aspects
            ]

            # ---- Trends (from pre-computed table) ----
            cursor.execute("""
                SELECT week_label, positive_pct, neutral_pct, negative_pct, total_reviews, avg_score
                FROM sentiment_trends
                ORDER BY week_start
            """)
            stats["trends"] = [
                {"week_label": r[0], "positive_pct": float(r[1] or 0), "neutral_pct": float(r[2] or 0), "negative_pct": float(r[3] or 0), "total_reviews": int(r[4] or 0), "avg_score": float(r[5] or 0)}
                for r in cursor.fetchall()
            ]

            # ---- Alerts ----
            al_where = "WHERE (brand = :brand OR brand IS NULL)" if brand else ""
            cursor.execute(f"""
                SELECT id, alert_type, title, description, severity, source_count, sources,
                       source_urls, detected_at, brand
                FROM sentiment_alerts
                {al_where}
                ORDER BY detected_at DESC
            """, brand_bind)
            stats["alerts"] = []
            for r in cursor.fetchall():
                descr = r[3].read() if hasattr(r[3], "read") else r[3]
                source_urls_raw = r[7]
                if source_urls_raw and hasattr(source_urls_raw, "read"):
                    source_urls_raw = source_urls_raw.read()
                try:
                    sources_data = json.loads(str(source_urls_raw)) if source_urls_raw else []
                except (json.JSONDecodeError, TypeError):
                    sources_data = []
                stats["alerts"].append({
                    "id": r[0],
                    "alert_type": r[1],
                    "title": r[2],
                    "description": descr,
                    "severity": r[4],
                    "source_count": r[5],
                    "sources": r[6],
                    "sources_data": sources_data,
                    "detected_at": r[8].isoformat() if r[8] else None,
                    "brand": r[9],
                })

            # ---- Actions ----
            ac_where = "WHERE (brand = :brand OR brand IS NULL)" if brand else ""
            cursor.execute(f"""
                SELECT id, alert_id, action_text, priority, impact, category, status, created_at, brand
                FROM action_recommendations
                {ac_where}
                ORDER BY
                    CASE priority WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END,
                    created_at DESC
            """, brand_bind)
            stats["actions"] = [
                {"id": r[0], "alert_id": r[1], "action_text": r[2], "priority": r[3], "impact": r[4], "category": r[5], "status": r[6], "created_at": r[7].isoformat() if r[7] else None, "brand": r[8]}
                for r in cursor.fetchall()
            ]

            # ---- Recent Reviews with Sentiment ----
            rr_where = "WHERE r.brand = :brand" if brand else ""
            cursor.execute(f"""
                SELECT r.id, r.source, r.author, r.review_text, r.product, r.rating,
                       s.sentiment, s.score
                FROM scraped_reviews r
                LEFT JOIN sentiment_results s ON s.review_id = r.id
                {rr_where}
                ORDER BY r.scraped_at DESC
                FETCH FIRST 20 ROWS ONLY
            """, brand_bind)
            stats["recent_reviews"] = []
            for r in cursor.fetchall():
                text = r[3]
                if hasattr(text, "read"):
                    text = text.read()
                stats["recent_reviews"].append({
                    "id": r[0], "source": r[1], "author": r[2],
                    "review_text": str(text)[:300], "product": r[4], "rating": float(r[5]) if r[5] else None,
                    "sentiment": r[6], "score": float(r[7]) if r[7] is not None else None,
                })

            # ---- Emotion Distribution ----
            em_join = "JOIN scraped_reviews r ON s.review_id = r.id" if brand else ""
            em_where = "WHERE s.emotions IS NOT NULL AND r.brand = :brand" if brand else "WHERE s.emotions IS NOT NULL"
            cursor.execute(f"""
                SELECT s.emotions
                FROM sentiment_results s
                {em_join}
                {em_where}
                ORDER BY s.analyzed_at DESC
                FETCH FIRST 200 ROWS ONLY
            """, brand_bind)
            emotion_counts = {}
            for (raw,) in cursor.fetchall():
                if hasattr(raw, "read"):
                    raw = raw.read()
                try:
                    for em in json.loads(str(raw)):
                        em_str = str(em).lower().strip()
                        if em_str:
                            emotion_counts[em_str] = emotion_counts.get(em_str, 0) + 1
                except (json.JSONDecodeError, TypeError):
                    continue

            stats["emotion_distribution"] = sorted(
                [{"emotion": em.title(), "count": cnt} for em, cnt in emotion_counts.items()],
                key=lambda x: x["count"], reverse=True,
            )[:12]

            logger.info("Dashboard stats: %d total results, avg_score=%.3f", stats["sentiment_distribution"]["total"], stats["avg_score"])

        except Exception as exc:
            logger.error("Dashboard stats failed: %s", exc, exc_info=True)
            raise
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

        return stats
