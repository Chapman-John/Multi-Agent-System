import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from app.main import app

class TestAPI:
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_read_root(self, client):
        """Test the root endpoint returns HTML"""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Multi-Agent AI System" in response.text
    
    @patch('worker.celery_app.process_query_task')
    def test_process_query_endpoint(self, mock_task, client):
        """Test the process query endpoint"""
        # Mock the Celery task
        mock_task.delay.return_value = Mock(id="test-task-id")
        
        response = client.post(
            "/api/process",
            json={"input": "Test query"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"
        assert "task_id" in data
        assert data["message"] == "Query processing started"
    
    def test_process_query_validation(self, client):
        """Test query validation"""
        response = client.post(
            "/api/process",
            json={}  # Missing 'input' field
        )
        
        assert response.status_code == 422  # Validation error
    
    @patch('worker.celery_app.get_task_status')
    def test_get_task_status(self, mock_get_status, client):
        """Test task status endpoint"""
        mock_get_status.return_value = {
            "status": "completed",
            "output": "Test output",
            "updated_at": 1234567890
        }
        
        response = client.get("/api/task/test-task-id")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["output"] == "Test output"
        assert data["task_id"] == "test-task-id"
    
    def test_get_nonexistent_task(self, client):
        """Test getting status for non-existent task"""
        with patch('worker.celery_app.get_task_status', return_value=None):
            response = client.get("/api/task/nonexistent")
            assert response.status_code == 404