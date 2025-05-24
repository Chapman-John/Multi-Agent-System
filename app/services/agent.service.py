from app.config import create_agents
from app.graph.multi_agent_workflow import create_multi_agent_graph
from typing import Dict, Any

class AgentService:
    def __init__(self):
        self.rag_agent, self.researcher, self.writer, self.reviewer = create_agents()
        self.workflow = create_multi_agent_graph(
            self.rag_agent, self.researcher, self.writer, self.reviewer
        )
    
    async def process_query(self, input_text: str) -> Dict[str, Any]:
        """Process a query through the multi-agent workflow"""
        result = await self.workflow.ainvoke({"input": input_text})
        return result
    
    async def search_documents(self, query: str):
        """Search documents using RAG agent"""
        return await self.rag_agent.retrieve_documents(query)

# Global service instance
agent_service = AgentService()