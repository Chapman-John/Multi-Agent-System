from pydantic import BaseModel
from typing import Optional

class QueryRequest(BaseModel):
    input: str
    
class SearchRequest(BaseModel):
    query: str

class TaskRequest(BaseModel):
    task_id: str