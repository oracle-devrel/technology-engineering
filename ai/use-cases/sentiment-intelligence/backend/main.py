"""
FastAPI application for Sentiment Intelligence.
Provides REST + SSE endpoints for the sentiment analysis dashboard.
"""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

import oracledb
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from config import settings
from database import connect_to_database, close_connection, is_connected, get_db_connection
from orchestrator import SentimentOrchestrator
from agents.analytics_agent import AnalyticsAgent
from agents.action_agent import ActionAgent
from agents.sentiment_agent import SentimentAgent
from agents.campaign_agent import CampaignAgent

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic request / response models
# ---------------------------------------------------------------------------
class AnalyzeRequest(BaseModel):
    topic: str = Field(..., description="Subject to analyze, e.g. 'product quality'")
    brand: str = Field(..., description="Brand name to analyze")
    use_web_search: bool = Field(default=True, description="Whether to search the web for reviews")


class QueryRequest(BaseModel):
    question: str = Field(..., description="Natural language question about sentiment data")


class ReviewAnalyzeRequest(BaseModel):
    review_text: str = Field(..., description="Single review text to analyze")


class RAGQueryRequest(BaseModel):
    question: str = Field(..., description="Natural language question for RAG knowledge base")


class CampaignRequest(BaseModel):
    brand: str = Field(..., description="Brand name to generate campaign for")
    campaign_objective: str = Field(default="customer_reactivation", description="Campaign objective key")
    tone: str = Field(default="warm_personal", description="Communication tone key")


