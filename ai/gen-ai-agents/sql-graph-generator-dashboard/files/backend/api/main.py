"""
FastAPI server for SQL Graph Generator Dashboard
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import json
import logging

from orchestration.langchain_orchestrator_v2 import LangChainOrchestratorV2

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SQL Graph Generator Dashboard", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize LangChain orchestrator
orchestrator = LangChainOrchestratorV2()

# Request/Response models
class QueryRequest(BaseModel):
    question: str
    context: Optional[str] = ""

class QueryResponse(BaseModel):
    success: bool
    response_type: str  # "visualization", "data", "error"
    query: Optional[str] = None
    agent_response: Optional[str] = None
    dashboard: Optional[Dict] = None
    data: Optional[List[Dict]] = None
    insights: Optional[List[str]] = None
    text_response: Optional[str] = None
    error: Optional[str] = None
    chart_base64: Optional[str] = None
    chart_config: Optional[Dict] = None
    method: Optional[str] = None
    generated_sql: Optional[str] = None
    additional_info: Optional[str] = None

@app.get("/")
async def root():
    return {
        "message": "SQL Graph Generator Dashboard API",
        "version": "1.0.0",
        "status": "active"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "sql-graph-generator"}

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a user query and return data, visualization, or text response
    """
    try:
        logger.info(f"Processing query: {request.question}")
        
        result = orchestrator.process_natural_language_query(request.question)
        
        return QueryResponse(**result)
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sample-questions")
async def get_sample_questions():
    """
    Get sample questions that users can ask
    """
    return {
        "questions": orchestrator.get_sample_questions(),
        "description": "Sample questions you can ask the SQL Graph Generator"
    }

@app.get("/database-schema")
async def get_database_schema():
    """
    Get the database schema information
    """
    from utils.config import DATABASE_SCHEMA
    return {
        "schema": DATABASE_SCHEMA,
        "description": "E-commerce database schema with orders, customers, products, and order_items"
    }

@app.get("/chart-types")
async def get_supported_chart_types():
    """
    Get supported chart types
    """
    return {
        "chart_types": [
            {"type": "bar", "description": "Bar charts for category comparisons"},
            {"type": "line", "description": "Line charts for trends over time"},
            {"type": "pie", "description": "Pie charts for distributions"},
            {"type": "scatter", "description": "Scatter plots for correlations"},
            {"type": "heatmap", "description": "Heatmaps for correlation analysis"}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)