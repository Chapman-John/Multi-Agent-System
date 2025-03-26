from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Optional
from app.agents.researcher_agent import ResearcherAgent
from app.agents.writer_agent import WriterAgent
from app.agents.reviewer_agent import ReviewerAgent

class AgentState(TypedDict):
    """
    Shared state between agents in the workflow
    """
    input: str
    research_result: Optional[str]
    draft: Optional[str]
    review_feedback: Optional[List[str]]
    final_output: Optional[str]

def create_multi_agent_graph(
    researcher: ResearcherAgent, 
    writer: WriterAgent, 
    reviewer: ReviewerAgent
):
    """
    Create a multi-agent workflow using LangGraph
    
    Args:
        researcher (ResearcherAgent): Agent responsible for research
        writer (WriterAgent): Agent responsible for writing
        reviewer (ReviewerAgent): Agent responsible for reviewing
    
    Returns:
        StateGraph: Configured multi-agent workflow
    """
    workflow = StateGraph(AgentState)

    # Add nodes for each agent
    workflow.add_node("researcher", researcher.process)
    workflow.add_node("writer", writer.process)
    workflow.add_node("reviewer", reviewer.process)

    # Define workflow edges
    workflow.set_entry_point("researcher")
    workflow.add_edge("researcher", "writer")
    workflow.add_edge("writer", "reviewer")
    
    # Conditional edge for review process
    def review_router(state: AgentState):
        if state.get("review_feedback"):
            return "writer"  # Revise if feedback exists
        return END  # Finish if no feedback

    workflow.add_conditional_edges("reviewer", review_router)

    # Compile the graph
    return workflow.compile()