from app.config import create_agents, settings
from app.graph.multi_agent_workflow import create_multi_agent_graph
from typing import Dict, Any, Optional
import asyncio
import logging

logger = logging.getLogger(__name__)

class AgentService:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            try:
                self.rag_agent, self.researcher, self.writer, self.reviewer = create_agents()
                self.workflow = create_multi_agent_graph(
                    self.rag_agent, self.researcher, self.writer, self.reviewer
                )
                self._initialized = True
                logger.info("AgentService initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize AgentService: {e}")
                raise
    
    async def process_query(self, input_text: str) -> Dict[str, Any]:
        """Process a query through the multi-agent workflow"""
        try:
            result = await self.workflow.ainvoke({"input": input_text})
            return result
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "final_output": f"Error processing query: {str(e)}",
                "error": str(e)
            }
    
    async def search_documents(self, query: str):
        """Search documents using RAG agent"""
        try:
            return await self.rag_agent.retrieve_documents(query)
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []

# Global service instance - singleton pattern
def get_agent_service() -> AgentService:
    return AgentService()

agent_service = get_agent_service()