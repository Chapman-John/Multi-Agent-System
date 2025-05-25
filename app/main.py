from fastapi import FastAPI, HTTPException, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from typing import Optional, Dict, Any, List
import uuid

from app.middleware.rate_limiter import verify_rate_limit_fastapi, RateLimitMiddleware
from worker.celery_app import process_query_task, get_task_status
from app.api.schemas import (
    QueryRequest, QueryResponse, TaskStatusResponse, 
    SearchRequest, SearchResponse
)
from app.config import settings, create_agents
from langchain_core.documents import Document

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="A state-of-the-art multi-agent system using FastAPI and Celery",
    version=settings.VERSION
)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Frontend HTML template (keep existing FRONTEND_HTML)
FRONTEND_HTML = """..."""  # Keep existing template

# Routes - Remove all duplicate class definitions
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the frontend interface"""
    return FRONTEND_HTML

@app.post("/api/process", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    background_tasks: BackgroundTasks,
    x_api_key: Optional[str] = Header(None),
):
    """Process a query through the multi-agent workflow"""
    tier = verify_rate_limit_fastapi(x_api_key)
    task_id = str(uuid.uuid4())
    
    task = process_query_task.delay(
        task_id=task_id,
        input_text=request.input,
        tier=tier
    )
    
    return QueryResponse(
        status="processing",
        task_id=task_id,
        message="Query processing started"
    )

@app.get("/api/task/{task_id}", response_model=TaskStatusResponse)
async def get_task(task_id: str):
    """Get the status and result of a task"""
    task_result = get_task_status(task_id)
    
    if not task_result:
        raise HTTPException(status_code=404, detail="Task not found")
        
    return TaskStatusResponse(**task_result, task_id=task_id)

@app.post("/api/search", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    x_api_key: Optional[str] = Header(None),
):
    """Search documents directly without full processing"""
    verify_rate_limit_fastapi(x_api_key)
    
    try:
        rag_agent, _, _, _ = create_agents()
        documents = await rag_agent.retrieve_documents(request.query)
        
        formatted_docs = []
        for doc in documents:
            if isinstance(doc, Document):
                formatted_docs.append({
                    'content': doc.page_content,
                    'metadata': doc.metadata
                })
            else:
                formatted_docs.append(doc)
        
        return SearchResponse(
            status="success",
            documents=formatted_docs,
            count=len(formatted_docs)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)