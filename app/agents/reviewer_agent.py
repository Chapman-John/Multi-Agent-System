from app.agents.base_agent import BaseAgent
from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import BaseTool
from typing import Dict, Any, List

class ReviewerAgent(BaseAgent):
    def __init__(self, 
                 name: str, 
                 llm: BaseLanguageModel, 
                 tools: list[BaseTool] = None):
        super().__init__(name, llm, tools)
        
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Review the draft and provide feedback
        
        Args:
            state (Dict): Current workflow state
        
        Returns:
            Dict: Updated state with review feedback
        """
        # Extract draft from state
        draft = state.get('draft', '')
        input_query = state.get('input', '')
        
        # Generate review prompt
        review_prompt = f"""
        Review the following draft for the query: {input_query}
        
        Draft Content:
        {draft}
        
        Review Criteria:
        1. Accuracy of information
        2. Clarity and coherence
        3. Completeness
        4. Adherence to the original query
        5. Suggestions for improvement
        
        Please provide specific, constructive feedback.
        """
        
        # Generate review using LLM
        review_feedback = await self._call_llm(review_prompt)
        
        # Determine if revisions are needed
        revision_needed = await self._determine_revision_needed(review_feedback)
        
        # Update and return state
        return {
            **state,
            'review_feedback': [review_feedback] if revision_needed else [],
            'final_output': draft if not revision_needed else None
        }
    
    async def _determine_revision_needed(self, feedback: str) -> bool:
        """
        Determine if the draft requires significant revisions
        
        Args:
            feedback (str): Review feedback
        
        Returns:
            bool: Whether revision is needed
        """
        revision_prompt = f"""
        Assess the following review feedback and determine if significant revisions are needed:
        
        Feedback: {feedback}
        
        Respond with REVISION_NEEDED or NO_REVISION based on the severity of feedback.
        """
        
        response = await self._call_llm(revision_prompt)
        return "REVISION_NEEDED" in response