import pytest
from unittest.mock import Mock, AsyncMock
from app.graph.multi_agent_workflow import create_multi_agent_graph, AgentState
from app.agents.rag_agent import RAGAgent
from app.agents.researcher_agent import ResearcherAgent
from app.agents.writer_agent import WriterAgent
from app.agents.reviewer_agent import ReviewerAgent

class TestWorkflow:
    @pytest.fixture
    def mock_agents(self):
        """Create mock agents for testing"""
        # Mock LLM
        mock_llm = Mock()
        mock_llm.ainvoke = AsyncMock()
        mock_response = Mock()
        mock_response.content = "Mock response"
        mock_llm.ainvoke.return_value = mock_response
        
        # Create agents with mocked LLM
        rag_agent = RAGAgent("RAG", mock_llm, search_tool=None)
        researcher = ResearcherAgent("Researcher", mock_llm)
        writer = WriterAgent("Writer", mock_llm)
        reviewer = ReviewerAgent("Reviewer", mock_llm)
        
        return rag_agent, researcher, writer, reviewer
    
    @pytest.mark.asyncio
    async def test_workflow_creation(self, mock_agents):
        """Test that workflow can be created successfully"""
        rag_agent, researcher, writer, reviewer = mock_agents
        
        workflow = create_multi_agent_graph(rag_agent, researcher, writer, reviewer)
        
        assert workflow is not None
        # Test that we can get the graph structure
        assert hasattr(workflow, 'invoke')
    
    @pytest.mark.asyncio
    async def test_complete_workflow_execution(self, mock_agents):
        """Test complete workflow execution"""
        rag_agent, researcher, writer, reviewer = mock_agents
        
        # Mock the LLM to return specific responses for each agent
        def mock_llm_response(messages):
            content = messages[0].content
            if "Research" in content or "research" in content:
                return Mock(content="Research findings on the topic")
            elif "Draft" in content or "Writing" in content:
                return Mock(content="Well-structured draft response")
            elif "Review" in content:
                return Mock(content="Good quality draft")
            elif "NO_REVISION" in content:
                return Mock(content="NO_REVISION")
            else:
                return Mock(content="Default response")
        
        # Apply the mock to all agents
        for agent in [rag_agent, researcher, writer, reviewer]:
            agent.llm.ainvoke = AsyncMock(side_effect=mock_llm_response)
        
        workflow = create_multi_agent_graph(rag_agent, researcher, writer, reviewer)
        
        # Test workflow execution
        initial_state = {"input": "Explain artificial intelligence"}
        result = await workflow.ainvoke(initial_state)
        
        # Verify the workflow completed successfully
        assert "final_output" in result
        assert result["input"] == "Explain artificial intelligence"
        assert "research_result" in result
        assert "draft" in result
    
    def test_agent_state_structure(self):
        """Test AgentState TypedDict structure"""
        # This is more of a structural test
        state: AgentState = {
            "input": "test",
            "rag_documents": None,
            "rag_enhanced_query": None,
            "research_result": None,
            "draft": None,
            "review_feedback": None,
            "final_output": None
        }
        
        assert state["input"] == "test"
        assert state["rag_documents"] is None