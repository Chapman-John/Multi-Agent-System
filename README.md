# Multi-Agent Generative AI System

## 🚀 Overview

This project implements a state-of-the-art multi-agent AI system that leverages advanced language models and intelligent workflow orchestration to process complex information requests. The system follows an optimized workflow:

**Query → RAG Processing → Research → Writing → Review → Final Output**

By combining specialized agents with distinct capabilities and incorporating robust rate limiting, this system delivers comprehensive, accurate, and well-structured responses to user queries while ensuring optimal resource utilization.

![image](https://github.com/user-attachments/assets/56a482b1-ac00-4bb3-a8bb-b5ee97085703)


## ✨ Key Features

- **Intelligent Multi-Agent Collaboration**: Specialized agents work together through a sophisticated orchestration system
- **Mixed AI Provider Support**: Combines OpenAI GPT and Anthropic Claude models for optimal performance per task
- **Advanced RAG Integration**: Retrieval-Augmented Generation enhances responses with relevant context
- **Dynamic Research Capabilities**: Comprehensive information gathering from multiple sources
- **Quality-Focused Processing**: Built-in review and revision process ensures high-quality outputs
- **Scalable Architecture**: Cloud-ready design supports distributed deployment
- **Tiered Rate Limiting**: Redis-based rate limiting with customizable tiers for different usage levels

## 🔧 Core Technologies

| Component | Technologies |
|-----------|--------------|
| **Framework** | FastAPI, LangChain, LangGraph |
| **AI Models** | OpenAI GPT-4, GPT-3.5-turbo, Anthropic Claude-3-opus |
| **Background Processing** | Celery, Redis |
| **Infrastructure** | Docker, Redis, Cloud-ready |
| **Search & Retrieval** | Tavily, ChromaDB |
| **API Management** | FastAPI middleware, Redis-based rate limiting |

## 🤖 Current AI Model Configuration

The system uses an optimized mix of AI models for different tasks:

| Agent | Model | Provider | Temperature | Purpose |
|-------|--------|----------|-------------|---------|
| **RAG Processor** | GPT-3.5-turbo | OpenAI | 0.1 | Fast information extraction |
| **Research Assistant** | GPT-4-turbo-preview | OpenAI | 0.7 | Deep analysis and reasoning |
| **Content Writer** | Claude-3-opus | Anthropic | 0.6 | High-quality creative writing |
| **Content Reviewer** | GPT-3.5-turbo | OpenAI | 0.3 | Quick quality assessment |

This configuration balances **performance, quality, and cost** for optimal results.

## 📊 System Architecture

### Agent Ecosystem

The system employs specialized agents, each with distinct responsibilities:

1. **RAG Agent**: Enhances queries with relevant context from vector stores and search results
2. **Researcher Agent**: Gathers comprehensive information from multiple sources
3. **Writer Agent**: Synthesizes research into coherent, well-structured content
4. **Reviewer Agent**: Provides critical analysis and quality assurance

### Workflow Orchestration

- **Event-Driven Design**: LangGraph enables sophisticated state management
- **Conditional Processing**: Intelligent routing based on quality assessments
- **Iterative Refinement**: Automatic revision cycles ensure high-quality output

### Advanced RAG Implementation

- **Hybrid Search**: Combines vector similarity with keyword search
- **Document Deduplication**: Intelligent merging of information from multiple sources
- **Persistent Vector Storage**: Efficient caching of previously retrieved information

### Rate Limiting Middleware

- **Tiered Usage Plans**: Configurable rate limits based on user tiers (free, basic, premium)
- **Redis-Based Tracking**: Efficient, distributed request counting and quota management
- **Time-Window Limits**: Both per-minute and daily quota constraints
- **API Key Authentication**: Rate limits tied to individual API keys

## 🛠️ Installation

### Prerequisites

- Python 3.9+
- OpenAI API Key
- Anthropic API Key
- Tavily API Key (optional, for web search)
- Redis Server (for rate limiting and background processing)

### Method 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/Chapman-John/multi-agent-system.git
cd multi-agent-system

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys

# Start all services with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f
```

### Method 2: Local Installation

```bash
# Clone the repository
git clone https://github.com/Chapman-John/multi-agent-system.git
cd multi-agent-system

# Create and activate virtual environment
python3.11 -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install and start Redis (if not already running)
# For Ubuntu/Debian: sudo apt-get install redis-server
# For macOS: brew install redis && brew services start redis

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys and configuration
```

### Method 3: Manual Docker Deployment

```bash
# Build the Docker image
docker build -t multi-agent-ai .

# Run Redis container
docker run -d --name redis-server -p 6379:6379 redis

# Run the application container
docker run -p 5000:5000 --link redis-server:redis \
  -e OPENAI_API_KEY=your_key \
  -e ANTHROPIC_API_KEY=your_key \
  -e TAVILY_API_KEY=your_key \
  -e REDIS_HOST=redis \
  multi-agent-ai
```

## 🚀 Usage

### Starting the Application

#### Docker Compose (Recommended)
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down
```

#### Local Development
```bash
# Method 1: Using the startup script
python run.py

# Method 2: Using uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload

# Method 3: Using the Makefile
make run
```

#### Background Worker (for Celery tasks)
```bash
# In a separate terminal, start the Celery worker
celery -A worker.celery_app worker --loglevel=info
```

The application will be available at http://localhost:5000

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web interface for interactive queries |
| `/api/process` | POST | Process a query through the full multi-agent workflow |
| `/api/task/{task_id}` | GET | Get the status and result of a processing task |
| `/api/search` | POST | Perform direct document search without full processing |
| `/docs` | GET | FastAPI automatic documentation |

### Rate Limiting

The API implements tiered rate limiting based on API keys:

| Tier | Requests per Minute | Requests per Day |
|------|---------------------|------------------|
| Free | 10 | 100 |
| Basic | 30 | 1,000 |
| Premium | 100 | 10,000 |

Include your API key in requests:

```python
import requests

headers = {'X-API-Key': 'your-api-key'}
response = requests.post('http://localhost:5000/api/process', 
                         headers=headers,
                         json={'input': 'Query text'})
```

### Example API Usage

#### Processing a Query
```python
import requests
import time

# Submit query for processing
response = requests.post('http://localhost:5000/api/process', 
                         headers={'X-API-Key': 'your-api-key'},
                         json={'input': 'Explain the impact of quantum computing on cryptography'})

task_data = response.json()
task_id = task_data['task_id']

# Poll for results
while True:
    status_response = requests.get(f'http://localhost:5000/api/task/{task_id}')
    status_data = status_response.json()
    
    if status_data['status'] == 'completed':
        print(status_data['output'])
        break
    elif status_data['status'] == 'failed':
        print(f"Error: {status_data['error']}")
        break
    else:
        time.sleep(2)  # Wait 2 seconds before checking again
```

#### Direct Document Search
```python
import requests

response = requests.post('http://localhost:5000/api/search',
                         headers={'X-API-Key': 'your-api-key'},
                         json={'query': 'artificial intelligence'})

documents = response.json()['documents']
print(f"Found {len(documents)} documents")
```

## 🧩 Advanced Configuration

### Environment Variables

All configuration is managed through environment variables. See `.env.example` for all available options:

```bash
# API Keys (Required)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here

# Application Settings
APP_NAME="Multi-Agent AI System"
VERSION=1.0.0
DEBUG=false

# Database & Cache
REDIS_URL=redis://localhost:6379
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Storage
VECTOR_DB_PATH=./storage/vector_db

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Feature Flags
MCP_ENABLED=true
RAG_ENABLED=true
MAX_DOCUMENTS=5
```

### Customizing AI Models

To change the AI models used by different agents, modify the `AGENT_CONFIGS` in `app/config.py`:

```python
AGENT_CONFIGS = {
    'rag': {
        'name': 'RAG Processor',
        'model': 'gpt-3.5-turbo',      # Fast extraction
        'temperature': 0.1,
        'provider': 'openai'
    },
    'researcher': {
        'name': 'Research Assistant',
        'model': 'gpt-4-turbo-preview', # Deep reasoning
        'temperature': 0.7,
        'provider': 'openai'
    },
    'writer': {
        'name': 'Content Writer',
        'model': 'claude-3-opus-20240229', # Best writing
        'temperature': 0.6,
        'provider': 'anthropic'
    },
    'reviewer': {
        'name': 'Content Reviewer',
        'model': 'gpt-3.5-turbo',      # Quick review
        'temperature': 0.3,
        'provider': 'openai'
    }
}
```

### Available Model Options

#### OpenAI Models
- `gpt-4-turbo-preview` - Latest GPT-4 with improved performance
- `gpt-4` - Standard GPT-4 model
- `gpt-3.5-turbo` - Fast and cost-effective
- `gpt-3.5-turbo-1106` - Updated version with better performance

#### Anthropic Claude Models
- `claude-3-opus-20240229` - Most capable, best for complex tasks
- `claude-3-sonnet-20240229` - Balanced performance and speed
- `claude-3-haiku-20240307` - Fastest, most cost-effective

### Configuring Rate Limits

Rate limits are defined in the `Settings` class in `app/config.py`:

```python
RATE_LIMIT_TIERS = {
    'free': {'per_minute': 10, 'per_day': 100},
    'basic': {'per_minute': 30, 'per_day': 1000},
    'premium': {'per_minute': 100, 'per_day': 10000}
}
```

### Adding Custom Tools

1. Create your tool in `app/utils/tools.py`:

```python
from langchain_core.tools import BaseTool

class CustomSearchTool(BaseTool):
    name = "custom_search"
    description = "Search a specialized database"
    
    async def _arun(self, query: str) -> str:
        # Your implementation here
        return f"Custom search results for: {query}"
```

2. Register it in the `create_agents()` function in `app/config.py`:

```python
# Add to the agent creation
custom_tool = create_tool(CustomSearchTool)
researcher = ResearcherAgent(
    name=settings.AGENT_CONFIGS['researcher']['name'],
    llm=llms['researcher'],
    tools=[web_search_tool, custom_tool]  # Add your tool here
)
```

## 🧪 Development

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app

# Run specific test file
pytest tests/test_agents.py -v

# Using Makefile
make test
```

### Code Formatting

```bash
# Format code
make format

# Check formatting
make lint
```

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt

# Install additional dev tools
pip install black isort mypy pytest-cov

# Run in development mode with auto-reload
python run.py  # with DEBUG=true in .env
```

## 📊 Performance Optimization

- **Model Selection**: Current configuration optimizes for performance/cost balance
- **Memory Management**: Vector store automatically persists to `./storage/vector_db`
- **Caching**: Redis used for rate limiting and task status caching
- **Celery Workers**: Scale by running multiple worker processes
- **Redis Configuration**: Tune Redis settings in environment variables

## 🐳 Docker Configuration

The project includes comprehensive Docker support:

- **Dockerfile**: Builds the main application
- **docker-compose.yml**: Orchestrates all services (app, worker, Redis)
- **Multi-service deployment**: Separate containers for API and background workers

Services included:
- `app`: FastAPI web application
- `worker`: Celery background worker
- `redis`: Redis server for caching and message brokering

## 🔧 Troubleshooting

### Common Issues

1. **Redis Connection Error**: Ensure Redis is running and accessible
   ```bash
   # Check Redis status
   redis-cli ping
   ```

2. **API Key Errors**: Verify all required API keys are set in `.env`
   ```bash
   # Check your .env file has all required keys
   cat .env | grep API_KEY
   ```

3. **Import Errors**: Ensure all dependencies are installed
   ```bash
   pip install -r requirements.txt
   ```

4. **Port Conflicts**: Default port is 5000, change with `PORT` environment variable

5. **Model Access Issues**: Ensure you have access to the configured AI models
   - OpenAI: Check your API key has sufficient credits
   - Anthropic: Verify Claude API access

### Logs

```bash
# View application logs
docker-compose logs app

# View worker logs  
docker-compose logs worker

# View all logs
docker-compose logs -f

# Local development logs
tail -f storage/logs/app.log
```

### Performance Issues

- **Slow responses**: Consider switching to faster models (GPT-3.5, Claude-haiku)
- **High costs**: Adjust model configuration to use more cost-effective options
- **Memory issues**: Increase Docker memory limits or reduce MAX_DOCUMENTS

## 💰 Cost Optimization

### Current Configuration Costs (Approximate)

| Agent | Model | Cost per 1K tokens | Usage Pattern |
|-------|-------|-------------------|---------------|
| RAG | GPT-3.5-turbo | $0.002 | Light (document processing) |
| Research | GPT-4-turbo | $0.01 | Medium (analysis) |
| Writer | Claude-3-opus | $0.015 | Medium (content creation) |
| Reviewer | GPT-3.5-turbo | $0.002 | Light (quality check) |

### Budget-Friendly Alternative

For lower costs, switch all agents to GPT-3.5-turbo:

```python
# In app/config.py, set all models to:
'model': 'gpt-3.5-turbo'
'provider': 'openai'
```

## 🤝 Contributing

We welcome contributions to enhance this multi-agent system!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`make test`)
4. Commit your changes (`git commit -m 'Add some amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
