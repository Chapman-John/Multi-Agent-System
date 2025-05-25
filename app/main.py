from fastapi import FastAPI, HTTPException, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from typing import Optional, Dict, Any, List
import uuid
import os
import logging
import traceback

from app.middleware.rate_limiter import verify_rate_limit_fastapi, RateLimitMiddleware
from worker.celery_app import process_query_task, get_task_status
from app.api.schemas import (
    QueryRequest, QueryResponse, TaskStatusResponse, 
    SearchRequest, SearchResponse
)
from app.config import settings, create_agents
from langchain_core.documents import Document

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Complete Frontend HTML template with better error handling
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
        .debug-info {
            margin-top: 15px;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 5px;
            font-size: 12px;
            color: #666;
            border-left: 3px solid #007bff;
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
            <div id="debug-info" class="debug-info" style="display: none;"></div>
        </div>
        <div id="result"></div>
    </div>

    <script>
        let currentTaskId = null;
        let pollCount = 0;
        const maxPollAttempts = 30; // 1 minute of polling
        
        document.getElementById('submit-btn').addEventListener('click', async () => {
            const queryInput = document.getElementById('query-input');
            const resultDiv = document.getElementById('result');
            const loadingDiv = document.getElementById('loading');
            const submitBtn = document.getElementById('submit-btn');
            const debugInfo = document.getElementById('debug-info');
            
            if (!queryInput.value.trim()) {
                alert('Please enter a query');
                return;
            }
            
            // Reset UI
            resultDiv.style.display = 'none';
            resultDiv.innerHTML = '';
            loadingDiv.style.display = 'block';
            debugInfo.style.display = 'block';
            submitBtn.disabled = true;
            submitBtn.textContent = 'Processing...';
            pollCount = 0;
            
            updateDebugInfo('Submitting query...');
            
            try {
                const response = await axios.post('/api/process', {
                    input: queryInput.value.trim()
                }, {
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    timeout: 10000 // 10 second timeout
                });
                
                updateDebugInfo(`Task created with ID: ${response.data.task_id}`);
                
                if (response.data.status === 'processing') {
                    currentTaskId = response.data.task_id;
                    showStatus('Processing started...', 'processing');
                    setTimeout(() => pollForResult(currentTaskId), 1000); // Start polling after 1 second
                } else {
                    displayResult(response.data.output || 'No output received');
                }
            } catch (error) {
                let errorMessage = 'Unknown error occurred';
                
                if (error.response) {
                    // Server responded with error status
                    errorMessage = `Server Error (${error.response.status}): ${error.response.data?.detail || error.response.statusText}`;
                    updateDebugInfo(`Server responded with ${error.response.status}: ${JSON.stringify(error.response.data)}`);
                } else if (error.request) {
                    // Request was made but no response received
                    errorMessage = 'No response from server. Please check your connection.';
                    updateDebugInfo('No response received from server');
                } else {
                    // Something else happened
                    errorMessage = `Request Error: ${error.message}`;
                    updateDebugInfo(`Request setup error: ${error.message}`);
                }
                
                displayError(errorMessage);
            }
        });
        
        async function pollForResult(taskId) {
            pollCount++;
            updateDebugInfo(`Checking task status... (attempt ${pollCount}/${maxPollAttempts})`);
            
            try {
                const response = await axios.get(`/api/task/${taskId}`, {
                    timeout: 5000 // 5 second timeout for status checks
                });
                const data = response.data;
                
                updateDebugInfo(`Status: ${data.status} (${new Date().toLocaleTimeString()})`);
                
                if (data.status === 'completed') {
                    displayResult(data.output || 'Task completed but no output received');
                    showStatus('Query completed successfully!', 'completed');
                } else if (data.status === 'failed') {
                    displayError(`Processing failed: ${data.error || 'Unknown error'}`);
                } else if (pollCount >= maxPollAttempts) {
                    displayError('Task is taking too long. Please try again later.');
                    updateDebugInfo('Polling timeout reached');
                } else {
                    // Still processing, poll again
                    setTimeout(() => pollForResult(taskId), 2000);
                }
            } catch (error) {
                updateDebugInfo(`Error checking status: ${error.message}`);
                
                if (error.response?.status === 404) {
                    displayError(`Task not found (ID: ${taskId}). This might indicate a worker issue.`);
                    updateDebugInfo('Task 404 error - possible worker or Redis connection issue');
                } else if (pollCount >= maxPollAttempts) {
                    displayError('Unable to check task status. Please try again later.');
                } else {
                    // Retry polling
                    setTimeout(() => pollForResult(taskId), 3000);
                }
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
            
            resultDiv.innerHTML = `❌ Error: ${message}`;
            resultDiv.style.display = 'block';
            resultDiv.style.borderLeft = '4px solid #e74c3c';
            resultDiv.style.backgroundColor = '#fff5f5';
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
        
        function updateDebugInfo(message) {
            const debugInfo = document.getElementById('debug-info');
            const timestamp = new Date().toLocaleTimeString();
            debugInfo.innerHTML += `<div>[${timestamp}] ${message}</div>`;
            debugInfo.scrollTop = debugInfo.scrollHeight;
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

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Redis connection
        from worker.celery_app import redis_client
        redis_client.ping()
        redis_status = "healthy"
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "redis": redis_status,
        "timestamp": os.time.time() if hasattr(os, 'time') else "unknown"
    }

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
    try:
        logger.info(f"Processing query: {request.input[:100]}...")
        
        # Verify rate limit
        tier = verify_rate_limit_fastapi(x_api_key)
        logger.info(f"Rate limit verified for tier: {tier}")
        
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        logger.info(f"Generated task ID: {task_id}")
        
        # Submit task to Celery
        try:
            task = process_query_task.delay(
                task_id=task_id,
                input_text=request.input,
                tier=tier
            )
            logger.info(f"Task submitted to Celery: {task.id}")
            
            # Verify task was created in Redis
            from worker.celery_app import get_task_status
            initial_status = get_task_status(task_id)
            logger.info(f"Initial task status: {initial_status}")
            
        except Exception as e:
            logger.error(f"Failed to submit task to Celery: {str(e)}")
            logger.error(f"Celery error traceback: {traceback.format_exc()}")
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to start task processing: {str(e)}"
            )
        
        return QueryResponse(
            status="processing",
            task_id=task_id,
            message="Query processing started"
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error in process_query: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/api/task/{task_id}", response_model=TaskStatusResponse)
async def get_task(task_id: str):
    """Get the status and result of a task"""
    try:
        logger.debug(f"Checking status for task: {task_id}")
        
        task_result = get_task_status(task_id)
        
        if not task_result:
            logger.warning(f"Task not found: {task_id}")
            
            # Try to get Celery task status as fallback
            try:
                from celery.result import AsyncResult
                celery_task = AsyncResult(task_id)
                logger.info(f"Celery task state: {celery_task.state}")
                
                if celery_task.state == 'PENDING':
                    return TaskStatusResponse(
                        status="processing",
                        task_id=task_id,
                        output=None,
                        error=None,
                        updated_at=None
                    )
                elif celery_task.state == 'FAILURE':
                    return TaskStatusResponse(
                        status="failed",
                        task_id=task_id,
                        output=None,
                        error=str(celery_task.info),
                        updated_at=None
                    )
            except Exception as celery_error:
                logger.error(f"Failed to check Celery task: {celery_error}")
            
            raise HTTPException(
                status_code=404, 
                detail=f"Task {task_id} not found. Task may have expired or failed to start."
            )
        
        logger.debug(f"Task status retrieved: {task_result}")
        return TaskStatusResponse(**task_result, task_id=task_id)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error retrieving task {task_id}: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve task status: {str(e)}"
        )

@app.post("/api/search", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    x_api_key: Optional[str] = Header(None),
):
    """Search documents directly without full processing"""
    try:
        verify_rate_limit_fastapi(x_api_key)
        logger.info(f"Document search request: {request.query}")
        
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
        
        logger.info(f"Found {len(formatted_docs)} documents")
        return SearchResponse(
            status="success",
            documents=formatted_docs,
            count=len(formatted_docs)
        )
        
    except Exception as e:
        logger.error(f"Error in document search: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

# Debug endpoint to check system status
@app.get("/api/debug")
async def debug_info():
    """Debug endpoint to check system components"""
    debug_data = {
        "app_status": "running",
        "settings": {
            "redis_host": settings.REDIS_HOST,
            "redis_port": settings.REDIS_PORT,
            "celery_broker": settings.CELERY_BROKER_URL,
        }
    }
    
    # Test Redis connection
    try:
        from worker.celery_app import redis_client
        redis_client.ping()
        debug_data["redis_status"] = "connected"
    except Exception as e:
        debug_data["redis_status"] = f"error: {str(e)}"
    
    # Test Celery connection
    try:
        from worker.celery_app import celery_app
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        debug_data["celery_workers"] = list(active_workers.keys()) if active_workers else []
        debug_data["celery_status"] = "connected" if active_workers else "no_workers"
    except Exception as e:
        debug_data["celery_status"] = f"error: {str(e)}"
    
    return debug_data

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)