from app.agents.base_agent import BaseAgent
from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import BaseTool
from langchain_core.documents import Document
from typing import Dict, Any, List
from app.utils.mcp import create_mcp_prompt_with_rag

class RAGAgent(BaseAgent):
    def __init__(self, 
                 name: str, 
                 llm: BaseLanguageModel, 
                 search_tool = None,
                 tools: list[BaseTool] = None):
        super().__init__(name, llm, tools)
        self.search_tool = search_tool
        
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieve relevant documents and enhance the query with RAG
        
        Args:
            state (Dict): Current workflow state
        
        Returns:
            Dict: Updated state with RAG context
        """
        # Extract input from state
        input_query = state.get('input', '')
        
        # Skip if no search tool is available
        if not self.search_tool:
            return {
                **state,
                'rag_documents': [],
                'rag_enhanced_query': input_query
            }
        
        # Perform hybrid search to get relevant documents
        documents = await self.search_tool.hybrid_search(input_query)
        
        # Create enhanced query with document context
        rag_prompt = create_mcp_prompt_with_rag(input_query, documents)
        
        # Update state with RAG information
        return {
            **state,
            'rag_documents': documents,
            'rag_enhanced_query': rag_prompt
        }
    
    async def retrieve_documents(self, query: str) -> List[Document]:
        """
        Retrieve documents for a specific query
        
        Args:
            query (str): Query to search for
            
        Returns:
            List[Document]: Retrieved documents
        """
        if not self.search_tool:
            return []
            
        return await self.search_tool.hybrid_search(query)