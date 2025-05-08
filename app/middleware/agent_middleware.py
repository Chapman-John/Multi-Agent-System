from functools import wraps
import asyncio
from typing import Callable, Any, Dict

def with_retry(max_retries=3, backoff_factor=2):
    """
    Decorator for agent processing functions to implement retry logic
    """
    def decorator(func):
        @wraps(func)
        async def wrapped_function(self, state, *args, **kwargs):
            retries = 0
            last_exception = None
            
            while retries < max_retries:
                try:
                    return await func(self, state, *args, **kwargs)
                except Exception as e:
                    retries += 1
                    last_exception = e
                    if retries < max_retries:
                        # Exponential backoff
                        wait_time = backoff_factor ** retries
                        print(f"Retrying {func.__name__} in {wait_time}s after error: {str(e)}")
                        await asyncio.sleep(wait_time)
            
            # Handle the failure after max retries
            print(f"Failed after {max_retries} retries: {str(last_exception)}")
            # Return a graceful fallback state
            return {
                **state,
                "error": str(last_exception),
                "status": "fallback"
            }
            
        return wrapped_function
    return decorator