from fastapi import FastAPI, HTTPException, Header, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
import uuid
from datetime import datetime
import json

from app.middleware.rate_limiter import verify_rate_limit_fastapi, RateLimitMiddleware
from worker.celery_app import process_query_task, get_task_status
from app.api.schemas import (
    QueryRequest, QueryResponse, TaskStatusResponse, 
    SearchRequest, SearchResponse
)
from app.config import settings, create_agents
from app.graph.multi_agent_workflow import create_multi_agent_graph
from langchain_core.documents import Document

# Pydantic Models
class QueryRequest(BaseModel):
    input: str

class QueryResponse(BaseModel):
    status: str
    task_id: Optional[str] = None
    message: Optional[str] = None
    output: Optional[str] = None

class TaskStatusResponse(BaseModel):
    status: str
    task_id: str
    output: Optional[str] = None
    error: Optional[str] = None

class SearchRequest(BaseModel):
    query: str

class SearchResponse(BaseModel):
    status: str
    documents: List[Dict[str, Any]]
    count: int

# Initialize FastAPI app
app = FastAPI(
    title="Multi-Agent AI System",
    description="A state-of-the-art multi-agent system using FastAPI and Celery",
    version="1.0.0"
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

# Frontend HTML template
FRONTEND_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Multi-Agent AI System</title>
    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            background-color: #f4f4f4;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        h1 {
            color: #333;
            text-align: center;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }
        #query-input {
            width: 100%;
            padding: 10px;
            margin-bottom: 15px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        #submit-btn {
            width: 100%;
            padding: 10px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        #submit-btn:hover {
            background-color: #45a049;
        }
        #result {
            margin-top: 20px;
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 4px;
            border: 1px solid #eee;
            min-height: 100px;
            white-space: pre-wrap;
        }
        #loading {
            display: none;
            text-align: center;
            color: #666;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Multi-Agent AI System</h1>
        
        <input type="text" id="query-input" placeholder="Enter your query...">
        <button id="submit-btn">Process Query</button>
        
        <div id="loading">Processing your query...</div>
        <div id="result"></div>
    </div>

    <script>
        document.getElementById('submit-btn').addEventListener('click', async () => {
            const queryInput = document.getElementById('query-input');
            const resultDiv = document.getElementById('result');
            const loadingDiv = document.getElementById('loading');
            
            resultDiv.textContent = '';
            loadingDiv.style.display = 'block';
            
            try {
                const response = await axios.post('/api/process', {
                    input: queryInput.value
                });
                
                if (response.data.status === 'processing') {
                    // Poll for results
                    const taskId = response.data.task_id;
                    pollForResult(taskId);
                } else {
                    resultDiv.textContent = response.data.output || 'No output received';
                    loadingDiv.style.display = 'none';
                }
            } catch (error) {
                resultDiv.textContent = `Error: ${error.response ? error.response.data.detail : error.message}`;
                loadingDiv.style.display = 'none';
            }
        });
        
        async function pollForResult(taskId) {
            try {
                const response = await axios.get(`/api/task/${taskId}`);
                const data = response.data;
                
                if (data.status === 'completed') {
                    document.getElementById('result').textContent = data.output;
                    document.getElementById('loading').style.display = 'none';
                } else if (data.status === 'failed') {
                    document.getElementById('result').textContent = `Error: ${data.error}`;
                    document.getElementById('loading').style.display = 'none';
                } else {
                    // Still processing, poll again
                    setTimeout(() => pollForResult(taskId), 2000);
                }
            } catch (error) {
                document.getElementById('result').textContent = `Error checking status: ${error.message}`;
                document.getElementById('loading').style.display = 'none';
            }
        }
    </script>
</body>
</html>"""

# Routes
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
    # Verify rate limit
    tier = verify_rate_limit_fastapi(x_api_key)
    
    # Generate task ID
    task_id = str(uuid.uuid4())
    
    # Queue the task for asynchronous processing
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
    # Verify rate limit
    verify_rate_limit_fastapi(x_api_key)
    
    try:
        # Initialize RAG agent
        rag_agent, _, _, _ = create_agents()
        
        # Retrieve documents
        documents = await rag_agent.retrieve_documents(request.query)
        
        # Format documents for response
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
