from celery import Celery
from typing import Dict, Any, Optional
import os
import time
import json
from redis import Redis

# Configure Celery
celery_app = Celery(
    "multi_agent_system",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
)

# Configure Redis
redis_client = Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=int(os.getenv("REDIS_DB", 1))  # Use different DB than rate limiter
)

# Import models, agents, and workflow after Celery is configured
from config.settings import create_agents
from app.graph.multi_agent_workflow import create_multi_agent_graph

# Celery task for processing queries
@celery_app.task(bind=True)
def process_query_task(self, task_id: str, input_text: str, tier: str = "free"):
    """
    Process a query through the multi-agent workflow
    
    Args:
        task_id (str): Unique task identifier
        input_text (str): Query to process
        tier (str): User tier for processing priority
    """
    try:
        # Update task status to processing
        update_task_status(task_id, "processing", None)
        
        # Set task priority based on tier
        if tier == "premium":
            self.request.delivery_info['priority'] = 9
        elif tier == "basic":
            self.request.delivery_info['priority'] = 5
        else:  # free tier
            self.request.delivery_info['priority'] = 1
            
        # Initialize agents
        rag_agent, researcher, writer, reviewer = create_agents()
        
        # Create workflow graph
        graph = create_multi_agent_graph(rag_agent, researcher, writer, reviewer)
        
        # Track processing stages
        update_task_status(task_id, "processing", {"stage": "rag"})
        
        # Run the workflow (this will be synchronous within the Celery task)
        result = graph.invoke({"input": input_text})
        
        # Process result
        output = result.get("final_output", "No output generated")
        
        # Update task status to completed
        update_task_status(
            task_id, 
            "completed", 
            {
                "output": output,
                "research_result": result.get("research_result", ""),
                "completed_at": time.time()
            }
        )
        
        return {
            "status": "completed", 
            "task_id": task_id, 
            "output": output
        }
        
    except Exception as e:
        # Update task status to failed
        update_task_status(
            task_id, 
            "failed", 
            {"error": str(e)}
        )
        
        # Re-raise for Celery's error handling
        raise

def update_task_status(task_id: str, status: str, data: Optional[Dict[str, Any]] = None):
    """
    Update task status in Redis
    
    Args:
        task_id (str): Task identifier
        status (str): Current status
        data (Dict, optional): Additional data
    """
    task_info = {
        "status": status,
        "updated_at": time.time()
    }
    
    if data:
        task_info.update(data)
        
    redis_client.set(
        f"task:{task_id}", 
        json.dumps(task_info),
        ex=86400  # Expire after 24 hours
    )

def get_task_status(task_id: str) -> Optional[Dict[str, Any]]:
    """
    Get task status from Redis
    
    Args:
        task_id (str): Task identifier
        
    Returns:
        Dict or None: Task information
    """
    task_data = redis_client.get(f"task:{task_id}")
    
    if not task_data:
        return None
        
    return json.loads(task_data)

# Celery configuration
celery_app.conf.task_routes = {
    'app.celery_app.process_query_task': {'queue': 'agent_tasks'}
}

celery_app.conf.task_queues = {
    'agent_tasks': {
        'exchange': 'agent_tasks',
        'routing_key': 'agent_tasks',
    }
}

# Configure task priorities
celery_app.conf.task_queue_max_priority = 10
celery_app.conf.task_default_priority = 5

# Optimize for long-running tasks
celery_app.conf.worker_prefetch_multiplier = 1
celery_app.conf.task_acks_late = True
