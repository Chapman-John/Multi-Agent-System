from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import redis
import time
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
from app.config import settings

# Use settings for Redis connection
redis_client = redis.Redis(
    host=settings.REDIS_HOST, 
    port=settings.REDIS_PORT, 
    db=settings.REDIS_DB
)

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith('/api/'):
            api_key = request.headers.get('X-API-Key', 'anonymous')
            tier = determine_tier(api_key)
            
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
    minute_key = f'rate_limit:{api_key}:{int(time.time()) // 60}'
    daily_key = f'daily_quota:{api_key}:{int(time.time()) // 86400}'
    
    minute_count = redis_client.incr(minute_key)
    if minute_count == 1:
        redis_client.expire(minute_key, 60)
        
    daily_count = redis_client.incr(daily_key)
    if daily_count == 1:
        redis_client.expire(daily_key, 86400)
    
    # Use settings for tier limits
    limits = settings.RATE_LIMIT_TIERS[tier]
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