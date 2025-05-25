from celery import Celery
from app.config import settings
from app.services.agent_service import get_agent_service
import json
import time
from redis import Redis
import asyncio
import logging
import traceback

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Celery with settings
celery_app = Celery(
    "multi_agent_system",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Configure Celery settings
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=50
)

# Configure Redis with connection retry
def create_redis_client():
    """Create Redis client with retry logic"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            client = Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB + 1,  # Use different DB than rate limiter
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            # Test connection
            client.ping()
            logger.info(f"Redis connected successfully on attempt {attempt + 1}")
            return client
        except Exception as e:
            logger.error(f"Redis connection attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff

redis_client = create_redis_client()

@celery_app.task(bind=True)
def process_query_task(self, task_id: str, input_text: str, tier: str = "free"):
    """Process a query through the multi-agent workflow"""
    logger.info(f"Starting task {task_id} for tier {tier}")
    
    try:
        # Initial status update
        update_task_status(task_id, "processing", {
            "stage": "initializing",
            "started_at": time.time()
        })
        
        # Set priority based on tier
        priority_map = {"premium": 9, "basic": 5, "free": 1}
        self.request.delivery_info['priority'] = priority_map.get(tier, 1)
        
        # Validate input
        if not input_text or not input_text.strip():
            raise ValueError("Input text cannot be empty")
        
        logger.info(f"Processing query for task {task_id}: {input_text[:100]}...")
        
        # Get agent service
        update_task_status(task_id, "processing", {"stage": "loading_agents"})
        
        try:
            agent_service = get_agent_service()
            logger.info(f"Agent service loaded for task {task_id}")
        except Exception as e:
            logger.error(f"Failed to load agent service: {e}")
            raise Exception(f"Failed to initialize AI agents: {str(e)}")
        
        # Create event loop for async operations
        loop = None
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            update_task_status(task_id, "processing", {"stage": "processing_workflow"})
            
            # Run async workflow in sync context
            logger.info(f"Starting workflow for task {task_id}")
            result = loop.run_until_complete(
                agent_service.workflow.ainvoke({"input": input_text})
            )
            
            logger.info(f"Workflow completed for task {task_id}")
            
            # Extract output
            output = result.get("final_output")
            if not output:
                # Try alternative output fields
                output = (result.get("draft") or 
                         result.get("research_result") or 
                         "Processing completed but no output was generated")
            
            logger.info(f"Task {task_id} completed successfully")
            
            # Final status update
            update_task_status(task_id, "completed", {
                "output": output,
                "research_result": result.get("research_result", ""),
                "completed_at": time.time(),
                "processing_time": time.time() - result.get("started_at", time.time())
            })
            
            return {
                "status": "completed", 
                "task_id": task_id, 
                "output": output
            }
            
        except asyncio.TimeoutError:
            logger.error(f"Task {task_id} timed out")
            raise Exception("Task processing timed out")
        except Exception as e:
            logger.error(f"Workflow error for task {task_id}: {e}")
            logger.error(f"Workflow traceback: {traceback.format_exc()}")
            raise Exception(f"Workflow processing failed: {str(e)}")
        finally:
            if loop:
                try:
                    loop.close()
                except Exception as e:
                    logger.error(f"Error closing event loop: {e}")
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Task {task_id} failed: {error_msg}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # Update task status with error
        update_task_status(task_id, "failed", {
            "error": error_msg,
            "failed_at": time.time(),
            "traceback": traceback.format_exc()[:1000]  # Limit traceback size
        })
        
        # Re-raise for Celery
        raise self.retry(exc=e, countdown=60, max_retries=2) if self.request.retries < 2 else e

def update_task_status(task_id: str, status: str, data: dict = None):
    """Update task status in Redis with retry logic"""
    max_retries = 3
    task_info = {"status": status, "updated_at": time.time()}
    if data:
        task_info.update(data)
    
    for attempt in range(max_retries):
        try:
            redis_client.set(
                f"task:{task_id}", 
                json.dumps(task_info), 
                ex=86400  # 24 hour expiration
            )
            logger.debug(f"Task {task_id} status updated to {status}")
            return
        except Exception as e:
            logger.error(f"Failed to update task status (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                logger.error(f"Failed to update status for task {task_id} after {max_retries} attempts")
            else:
                time.sleep(0.5 * (attempt + 1))  # Brief backoff

def get_task_status(task_id: str):
    """Get task status from Redis with retry logic"""
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            task_data = redis_client.get(f"task:{task_id}")
            if task_data:
                return json.loads(task_data)
            else:
                logger.debug(f"No data found for task {task_id}")
                return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode task data for {task_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Redis error getting task {task_id} (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                logger.error(f"Failed to get task {task_id} after {max_retries} attempts")
                return None
            time.sleep(0.5 * (attempt + 1))

# Celery signal handlers for better monitoring
@celery_app.task(bind=True)
def test_task(self):
    """Test task to verify Celery is working"""
    logger.info("Test task executed successfully")
    return {"status": "success", "message": "Celery is working"}

# Health check for Celery workers
@celery_app.task
def health_check():
    """Health check task"""
    try:
        # Test Redis connection
        redis_client.ping()
        
        # Test agent service
        agent_service = get_agent_service()
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "redis": "connected",
            "agents": "loaded"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }

# Celery event handlers for better monitoring
from celery.signals import task_prerun, task_postrun, task_failure, task_retry

@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    """Handle task prerun"""
    logger.info(f"Task {task_id} starting: {task.name}")

@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kwds):
    """Handle task postrun"""
    logger.info(f"Task {task_id} completed with state: {state}")

@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwds):
    """Handle task failure"""
    logger.error(f"Task {task_id} failed: {exception}")

@task_retry.connect
def task_retry_handler(sender=None, task_id=None, reason=None, einfo=None, **kwds):
    """Handle task retry"""
    logger.warning(f"Task {task_id} retrying: {reason}")

# Utility function to check if workers are available
def check_workers():
    """Check if Celery workers are available"""
    try:
        inspect = celery_app.control.inspect()
        active = inspect.active()
        return bool(active)
    except Exception as e:
        logger.error(f"Failed to check workers: {e}")
        return False

# Initialize on worker startup
@celery_app.task(bind=True)
def worker_startup_check(self):
    """Check worker health on startup"""
    try:
        logger.info("Worker startup check initiated")
        
        # Test Redis connection
        redis_client.ping()
        logger.info("Redis connection: OK")
        
        # Test agent service initialization
        agent_service = get_agent_service()
        logger.info("Agent service: OK")
        
        return {
            "status": "worker_ready",
            "timestamp": time.time(),
            "worker_id": self.request.id
        }
    except Exception as e:
        logger.error(f"Worker startup check failed: {e}")
        raise

if __name__ == "__main__":
    # Start worker with proper logging
    logger.info("Starting Celery worker...")
    celery_app.start()