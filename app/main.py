from fastapi import FastAPI, Depends, HTTPException, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
import uuid
from datetime import datetime

from app.middleware.rate_limiter import verify_rate_limit
from app.celery_app import process_query_task, get_task_status
from app.schemas import QueryRequest, QueryResponse, TaskStatusResponse

# Initialize FastAPI app
app = FastAPI(
    title="Multi-Agent AI System",
    description="A state-of-the-art multi-agent system using FastAPI and Celery",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Specify allowed origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
@app.post("/api/process", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    background_tasks: BackgroundTasks,
    x_api_key: Optional[str] = Header(None),
):
    """
    Process a query through the multi-agent workflow
    """
    # Verify rate limit
    tier = verify_rate_limit(x_api_key)
    
    # Generate task ID
    task_id = str(uuid.uuid4())
    
    # Queue the task for asynchronous processing
    background_tasks.add_task(
        process_query_task.delay,
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
    """
    Get the status and result of a task
    """
    task_result = get_task_status(task_id)
    
    if not task_result:
        raise HTTPException(status_code=404, detail="Task not found")
        
    return task_result

@app.get("/")
async def read_root():
    """
    Root endpoint
    """
    return {"message": "Multi-Agent AI System API"}

# Start the application with: uvicorn app.main:app --reload