class HealthResponse(BaseModel):
    status: str
    app_name: str
    app_version: str
    database_connected: bool
    timestamp: str


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: connect to DB on startup, close on shutdown."""
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
    try:
        await connect_to_database()
        logger.info("Database connection established on startup.")
    except Exception as exc:
        logger.error("Failed to connect to database on startup: %s", exc)
        # Allow the app to start even if DB is down -- endpoints will fail gracefully
    yield
    logger.info("Shutting down %s...", settings.APP_NAME)
    await close_connection()


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy" if is_connected() else "degraded",
        app_name=settings.APP_NAME,
        app_version=settings.APP_VERSION,
        database_connected=is_connected(),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/api/dashboard")
async def get_dashboard(brand: Optional[str] = None):
    """Get current dashboard data: gauges, trends, alerts, actions, sources."""
    if not is_connected():
        raise HTTPException(status_code=503, detail="Database not connected.")

    try:
        analytics = AnalyticsAgent()
        dashboard = await analytics.get_dashboard_stats(brand=brand)

        # Flatten into the shape the frontend expects
        return {
            "gauges": dashboard.get("sentiment_distribution", {}),
            "avg_score": dashboard.get("avg_score", 0),
            "trends": dashboard.get("trends", []),
            "alerts": dashboard.get("alerts", []),
            "actions": dashboard.get("actions", []),
            "sources": dashboard.get("source_breakdown", []),
            "recent_reviews": dashboard.get("recent_reviews", []),
            "top_aspects": dashboard.get("top_aspects", []),
            "emotion_distribution": dashboard.get("emotion_distribution", []),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as exc:
        logger.error("Dashboard endpoint failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/analyze")
async def run_analysis(request: AnalyzeRequest):
    """
    Trigger the full 6-step agentic workflow with Server-Sent Events (SSE) streaming.
    Returns a streaming response with progress events.
    """
    if not is_connected():
        raise HTTPException(status_code=503, detail="Database not connected.")

    progress_queue: asyncio.Queue = asyncio.Queue()

    def progress_callback(event: dict):
        progress_queue.put_nowait(event)

    async def event_generator():
        orchestrator = SentimentOrchestrator(progress_callback=progress_callback)
        task = asyncio.create_task(
            orchestrator.run_analysis(
                topic=request.topic,
                brand=request.brand,
                use_web_search=request.use_web_search,
            )
        )

        try:
            while True:
                try:
                    event = await asyncio.wait_for(progress_queue.get(), timeout=5.0)
                    yield f"data: {json.dumps(event, default=str)}\n\n"
                    if event.get("type") in ("complete", "error"):
                        break
                except asyncio.TimeoutError:
                    if task.done():
                        # Check if there was an unhandled exception
                        exc = task.exception()
                        if exc:
                            error_event = {
                                "type": "error",
                                "message": f"Pipeline error: {exc}",
                                "error": str(exc),
                            }
                            yield f"data: {json.dumps(error_event, default=str)}\n\n"
                        break
                    # Send keepalive ping
                    yield f"data: {json.dumps({'type': 'ping'})}\n\n"
        except asyncio.CancelledError:
            task.cancel()
            logger.info("SSE stream cancelled by client.")
        except Exception as exc:
            logger.error("SSE stream error: %s", exc, exc_info=True)
            error_event = {
                "type": "error",
                "message": f"Streaming error: {exc}",
                "error": str(exc),
            }
            yield f"data: {json.dumps(error_event, default=str)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/query")
async def natural_language_query(request: QueryRequest):
    """Run a natural language query on sentiment data via Select AI."""
    if not is_connected():
        raise HTTPException(status_code=503, detail="Database not connected.")

    try:
        analytics = AnalyticsAgent()
        result = await analytics.query(request.question)

        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])

        return {
            "question": request.question,
            "sql": result.get("sql"),
            "data": result.get("data", []),
            "narrative": result.get("narrative"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Query endpoint failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/rag-query")
async def rag_query(request: RAGQueryRequest):
    """Query the knowledge base using Select AI RAG with vector search."""
    if not is_connected():
        raise HTTPException(status_code=503, detail="Database not connected.")

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Use DBMS_CLOUD_AI.GENERATE with the RAG profile
        result_clob = cursor.var(oracledb.DB_TYPE_CLOB)
        cursor.execute(
            """
            BEGIN
                :result := DBMS_CLOUD_AI.GENERATE(
                    prompt       => :question,
                    profile_name => 'OCI_SELECTAI_RAG',
                    action       => 'narrate'
                );
            END;
            """,
            {"result": result_clob, "question": request.question},
        )

        answer_raw = result_clob.getvalue()
        answer = answer_raw.read() if hasattr(answer_raw, "read") else str(answer_raw or "")

        return {
            "question": request.question,
            "answer": answer,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as exc:
        logger.error("RAG query failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


@app.get("/api/alerts")
async def get_alerts():
    """Get active sentiment alerts from the database."""
    if not is_connected():
        raise HTTPException(status_code=503, detail="Database not connected.")

    try:
        analytics = AnalyticsAgent()
        dashboard = await analytics.get_dashboard_stats()
        return {
            "alerts": dashboard.get("alerts", []),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as exc:
        logger.error("Alerts endpoint failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/actions")
async def get_actions():
    """Get action recommendations from the database."""
    if not is_connected():
        raise HTTPException(status_code=503, detail="Database not connected.")

    try:
        analytics = AnalyticsAgent()
        dashboard = await analytics.get_dashboard_stats()
        return {
            "actions": dashboard.get("actions", []),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as exc:
        logger.error("Actions endpoint failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/reviews")
async def get_reviews(
    limit: int = 20,
    offset: int = 0,
    sentiment: Optional[str] = None,
):
    """Get recent reviews with their sentiment results."""
    if not is_connected():
        raise HTTPException(status_code=503, detail="Database not connected.")

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Build query with optional sentiment filter
        where_clause = ""
        bind_vars = {"lim": limit, "off": offset}

        if sentiment and sentiment in ("Positive", "Negative", "Neutral"):
            where_clause = "WHERE s.SENTIMENT = :sentiment"
            bind_vars["sentiment"] = sentiment

        sql = f"""
            SELECT
                r.id,
                r.source,
                r.author,
                r.review_text,
                r.url,
                r.brand,
                r.product,
                r.scraped_at,
                r.rating,
                s.sentiment,
                s.score,
                s.aspects_json,
                s.explanation,
                s.emotions,
                s.analyzed_at
            FROM scraped_reviews r
            LEFT JOIN sentiment_results s ON r.id = s.review_id
            {where_clause}
            ORDER BY r.scraped_at DESC
            OFFSET :off ROWS FETCH NEXT :lim ROWS ONLY
        """

        cursor.execute(sql, bind_vars)
        rows = cursor.fetchall()

        reviews = []
        for row in rows:
            review_text = row[3]
            if hasattr(review_text, "read"):
                review_text = review_text.read()

            aspects_raw = row[11]
            if aspects_raw and hasattr(aspects_raw, "read"):
                aspects_raw = aspects_raw.read()

            try:
                aspects = json.loads(str(aspects_raw)) if aspects_raw else []
            except (json.JSONDecodeError, TypeError):
                aspects = []

            emotions_raw = row[13]
            try:
                emotions = json.loads(str(emotions_raw)) if emotions_raw else []
            except (json.JSONDecodeError, TypeError):
                emotions = []

            reviews.append({
                "id": row[0],
                "source": row[1],
                "author": row[2],
                "review_text": str(review_text or "")[:500],
                "url": row[4],
                "brand": row[5],
                "product": row[6],
                "scraped_at": row[7].isoformat() if row[7] else None,
                "rating": float(row[8]) if row[8] is not None else None,
                "sentiment": row[9],
                "score": float(row[10]) if row[10] is not None else None,
                "aspects": aspects,
                "explanation": row[12],
                "emotions": emotions,
                "analyzed_at": row[14].isoformat() if row[14] else None,
            })

        # Get total count
        count_sql = f"""
            SELECT COUNT(*)
            FROM scraped_reviews r
            LEFT JOIN sentiment_results s ON r.id = s.review_id
            {where_clause}
        """
        count_vars = {}
        if sentiment and sentiment in ("Positive", "Negative", "Neutral"):
            count_vars["sentiment"] = sentiment
        cursor.execute(count_sql, count_vars)
        total = cursor.fetchone()[0]

        return {
            "reviews": reviews,
            "total": total,
            "limit": limit,
            "offset": offset,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as exc:
        logger.error("Reviews endpoint failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


@app.get("/api/history")
async def get_history(brand: Optional[str] = None):
    """Get historical data for charts: review volume over time, score history, brands analyzed."""
    if not is_connected():
        raise HTTPException(status_code=503, detail="Database not connected.")

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        brand_bind = {"brand": brand} if brand else {}

        # Review volume over time (by day, last 90 days)
        vol_where = "WHERE r.scraped_at >= SYSDATE - 90 AND r.brand = :brand" if brand else "WHERE r.scraped_at >= SYSDATE - 90"
        cursor.execute(f"""
            SELECT TRUNC(r.scraped_at) AS day, COUNT(*) AS review_count
            FROM scraped_reviews r
            {vol_where}
            GROUP BY TRUNC(r.scraped_at)
            ORDER BY day
        """, brand_bind)
        volume_over_time = [
            {"date": row[0].isoformat() if row[0] else None, "count": int(row[1])}
            for row in cursor.fetchall()
        ]

        # Score history (average score per day)
        sc_join = "JOIN scraped_reviews r ON s.review_id = r.id" if brand else ""
        sc_where = "WHERE s.analyzed_at >= SYSDATE - 90 AND r.brand = :brand" if brand else "WHERE s.analyzed_at >= SYSDATE - 90"
        cursor.execute(f"""
            SELECT TRUNC(s.analyzed_at) AS day,
                   ROUND(AVG(s.score), 3) AS avg_score,
                   COUNT(*) AS review_count
            FROM sentiment_results s
            {sc_join}
            {sc_where}
            GROUP BY TRUNC(s.analyzed_at)
            ORDER BY day
        """, brand_bind)
        score_history = [
            {"date": row[0].isoformat() if row[0] else None, "avg_score": float(row[1] or 0), "count": int(row[2])}
            for row in cursor.fetchall()
        ]

        # All brands analyzed
        cursor.execute("""
            SELECT DISTINCT brand FROM scraped_reviews WHERE brand IS NOT NULL ORDER BY brand
        """)
        brands = [row[0] for row in cursor.fetchall()]

        return {
            "volume_over_time": volume_over_time,
            "score_history": score_history,
            "brands": brands,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:
        logger.error("History endpoint failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


@app.post("/api/generate-campaign")
async def generate_campaign(request: CampaignRequest):
    """Generate personalized marketing email variants using OCI GenAI informed by sentiment data."""
    if not is_connected():
        raise HTTPException(status_code=503, detail="Database not connected.")

    try:
        # Fetch sentiment context for the brand
        analytics = AnalyticsAgent()
        stats = await analytics.get_dashboard_stats(brand=request.brand)

        # Generate campaign variants
        agent = CampaignAgent()
        variants = await agent.generate_campaign(
            brand=request.brand,
            campaign_objective=request.campaign_objective,
            tone=request.tone,
            sentiment_context=stats,
        )

        return {
            "variants": variants,
            "brand": request.brand,
            "campaign_objective": request.campaign_objective,
            "tone": request.tone,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as exc:
        logger.error("Campaign generation failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/analyze-review")
async def analyze_single_review(request: ReviewAnalyzeRequest):
    """Analyze a single review text and return sentiment without persisting."""
    if not is_connected():
        raise HTTPException(status_code=503, detail="Database not connected.")

    try:
        agent = SentimentAgent()
        result = await agent.analyze_single_review(request.review_text)
        return {
            "review_text": request.review_text[:200] + ("..." if len(request.review_text) > 200 else ""),
            "sentiment": result,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:
        logger.error("Single review analysis failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    logger.info(
        "Starting %s v%s on %s:%d",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.API_HOST,
        settings.API_PORT,
    )
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        log_level="info",
    )
