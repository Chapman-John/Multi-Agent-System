from celery import Celery
from app.config import settings
from app.services.agent_service import get_agent_service
import json
import time
from redis import Redis
import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Celery with settings
celery_app = Celery(
    "multi_agent_system",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Configure Redis
redis_client = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB + 1  # Use different DB than rate limiter
)

@celery_app.task(bind=True)
def process_query_task(self, task_id: str, input_text: str, tier: str = "free"):
    """Process a query through the multi-agent workflow"""
    try:
        update_task_status(task_id, "processing", {"stage": "initializing"})
        
        # Set priority based on tier
        priority_map = {"premium": 9, "basic": 5, "free": 1}
        self.request.delivery_info['priority'] = priority_map.get(tier, 1)
        
        # Get agent service
        agent_service = get_agent_service()
        
        # Create event loop for async operations
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Run async workflow in sync context
            result = loop.run_until_complete(
                agent_service.workflow.ainvoke({"input": input_text})
            )
            
            output = result.get("final_output", "No output generated")
            
            update_task_status(task_id, "completed", {
                "output": output,
                "research_result": result.get("research_result", ""),
                "completed_at": time.time()
            })
            
            return {"status": "completed", "task_id": task_id, "output": output}
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error processing task {task_id}: {str(e)}")
        update_task_status(task_id, "failed", {"error": str(e)})
        raise

def update_task_status(task_id: str, status: str, data: dict = None):
    """Update task status in Redis"""
    task_info = {"status": status, "updated_at": time.time()}
    if data:
        task_info.update(data)
    redis_client.set(f"task:{task_id}", json.dumps(task_info), ex=86400)

def get_task_status(task_id: str):
    """Get task status from Redis"""
    task_data = redis_client.get(f"task:{task_id}")
    return json.loads(task_data) if task_data else None