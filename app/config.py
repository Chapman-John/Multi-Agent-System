from pydantic import BaseSettings
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # API Configuration
    APP_NAME: str = "Multi-Agent AI System"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # API Keys
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str
    TAVILY_API_KEY: Optional[str] = None
    
    # Database & Cache
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    VECTOR_DB_PATH: str = "./storage/vector_db"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # Rate Limiting
    RATE_LIMIT_TIERS: Dict[str, Dict[str, int]] = {
        'free': {'per_minute': 10, 'per_day': 100},
        'basic': {'per_minute': 30, 'per_day': 1000},
        'premium': {'per_minute': 100, 'per_day': 10000}
    }
    
    # Agent Configuration
    AGENT_CONFIGS: Dict[str, Dict[str, Any]] = {
        'rag': {
            'name': 'RAG Processor',
            'model': 'claude-3-sonnet-20240229',
            'temperature': 0.2
        },
        'researcher': {
            'name': 'Research Assistant',
            'model': 'claude-3-opus-20240229',
            'temperature': 0.7
        },
        'writer': {
            'name': 'Content Writer',
            'model': 'claude-3-opus-20240229',
            'temperature': 0.6,
            'writing_style': 'professional'
        },
        'reviewer': {
            'name': 'Content Reviewer',
            'model': 'claude-3-haiku-20240307',
            'temperature': 0.5
        }
    }
    
    # Feature Flags
    MCP_ENABLED: bool = True
    RAG_ENABLED: bool = True
    MAX_DOCUMENTS: int = 5

    class Config:
        env_file = ".env"

settings = Settings()

# Agent factory function
def create_agents():
    from langchain_openai import ChatOpenAI
    from langchain_anthropic import ChatAnthropicMessages
    from app.utils.tools import WebSearchTool, create_tool
    from app.utils.search_rag import SearchRAGTool
    from app.utils.mcp import create_mcp_llm
    from app.agents.researcher_agent import ResearcherAgent
    from app.agents.writer_agent import WriterAgent
    from app.agents.reviewer_agent import ReviewerAgent
    from app.agents.rag_agent import RAGAgent
    
    # Create search tool
    search_rag_tool = None
    if settings.RAG_ENABLED and settings.TAVILY_API_KEY:
        search_rag_tool = SearchRAGTool(
            tavily_api_key=settings.TAVILY_API_KEY,
            openai_api_key=settings.OPENAI_API_KEY,
            persist_dir=settings.VECTOR_DB_PATH
        )
    
    # Create LLMs based on configuration
    if settings.MCP_ENABLED and settings.ANTHROPIC_API_KEY:
        llms = {
            'rag': create_mcp_llm(settings.ANTHROPIC_API_KEY, 
                                settings.AGENT_CONFIGS['rag']['model'],
                                settings.AGENT_CONFIGS['rag']['temperature']),
            'researcher': create_mcp_llm(settings.ANTHROPIC_API_KEY,
                                       settings.AGENT_CONFIGS['researcher']['model'],
                                       settings.AGENT_CONFIGS['researcher']['temperature']),
            'writer': create_mcp_llm(settings.ANTHROPIC_API_KEY,
                                   settings.AGENT_CONFIGS['writer']['model'],
                                   settings.AGENT_CONFIGS['writer']['temperature']),
            'reviewer': create_mcp_llm(settings.ANTHROPIC_API_KEY,
                                     settings.AGENT_CONFIGS['reviewer']['model'], 
                                     settings.AGENT_CONFIGS['reviewer']['temperature'])
        }
    else:
        # Fallback to OpenAI
        llms = {
            'rag': ChatOpenAI(model="gpt-4-turbo", temperature=0.2),
            'researcher': ChatOpenAI(model="gpt-4-turbo", temperature=0.7),
            'writer': ChatOpenAI(model="gpt-4-turbo", temperature=0.6),
            'reviewer': ChatOpenAI(model="gpt-4-turbo", temperature=0.5)
        }
    
    # Create agents
    web_search_tool = create_tool(WebSearchTool)
    
    rag_agent = RAGAgent(
        name=settings.AGENT_CONFIGS['rag']['name'],
        llm=llms['rag'],
        search_tool=search_rag_tool
    )
    
    researcher = ResearcherAgent(
        name=settings.AGENT_CONFIGS['researcher']['name'],
        llm=llms['researcher'],
        tools=[web_search_tool]
    )
    
    writer = WriterAgent(
        name=settings.AGENT_CONFIGS['writer']['name'],
        llm=llms['writer'],
        writing_style=settings.AGENT_CONFIGS['writer']['writing_style']
    )
    
    reviewer = ReviewerAgent(
        name=settings.AGENT_CONFIGS['reviewer']['name'],
        llm=llms['reviewer']
    )
    
    return rag_agent, researcher, writer, reviewer