import pytest
from app.agents.researcher_agent import ResearcherAgent
from app.agents.writer_agent import WriterAgent
from app.agents.reviewer_agent import ReviewerAgent

class TestAgents:
    @pytest.mark.asyncio
    async def test_researcher_agent(self, mocker):
        """
        Test researcher agent processing
        """
        # Mock LLM and tools
        mock_llm = mocker.Mock()
        mock_llm.apredict = mocker.AsyncMock(return_value="Research summary")
        
        researcher = ResearcherAgent(
            name="Test Researcher", 
            llm=mock_llm
        )
        
        state = {"input": "Test query"}
        result = await researcher.process(state)
        
        assert "research_result" in result
        assert result["research_result"] == "Research summary"

    @pytest.mark.asyncio
    async def test_writer_agent(self, mocker):
        """
        Test writer agent processing
        """
        mock_llm = mocker.Mock()
        mock_llm.apredict = mocker.AsyncMock(return_value="Draft content")
        
        writer = WriterAgent(
            name="Test Writer", 
            llm=mock_llm
        )
        
        state = {
            "input": "Test query", 
            "research_result": "Research summary"
        }
        result = await writer.process(state)
        
        assert "draft" in result
        assert result["draft"] == "Draft content"

    @pytest.mark.asyncio
    async def test_reviewer_agent(self, mocker):
        """
        Test reviewer agent processing
        """
        mock_llm = mocker.Mock()
        mock_llm.apredict = mocker.AsyncMock(return_value="Revision needed")
        
        reviewer = ReviewerAgent(
            name="Test Reviewer", 
            llm=mock_llm
        )
        
        state = {
            "input": "Test query", 
            "draft": "Initial draft"
        }
        result = await reviewer.process(state)
        
        assert "review_feedback" in result