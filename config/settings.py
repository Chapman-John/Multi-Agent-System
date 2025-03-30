import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # API Keys
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    TAVILY_API_KEY = os.getenv('TAVILY_API_KEY', '')
    
    # Application Settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')
    DEBUG = os.getenv('FLASK_DEBUG', 'False') == 'True'
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Storage settings
    VECTOR_DB_PATH = os.getenv('VECTOR_DB_PATH', './agent_cache/vector_db')
    
    # Agent Configuration
    AGENT_CONFIGS = {
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
    
    # MCP Configuration
    MCP_ENABLED = True
    DEFAULT_MODEL = 'claude-3-opus-20240229'
    
    # RAG Configuration
    RAG_ENABLED = True
    MAX_DOCUMENTS = 5

# Utility method to create agents
def create_agents(config=Config):
    from openai import OpenAI
    from langchain_openai import ChatOpenAI
    from langchain_anthropic import ChatAnthropicMessages
    from app.utils.tools import WebSearchTool, create_tool
    from app.utils.search_rag import SearchRAGTool
    from app.utils.mcp import create_mcp_llm
    
    # Initialize API clients
    openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
    
    # Create search and RAG tool if enabled
    search_rag_tool = None
    if config.RAG_ENABLED and config.TAVILY_API_KEY:
        search_rag_tool = SearchRAGTool(
            tavily_api_key=config.TAVILY_API_KEY,
            openai_api_key=config.OPENAI_API_KEY,
            persist_dir=config.VECTOR_DB_PATH
        )
    
    # Register cleanup handler
        import atexit
        atexit.register(lambda: search_rag_tool.vector_store._client.close() 
                         if hasattr(search_rag_tool, 'vector_store') and 
                            hasattr(search_rag_tool.vector_store, '_client') 
                         else None)
    
    # Create LLM instances for each agent
    # Use MCP if enabled, otherwise use OpenAI/other models
    if config.MCP_ENABLED and config.ANTHROPIC_API_KEY:
        # Using Anthropic's Claude with MCP
        rag_llm = create_mcp_llm(
            api_key=config.ANTHROPIC_API_KEY,
            model_name=config.AGENT_CONFIGS['rag']['model'],
            temperature=config.AGENT_CONFIGS['rag']['temperature']
        )
        
        researcher_llm = create_mcp_llm(
            api_key=config.ANTHROPIC_API_KEY,
            model_name=config.AGENT_CONFIGS['researcher']['model'],
            temperature=config.AGENT_CONFIGS['researcher']['temperature']
        )
        
        writer_llm = create_mcp_llm(
            api_key=config.ANTHROPIC_API_KEY,
            model_name=config.AGENT_CONFIGS['writer']['model'],
            temperature=config.AGENT_CONFIGS['writer']['temperature']
        )
        
        reviewer_llm = create_mcp_llm(
            api_key=config.ANTHROPIC_API_KEY,
            model_name=config.AGENT_CONFIGS['reviewer']['model'],
            temperature=config.AGENT_CONFIGS['reviewer']['temperature']
        )
    else:
        # Fallback to OpenAI models
        rag_llm = ChatOpenAI(
            model="gpt-4-turbo",
            temperature=config.AGENT_CONFIGS['rag']['temperature']
        )
        
        researcher_llm = ChatOpenAI(
            model=config.AGENT_CONFIGS['researcher']['model'],
            temperature=config.AGENT_CONFIGS['researcher']['temperature']
        )
        
        writer_llm = ChatOpenAI(
            model=config.AGENT_CONFIGS['writer']['model'],
            temperature=config.AGENT_CONFIGS['writer']['temperature']
        )
        
        reviewer_llm = ChatOpenAI(
            model=config.AGENT_CONFIGS['reviewer']['model'],
            temperature=config.AGENT_CONFIGS['reviewer']['temperature']
        )
    
    # Import agent classes
    from app.agents.researcher_agent import ResearcherAgent
    from app.agents.writer_agent import WriterAgent
    from app.agents.reviewer_agent import ReviewerAgent
    from app.agents.rag_agent import RAGAgent
    
    # Create web search tool
    web_search_tool = create_tool(WebSearchTool)
    
    # Create agents with appropriate tools and configurations
    rag_agent = RAGAgent(
        name=config.AGENT_CONFIGS['rag']['name'],
        llm=rag_llm,
        search_tool=search_rag_tool
    )
    
    researcher = ResearcherAgent(
        name=config.AGENT_CONFIGS['researcher']['name'],
        llm=researcher_llm,
        tools=[web_search_tool]  
    )
    
    writer = WriterAgent(
        name=config.AGENT_CONFIGS['writer']['name'],
        llm=writer_llm,
        writing_style=config.AGENT_CONFIGS['writer']['writing_style']
    )
    
    reviewer = ReviewerAgent(
        name=config.AGENT_CONFIGS['reviewer']['name'],
        llm=reviewer_llm
    )
    
    return rag_agent, researcher, writer, reviewer