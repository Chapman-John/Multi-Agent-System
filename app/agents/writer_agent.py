from app.agents.base_agent import BaseAgent
from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import BaseTool
from typing import Dict, Any

class WriterAgent(BaseAgent):
    def __init__(self, 
                 name: str, 
                 llm: BaseLanguageModel, 
                 tools: list[BaseTool] = None,
                 writing_style: str = 'professional'):
        super().__init__(name, llm, tools)
        self.writing_style = writing_style
        
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a draft based on research results
        
        Args:
            state (Dict): Current workflow state
        
        Returns:
            Dict: Updated state with draft content
        """
        # Extract research from state
        research_result = state.get('research_result', '')
        input_query = state.get('input', '')
        
        # Generate draft using LLM
        draft_prompt = f"""
        Writing Style: {self.writing_style}
        Input Query: {input_query}
        Research Summary: {research_result}
        
        Tasks:
        1. Create a well-structured draft
        2. Ensure clarity and coherence
        3. Incorporate key findings from research
        4. Maintain the specified writing style
        
        Draft:
        """
        
        draft = await self._call_llm(draft_prompt)
        
        # Update and return state
        return {
            **state,
            'draft': draft
        }