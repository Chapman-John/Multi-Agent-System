from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import redis
import time
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional

# Redis connection for storing rate limit data
redis_client = redis.Redis(host='localhost', port=6379, db=0)

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Only apply rate limiting to API endpoints
        if request.url.path.startswith('/api/'):
            # Get API key from headers
            api_key = request.headers.get('X-API-Key', 'anonymous')
            
            # Determine tier
            tier = determine_tier(api_key)
            
            # Check rate limits
            if not check_rate_limit(api_key, tier):
                return JSONResponse(
                    status_code=429,
                    content={
                        "status": "error",
                        "message": "Rate limit exceeded. Try again later."
                    }
                )
        
        response = await call_next(request)
        return response

def determine_tier(api_key: str) -> str:
    """Determine tier based on API key"""
    if not api_key or api_key == 'anonymous':
        return 'free'
    
    if api_key.startswith('premium_'):
        return 'premium'
    elif api_key.startswith('basic_'):
        return 'basic'
    else:
        return 'free'

def check_rate_limit(api_key: str, tier: str) -> bool:
    """Check if request is within rate limits"""
    # Create Redis keys
    minute_key = f'rate_limit:{api_key}:{int(time.time()) // 60}'
    daily_key = f'daily_quota:{api_key}:{int(time.time()) // 86400}'
    
    # Get current usage counts
    minute_count = redis_client.incr(minute_key)
    if minute_count == 1:
        redis_client.expire(minute_key, 60)
        
    daily_count = redis_client.incr(daily_key)
    if daily_count == 1:
        redis_client.expire(daily_key, 86400)
    
    # Define tier limits
    tier_limits = {
        'free': {'per_minute': 10, 'per_day': 100},
        'basic': {'per_minute': 30, 'per_day': 1000},
        'premium': {'per_minute': 100, 'per_day': 10000}
    }
    
    # Check limits
    limits = tier_limits[tier]
    return (minute_count <= limits['per_minute'] and 
            daily_count <= limits['per_day'])

def verify_rate_limit_fastapi(api_key: Optional[str] = None) -> str:
    """Verify rate limit for FastAPI endpoints"""
    if not api_key:
        return 'free'
    
    tier = determine_tier(api_key)
    
    if not check_rate_limit(api_key, tier):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Try again later."
        )
    
    return tier
