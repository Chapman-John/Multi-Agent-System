from langchain_core.tools import BaseTool
from typing import Optional, Type
import asyncio

class WebSearchTool(BaseTool):
    """
    Custom web search tool for research agent
    """
    name = "web_search"
    description = "Perform a web search and retrieve relevant information"
    
    def __init__(self, search_service=None):
        super().__init__()
        self.search_service = search_service or self._default_search
    
    async def _default_search(self, query: str) -> str:
        """
        Default search implementation (can be replaced with actual search API)
        
        Args:
            query (str): Search query
        
        Returns:
            str: Search results
        """
        # Simulate search - replace with actual search API
        return f"Simulated search results for: {query}"
    
    async def _arun(self, query: str) -> str:
        """
        Async run method for web search
        
        Args:
            query (str): Search query
        
        Returns:
            str: Search results
        """
        return await self.search_service(query)
    
    def _run(self, query: str) -> str:
        """
        Sync run method (falls back to async)
        
        Args:
            query (str): Search query
        
        Returns:
            str: Search results
        """
        return asyncio.run(self._arun(query))

def create_tool(
    tool_class: Type[BaseTool], 
    *args, 
    **kwargs
) -> BaseTool:
    """
    Factory method to create tools with flexible configuration
    
    Args:
        tool_class (Type[BaseTool]): Tool class to instantiate
        *args: Positional arguments for tool initialization
        **kwargs: Keyword arguments for tool initialization
    
    Returns:
        BaseTool: Instantiated tool
    """
    return tool_class(*args, **kwargs)