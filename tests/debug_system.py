"""
Debug script to diagnose multi-agent system issues
Run this script to check all system components
"""

import os
import sys
import json
import time
import asyncio
import traceback
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_environment():
    """Check environment variables and configuration"""
    print("🔍 Checking Environment Configuration...")
    
    required_vars = [
        'OPENAI_API_KEY',
        'ANTHROPIC_API_KEY',
        'REDIS_HOST',
        'REDIS_PORT'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            # Mask API keys for security
            if 'API_KEY' in var:
                print(f"  ✅ {var}: {'*' * len(value)}")
            else:
                print(f"  ✅ {var}: {value}")
    
    if missing_vars:
        print(f"  ❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    return True

def check_redis():
    """Check Redis connection"""
    print("\n📡 Checking Redis Connection...")
    
    try:
        from app.config import settings
        import redis
        
        client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB
        )
        
        # Test connection
        client.ping()
        print(f"  ✅ Redis connected at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        
        # Test basic operations
        client.set("test_key", "test_value", ex=10)
        value = client.get("test_key")
        if value == b"test_value":
            print("  ✅ Redis read/write operations working")
        
        # Check memory usage
        info = client.info('memory')
        memory_mb = info['used_memory'] / (1024 * 1024)
        print(f"  ℹ️  Redis memory usage: {memory_mb:.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Redis connection failed: {e}")
        print(f"     Make sure Redis is running: docker-compose up redis")
        return False

def check_celery():
    """Check Celery worker status"""
    print("\n⚡ Checking Celery Workers...")
    
    try:
        from worker.celery_app import celery_app, redis_client
        
        # Check broker connection
        try:
            redis_client.ping()
            print("  ✅ Celery broker (Redis) connected")
        except Exception as e:
            print(f"  ❌ Celery broker connection failed: {e}")
            return False
        
        # Check active workers
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        
        if active_workers:
            print(f"  ✅ Active workers found: {list(active_workers.keys())}")
            
            # Check worker stats
            stats = inspect.stats()
            for worker, stat in stats.items():
                print(f"    📊 {worker}: {stat.get('total', 'N/A')} total tasks")
        else:
            print("  ⚠️  No active workers found")
            print("     Start workers with: docker-compose up worker")
            return False
            
        # Test task submission
        print("  🧪 Testing task submission...")
        from worker.celery_app import test_task
        
        result = test_task.delay()
        task_result = result.get(timeout=10)
        
        if task_result and task_result.get('status') == 'success':
            print("  ✅ Test task executed successfully")
        else:
            print(f"  ⚠️  Test task returned: {task_result}")
            
        return True
        
    except Exception as e:
        print(f"  ❌ Celery check failed: {e}")
        print(f"     Traceback: {traceback.format_exc()}")
        return False

def check_agents():
    """Check agent initialization"""
    print("\n🤖 Checking AI Agents...")
    
    try:
        from app.config import create_agents
        
        print("  🔄 Initializing agents...")
        rag_agent, researcher, writer, reviewer = create_agents()
        
        print(f"  ✅ RAG Agent: {rag_agent.name}")
        print(f"  ✅ Researcher Agent: {researcher.name}")
        print(f"  ✅ Writer Agent: {writer.name}")
        print(f"  ✅ Reviewer Agent: {reviewer.name}")
        
        # Test a simple LLM call
        print("  🧪 Testing LLM connectivity...")
        
        try:
            # Test with a simple prompt
            test_result = asyncio.run(
                researcher._call_llm("Say 'Hello' if you can hear me.")
            )
            if "hello" in test_result.lower():
                print("  ✅ LLM connectivity test passed")
            else:
                print(f"  ⚠️  LLM response: {test_result[:100]}...")
        except Exception as e:
            print(f"  ❌ LLM test failed: {e}")
            
        return True
        
    except Exception as e:
        print(f"  ❌ Agent initialization failed: {e}")
        print(f"     Traceback: {traceback.format_exc()}")
        return False

def check_workflow():
    """Check full workflow"""
    print("\n🔄 Checking Complete Workflow...")
    
    try:
        from app.services.agent_service import get_agent_service
        
        agent_service = get_agent_service()
        print("  ✅ Agent service initialized")
        
        # Test with a simple query
        test_query = "What is 2+2?"
        print(f"  🧪 Testing workflow with query: '{test_query}'")
        
        result = asyncio.run(
            agent_service.process_query(test_query)
        )
        
        if result.get("final_output"):
            print("  ✅ Workflow completed successfully")
            print(f"     Output preview: {result['final_output'][:100]}...")
        else:
            print("  ⚠️  Workflow completed but no final output")
            print(f"     Result keys: {list(result.keys())}")
            
        return True
        
    except Exception as e:
        print(f"  ❌ Workflow test failed: {e}")
        print(f"     Traceback: {traceback.format_exc()}")
        return False

def check_api_endpoints():
    """Check API endpoints"""
    print("\n🌐 Checking API Endpoints...")
    
    try:
        import requests
        import time
        
        base_url = "http://localhost:8000"  # Default Docker port
        
        # Test health endpoint
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                print("  ✅ Health endpoint responding")
            else:
                print(f"  ⚠️  Health endpoint returned {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("  ❌ Cannot connect to API server")
            print("     Make sure the app is running: docker-compose up app")
            return False
        
        # Test debug endpoint
        try:
            response = requests.get(f"{base_url}/api/debug", timeout=5)
            if response.status_code == 200:
                debug_data = response.json()
                print("  ✅ Debug endpoint responding")
                print(f"     Redis status: {debug_data.get('redis_status', 'unknown')}")
                print(f"     Celery status: {debug_data.get('celery_status', 'unknown')}")
            else:
                print(f"  ⚠️  Debug endpoint returned {response.status_code}")
        except Exception as e:
            print(f"  ⚠️  Debug endpoint error: {e}")
        
        # Test process endpoint
        try:
            response = requests.post(
                f"{base_url}/api/process",
                json={"input": "Hello world test"},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                task_id = data.get('task_id')
                print("  ✅ Process endpoint responding")
                print(f"     Task ID: {task_id}")
                
                # Test task status endpoint
                if task_id:
                    time.sleep(2)  # Give task time to start
                    status_response = requests.get(f"{base_url}/api/task/{task_id}")
                    if status_response.status_code == 200:
                        print("  ✅ Task status endpoint responding")
                    elif status_response.status_code == 404:
                        print("  ❌ Task not found (this is the main issue!)")
                        print("     This indicates tasks are not being stored properly")
                    else:
                        print(f"  ⚠️  Task status returned {status_response.status_code}")
                        
            else:
                print(f"  ❌ Process endpoint returned {response.status_code}")
                print(f"     Response: {response.text}")
                
        except Exception as e:
            print(f"  ❌ Process endpoint error: {e}")
            
        return True
        
    except Exception as e:
        print(f"  ❌ API check failed: {e}")
        return False

def main():
    """Run all diagnostic checks"""
    print("🔧 Multi-Agent System Diagnostics")
    print("=" * 50)
    
    checks = [
        ("Environment", check_environment),
        ("Redis", check_redis),
        ("Celery", check_celery),
        ("Agents", check_agents),
        ("Workflow", check_workflow),
        ("API", check_api_endpoints)
    ]
    
    results = {}
    
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            print(f"  ❌ {check_name} check crashed: {e}")
            results[check_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 50)
    
    passed = sum(results.values())
    total = len(results)
    
    for check_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{check_name:.<20} {status}")
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All systems operational!")
    else:
        print("\n🔧 TROUBLESHOOTING STEPS:")
        
        if not results.get("Environment"):
            print("1. Check your .env file has all required API keys")
            
        if not results.get("Redis"):
            print("2. Start Redis: docker-compose up redis")
            
        if not results.get("Celery"):
            print("3. Start Celery worker: docker-compose up worker")
            
        if not results.get("API"):
            print("4. Start API server: docker-compose up app")
            
        print("5. Check Docker logs: docker-compose logs")

if __name__ == "__main__":
    main()