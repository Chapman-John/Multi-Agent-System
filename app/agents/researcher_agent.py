from app.agents.base_agent import BaseAgent
from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import BaseTool
from typing import Dict, Any

class ResearcherAgent(BaseAgent):
    def __init__(self, 
                 name: str, 
                 llm: BaseLanguageModel, 
                 tools: list[BaseTool] = None):
        super().__init__(name, llm, tools)
        
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Conduct research based on the input query
        
        Args:
            state (Dict): Current workflow state
        
        Returns:
            Dict: Updated state with research results
        """
        # Extract input from state
        input_query = state.get('input', '')
        
        # Perform research using available tools
        research_results = []
        
        # Use search tools to gather information
        for tool in self.tools:
            try:
                result = await tool.arun(input_query)
                research_results.append(result)
            except Exception as e:
                print(f"Research tool {tool.name} failed: {e}")
        
        # Use LLM to synthesize research results
        synthesis_prompt = f"""
        Synthesize the following research results for the query: {input_query}
        
        Research Sources:
        {chr(10).join(research_results)}
        
        Provide a comprehensive and concise summary of the key findings.
        """
        
        synthesized_research = await self._call_llm(synthesis_prompt)
        
        # Update and return state
        return {
            **state,
            'research_result': synthesized_research
        }