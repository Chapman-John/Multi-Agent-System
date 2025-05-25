"""
End-to-end test script for the multi-agent system
"""

import requests
import time
import json

def test_system():
    """Test the complete system workflow"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Multi-Agent System End-to-End")
    print("=" * 50)
    
    # Test 1: Health check
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Health check passed")
            health_data = response.json()
            print(f"   📊 Redis status: {health_data.get('redis', 'unknown')}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        return False
    
    # Test 2: Debug info
    print("\n2. Testing debug endpoint...")
    try:
        response = requests.get(f"{base_url}/api/debug", timeout=5)
        if response.status_code == 200:
            debug_data = response.json()
            print("   ✅ Debug endpoint responding")
            print(f"   📊 Redis: {debug_data.get('redis_status')}")
            print(f"   📊 Celery: {debug_data.get('celery_status')}")
            print(f"   📊 Workers: {debug_data.get('celery_workers', [])}")
        else:
            print(f"   ⚠️ Debug endpoint returned {response.status_code}")
    except Exception as e:
        print(f"   ⚠️ Debug endpoint error: {e}")
    
    # Test 3: Simple query processing
    print("\n3. Testing query processing...")
    test_query = "What is the capital of France?"
    
    try:
        # Submit query
        response = requests.post(
            f"{base_url}/api/process",
            json={"input": test_query},
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"   ❌ Failed to submit query: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        data = response.json()
        task_id = data.get('task_id')
        
        if not task_id:
            print("   ❌ No task ID received")
            return False
        
        print(f"   ✅ Query submitted successfully")
        print(f"   📝 Task ID: {task_id}")
        
        # Poll for results
        print("   ⏳ Waiting for results...")
        max_attempts = 30  # 1 minute max
        attempt = 0
        
        while attempt < max_attempts:
            try:
                status_response = requests.get(f"{base_url}/api/task/{task_id}", timeout=5)
                
                if status_response.status_code == 404:
                    print(f"   ❌ Task not found (attempt {attempt + 1})")
                    if attempt == 0:
                        print("   🔍 This suggests the task wasn't stored properly")
                        # Try to check what's in Redis
                        return False
                elif status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data.get('status')
                    
                    print(f"   📊 Status: {status} (attempt {attempt + 1})")
                    
                    if status == 'completed':
                        output = status_data.get('output', 'No output')
                        print(f"   ✅ Task completed successfully!")
                        print(f"   📝 Output preview: {output[:100]}...")
                        return True
                    elif status == 'failed':
                        error = status_data.get('error', 'Unknown error')
                        print(f"   ❌ Task failed: {error}")
                        return False
                    elif status == 'processing':
                        print(f"   ⏳ Still processing... (attempt {attempt + 1})")
                    else:
                        print(f"   ⚠️ Unknown status: {status}")
                else:
                    print(f"   ⚠️ Unexpected status code: {status_response.status_code}")
                
            except Exception as e:
                print(f"   ⚠️ Error checking status: {e}")
            
            attempt += 1
            time.sleep(2)
        
        print("   ⏰ Task timed out")
        return False
        
    except Exception as e:
        print(f"   ❌ Query processing error: {e}")
        return False

def test_direct_components():
    """Test components directly"""
    print("\n" + "=" * 50)
    print("🔧 Testing Components Directly")
    print("=" * 50)
    
    # Test Redis
    print("1. Testing Redis directly...")
    try:
        import redis
        client = redis.Redis(host='localhost', port=6379, db=0)
        client.ping()
        
        # Test task storage format
        client.set('task:test', json.dumps({
            'status': 'test',
            'updated_at': time.time()
        }), ex=60)
        
        data = client.get('task:test')
        if data:
            parsed = json.loads(data)
            print("   ✅ Redis read/write working")
            print(f"   📊 Test data: {parsed}")
        
    except Exception as e:
        print(f"   ❌ Redis test failed: {e}")
    
    # Test Celery
    print("\n2. Testing Celery directly...")
    try:
        from worker.celery_app import celery_app, test_task
        
        # Check workers
        inspect = celery_app.control.inspect()
        active = inspect.active()
        
        if active:
            print(f"   ✅ Active workers: {list(active.keys())}")
            
            # Submit test task
            result = test_task.delay()
            task_result = result.get(timeout=10)
            print(f"   ✅ Test task result: {task_result}")
        else:
            print("   ❌ No active workers found")
            
    except Exception as e:
        print(f"   ❌ Celery test failed: {e}")

if __name__ == "__main__":
    success = test_system()
    
    if not success:
        print("\n🔧 Running direct component tests for debugging...")
        test_direct_components()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! System is working correctly.")
    else:
        print("❌ Tests failed. Check the logs above for details.")
        print("\n📋 Common fixes:")
        print("   • Restart services: docker-compose down && docker-compose up")
        print("   • Check logs: docker-compose logs")
        print("   • Run diagnostics: python debug_system.py")