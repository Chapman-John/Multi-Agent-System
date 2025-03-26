from typing import Any, Dict
from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import BaseTool

class BaseAgent:
    def __init__(self, 
                 name: str, 
                 llm: BaseLanguageModel, 
                 tools: list[BaseTool] = None):
        self.name = name
        self.llm = llm
        self.tools = tools or []

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Base processing method for agents
        
        Args:
            input_data (Dict): Input data for agent processing
        
        Returns:
            Dict: Processed output
        """
        raise NotImplementedError("Subclasses must implement processing method")

    def add_tool(self, tool: BaseTool):
        """
        Add a tool to the agent's toolset
        
        Args:
            tool (BaseTool): Tool to be added
        """
        self.tools.append(tool)