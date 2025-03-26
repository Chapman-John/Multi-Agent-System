import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Application Settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')
    DEBUG = os.getenv('FLASK_DEBUG', 'False') == 'True'
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Agent Configuration
    AGENT_CONFIGS = {
        'researcher': {
            'name': 'Research Assistant',
            'model': 'gpt-4-turbo',
            'temperature': 0.7
        },
        'writer': {
            'name': 'Content Writer',
            'model': 'gpt-4-turbo',
            'temperature': 0.6,
            'writing_style': 'professional'
        },
        'reviewer': {
            'name': 'Content Reviewer',
            'model': 'gpt-4-turbo',
            'temperature': 0.5
        }
    }

# Utility method to create agents
def create_agents(config=Config):
    from openai import OpenAI
    from langchain_openai import ChatOpenAI
    
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    
    # Create LLM instances for each agent
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
    
    # Create agents with appropriate tools and configurations
    researcher = ResearcherAgent(
        name=config.AGENT_CONFIGS['researcher']['name'],
        llm=researcher_llm,
        tools=[]  # Add specific research tools here
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
    
    return researcher, writer, reviewer