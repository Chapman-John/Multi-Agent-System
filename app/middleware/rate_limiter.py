from flask import request, jsonify
import redis
import time
from functools import wraps

# Redis connection for storing rate limit data
redis_client = redis.Redis(host='localhost', port=6379, db=0)

def rate_limit(requests_per_minute=60, tier='free'):
    def decorator(f):
        @wraps(f)
        def wrapped_function(*args, **kwargs):
            # Get client identifier (API key or user ID)
            api_key = request.headers.get('X-API-Key', 'anonymous')
            
            # Create Redis keys for this user
            minute_key = f'rate_limit:{api_key}:{int(time.time()) // 60}'
            daily_key = f'daily_quota:{api_key}:{int(time.time()) // 86400}'
            
            # Get current usage counts
            minute_count = redis_client.incr(minute_key)
            # Set expiration if new key
            if minute_count == 1:
                redis_client.expire(minute_key, 60)
                
            daily_count = redis_client.incr(daily_key)
            if daily_count == 1:
                redis_client.expire(daily_key, 86400)  # 24 hours
            
            # Define tier limits
            tier_limits = {
                'free': {'per_minute': 10, 'per_day': 100},
                'basic': {'per_minute': 30, 'per_day': 1000},
                'premium': {'per_minute': 100, 'per_day': 10000}
            }
            
            # Check rate limits
            if minute_count > tier_limits[tier]['per_minute']:
                return jsonify({
                    "status": "error",
                    "message": "Rate limit exceeded. Try again later."
                }), 429
                
            if daily_count > tier_limits[tier]['per_day']:
                return jsonify({
                    "status": "error",
                    "message": "Daily quota exceeded."
                }), 429
                
            # If within limits, process the request
            return f(*args, **kwargs)
        return wrapped_function
    return decorator