from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class QueryResponse(BaseModel):
    status: str
    task_id: Optional[str] = None
    message: Optional[str] = None
    output: Optional[str] = None

class TaskStatusResponse(BaseModel):
    status: str
    task_id: str
    output: Optional[str] = None
    error: Optional[str] = None
    updated_at: Optional[float] = None

class SearchResponse(BaseModel):
    status: str
    documents: List[Dict[str, Any]]
    count: int

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: float