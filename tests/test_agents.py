import pytest
from unittest.mock import AsyncMock, Mock
from app.agents.researcher_agent import ResearcherAgent
from app.agents.writer_agent import WriterAgent
from app.agents.reviewer_agent import ReviewerAgent
from app.agents.rag_agent import RAGAgent

class TestAgents:
    @pytest.mark.asyncio
    async def test_researcher_agent(self, mocker):
        """Test researcher agent processing"""
        # Mock LLM with correct method
        mock_llm = Mock()
        mock_llm.ainvoke = AsyncMock()
        mock_response = Mock()
        mock_response.content = "Research summary based on available sources"
        mock_llm.ainvoke.return_value = mock_response
        
        researcher = ResearcherAgent(
            name="Test Researcher", 
            llm=mock_llm
        )
        
        state = {"input": "Test query about AI"}
        result = await researcher.process(state)
        
        assert "research_result" in result
        assert "Research summary" in result["research_result"]
        assert mock_llm.ainvoke.called
    
    @pytest.mark.asyncio
    async def test_writer_agent(self, mocker):
        """Test writer agent processing"""
        mock_llm = Mock()
        mock_llm.ainvoke = AsyncMock()
        mock_response = Mock()
        mock_response.content = "Well-structured draft content based on research"
        mock_llm.ainvoke.return_value = mock_response
        
        writer = WriterAgent(
            name="Test Writer", 
            llm=mock_llm,
            writing_style="professional"
        )
        
        state = {
            "input": "Test query", 
            "research_result": "Research findings about the topic"
        }
        result = await writer.process(state)
        
        assert "draft" in result
        assert "draft content" in result["draft"]
        assert mock_llm.ainvoke.called

    @pytest.mark.asyncio
    async def test_reviewer_agent(self, mocker):
        """Test reviewer agent processing"""
        mock_llm = Mock()
        mock_llm.ainvoke = AsyncMock()
        
        # Mock both review and revision check calls
        mock_responses = [
            Mock(content="The draft looks good with minor suggestions"),
            Mock(content="NO_REVISION needed")
        ]
        mock_llm.ainvoke.side_effect = mock_responses
        
        reviewer = ReviewerAgent(
            name="Test Reviewer", 
            llm=mock_llm
        )
        
        state = {
            "input": "Test query", 
            "draft": "Initial draft content"
        }
        result = await reviewer.process(state)
        
        assert "review_feedback" in result
        assert "final_output" in result
        # Should have final output since no revision needed
        assert result["final_output"] == "Initial draft content"
        assert len(result["review_feedback"]) == 0

    @pytest.mark.asyncio
    async def test_rag_agent_without_search_tool(self):
        """Test RAG agent when no search tool is available"""
        mock_llm = Mock()
        
        rag_agent = RAGAgent(
            name="Test RAG", 
            llm=mock_llm,
            search_tool=None
        )
        
        state = {"input": "Test query"}
        result = await rag_agent.process(state)
        
        assert result["rag_documents"] == []
        assert result["rag_enhanced_query"] == "Test query"
        
    @pytest.mark.asyncio
    async def test_rag_agent_with_search_tool(self, mocker):
        """Test RAG agent with mock search tool"""
        mock_llm = Mock()
        mock_search_tool = Mock()
        mock_documents = [Mock(page_content="Test content", metadata={"source": "test"})]
        mock_search_tool.hybrid_search = AsyncMock(return_value=mock_documents)
        
        rag_agent = RAGAgent(
            name="Test RAG", 
            llm=mock_llm,
            search_tool=mock_search_tool
        )
        
        state = {"input": "Test query"}
        result = await rag_agent.process(state)
        
        assert "rag_documents" in result
        assert len(result["rag_documents"]) == 1
        assert "rag_enhanced_query" in result
        mock_search_tool.hybrid_search.assert_called_once_with("Test query")