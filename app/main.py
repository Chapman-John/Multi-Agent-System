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

# Complete Frontend HTML template
FRONTEND_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Multi-Agent AI System</title>
    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            background-color: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
        }
        h1 {
            color: #333;
            text-align: center;
            border-bottom: 3px solid #667eea;
            padding-bottom: 15px;
            margin-bottom: 30px;
            font-size: 2.5em;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 1.1em;
        }
        #query-input {
            width: 100%;
            padding: 15px;
            margin-bottom: 20px;
            border: 2px solid #ddd;
            border-radius: 8px;
            box-sizing: border-box;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        #query-input:focus {
            outline: none;
            border-color: #667eea;
        }
        #submit-btn {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        #submit-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        #submit-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        #result {
            margin-top: 25px;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            min-height: 120px;
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
            display: none;
        }
        #loading {
            display: none;
            text-align: center;
            color: #667eea;
            margin-top: 20px;
            font-weight: bold;
        }
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .status {
            text-align: center;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }
        .status.processing {
            background-color: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
        }
        .status.completed {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #00b894;
        }
        .status.error {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #e74c3c;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Multi-Agent AI System</h1>
        <p class="subtitle">Powered by specialized AI agents working together</p>
        
        <input type="text" id="query-input" placeholder="Enter your query (e.g., 'Explain quantum computing applications')...">
        <button id="submit-btn">Process Query</button>
        
        <div id="loading">
            <div class="spinner"></div>
            Processing your query through our AI agents...
        </div>
        <div id="result"></div>
    </div>

    <script>
        let currentTaskId = null;
        
        document.getElementById('submit-btn').addEventListener('click', async () => {
            const queryInput = document.getElementById('query-input');
            const resultDiv = document.getElementById('result');
            const loadingDiv = document.getElementById('loading');
            const submitBtn = document.getElementById('submit-btn');
            
            if (!queryInput.value.trim()) {
                alert('Please enter a query');
                return;
            }
            
            // Reset UI
            resultDiv.style.display = 'none';
            resultDiv.innerHTML = '';
            loadingDiv.style.display = 'block';
            submitBtn.disabled = true;
            submitBtn.textContent = 'Processing...';
            
            try {
                const response = await axios.post('/api/process', {
                    input: queryInput.value.trim()
                });
                
                if (response.data.status === 'processing') {
                    currentTaskId = response.data.task_id;
                    showStatus('Processing started...', 'processing');
                    pollForResult(currentTaskId);
                } else {
                    displayResult(response.data.output || 'No output received');
                }
            } catch (error) {
                displayError(`Error: ${error.response ? error.response.data.detail : error.message}`);
            }
        });
        
        async function pollForResult(taskId) {
            try {
                const response = await axios.get(`/api/task/${taskId}`);
                const data = response.data;
                
                if (data.status === 'completed') {
                    displayResult(data.output);
                    showStatus('Query completed successfully!', 'completed');
                } else if (data.status === 'failed') {
                    displayError(`Processing failed: ${data.error}`);
                } else {
                    // Still processing, poll again
                    setTimeout(() => pollForResult(taskId), 2000);
                }
            } catch (error) {
                displayError(`Error checking status: ${error.message}`);
            }
        }
        
        function displayResult(output) {
            const resultDiv = document.getElementById('result');
            const loadingDiv = document.getElementById('loading');
            const submitBtn = document.getElementById('submit-btn');
            
            resultDiv.innerHTML = output;
            resultDiv.style.display = 'block';
            loadingDiv.style.display = 'none';
            submitBtn.disabled = false;
            submitBtn.textContent = 'Process Query';
        }
        
        function displayError(message) {
            const resultDiv = document.getElementById('result');
            const loadingDiv = document.getElementById('loading');
            const submitBtn = document.getElementById('submit-btn');
            
            resultDiv.innerHTML = message;
            resultDiv.style.display = 'block';
            loadingDiv.style.display = 'none';
            submitBtn.disabled = false;
            submitBtn.textContent = 'Process Query';
            showStatus('Error occurred', 'error');
        }
        
        function showStatus(message, type) {
            // Remove existing status
            const existingStatus = document.querySelector('.status');
            if (existingStatus) {
                existingStatus.remove();
            }
            
            // Add new status
            const statusDiv = document.createElement('div');
            statusDiv.className = `status ${type}`;
            statusDiv.textContent = message;
            document.querySelector('.container').insertBefore(statusDiv, document.getElementById('loading'));
            
            // Remove status after 3 seconds for non-processing states
            if (type !== 'processing') {
                setTimeout(() => statusDiv.remove(), 3000);
            }
        }
        
        // Allow Enter key to submit
        document.getElementById('query-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                document.getElementById('submit-btn').click();
            }
        });
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