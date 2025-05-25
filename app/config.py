from pydantic_settings import BaseSettings
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
        'model': 'gpt-3.5-turbo',
        'temperature': 0.1,
        'provider': 'openai'
    },
    'researcher': {
        'name': 'Research Assistant',
        'model': 'gpt-4-turbo-preview',
        'temperature': 0.7,
        'provider': 'openai'
    },
    'writer': {
        'name': 'Content Writer',
        'model': 'claude-3-opus-20240229',
        'temperature': 0.6,
        'provider': 'anthropic'
    },
    'reviewer': {
        'name': 'Content Reviewer',
        'model': 'gpt-3.5-turbo',
        'temperature': 0.3,
        'provider': 'openai'
    }
}
    # Feature Flags
    MIXED_PROVIDERS = True
    MCP_ENABLED: bool = True
    RAG_ENABLED: bool = True
    MAX_DOCUMENTS: int = 5

    model_config = {"env_file": ".env"}
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create required directories
        self._create_directories()
    
    def _create_directories(self):
        """Create required directories if they don't exist"""
        directories = [
            self.VECTOR_DB_PATH,
            "./storage/cache",
            "./storage/logs"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)

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
    
    # Create LLMs based on individual agent configuration
    llms = {}
    
    for agent_name, config in settings.AGENT_CONFIGS.items():
        provider = config.get('provider', 'anthropic')
        model = config['model']
        temperature = config['temperature']
        
        if provider == 'anthropic' and settings.ANTHROPIC_API_KEY:
            llms[agent_name] = create_mcp_llm(
                api_key=settings.ANTHROPIC_API_KEY,
                model_name=model,
                temperature=temperature
            )
        elif provider == 'openai' and settings.OPENAI_API_KEY:
            llms[agent_name] = ChatOpenAI(
                model=model,
                temperature=temperature,
                openai_api_key=settings.OPENAI_API_KEY
            )
        else:
            # Fallback to GPT-3.5
            llms[agent_name] = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=temperature,
                openai_api_key=settings.OPENAI_API_KEY
            )
    
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
        writing_style=settings.AGENT_CONFIGS['writer'].get('writing_style', 'professional')
    )
    
    reviewer = ReviewerAgent(
        name=settings.AGENT_CONFIGS['reviewer']['name'],
        llm=llms['reviewer']
    )
    
    return rag_agent, researcher, writer, reviewer