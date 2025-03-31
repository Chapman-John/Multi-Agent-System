# Multi-Agent Generative AI System

## 🚀 Overview

This project implements a state-of-the-art multi-agent AI system that leverages advanced language models and intelligent workflow orchestration to process complex information requests. The system follows an optimized workflow:

**Query → RAG Processing → Research → Writing → Review → Final Output**

By combining specialized agents with distinct capabilities, this system delivers comprehensive, accurate, and well-structured responses to user queries.

![Multi-Agent Workflow](![image](https://github.com/user-attachments/assets/c20ed1e5-7673-4a78-8b2a-bc60d07401d4)
)

## ✨ Key Features

- **Intelligent Multi-Agent Collaboration**: Specialized agents work together through a sophisticated orchestration system
- **Advanced RAG Integration**: Retrieval-Augmented Generation enhances responses with relevant context
- **Dynamic Research Capabilities**: Comprehensive information gathering from multiple sources
- **Quality-Focused Processing**: Built-in review and revision process ensures high-quality outputs
- **Scalable Architecture**: Cloud-ready design supports distributed deployment

## 🔧 Core Technologies

| Component | Technologies |
|-----------|--------------|
| **Framework** | LangChain, LangGraph |
| **Models** | OpenAI, Anthropic Claude |
| **Backend** | Flask, Python 3.9+ |
| **Infrastructure** | Docker, Cloud-ready |
| **Search & Retrieval** | Tavily, ChromaDB |

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

## 🛠️ Installation

### Prerequisites

- Python 3.9+
- OpenAI API Key
- Tavily API Key (for web search)
- Anthropic API Key (optional, for Claude models)

### Method 1: Local Installation

```bash
# Clone the repository
git clone https://github.com/Chapman-John/multi-agent-system.git
cd multi-agent-system

# Create and activate virtual environment
python3.11 -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys and configuration
```

### Method 2: Docker Deployment

```bash
# Build the Docker image
docker build -t multi-agent-ai .

# Run the container
docker run -p 5000:5000 -e OPENAI_API_KEY=your_key -e TAVILY_API_KEY=your_key multi-agent-ai
```

## 🚀 Usage

### Starting the Application

```bash
# Run the application
python run.py
```

The application will be available at http://localhost:5000

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/process` | POST | Process a query through the full multi-agent workflow |
| `/api/search` | POST | Perform direct document search without full processing |

### Example API Request

```python
import requests

response = requests.post('http://localhost:5000/api/process', 
                         json={'input': 'Explain the impact of quantum computing on cryptography'})

result = response.json()
print(result['output'])
```

## 🧩 Advanced Configuration

### Customizing Agent Behavior

Edit `config/settings.py` to modify:

- LLM parameters (temperature, model selection)
- Agent specialization settings
- Tool configuration and integration

### Adding Custom Tools

Extend the system's capabilities by implementing custom tools in `app/utils/tools.py`:

```python
from app.utils.tools import create_tool
from langchain_core.tools import BaseTool

class CustomSearchTool(BaseTool):
    name = "custom_search"
    description = "Search a specialized database"
    
    async def _arun(self, query: str) -> str:
        # Implementation goes here
        pass

# Register your tool in config/settings.py
```

## 📊 Performance Optimization

- **Memory Management**: Configure `app/utils/search_rag.py` for optimal vector storage
- **Caching**: Adjust caching parameters in `config/settings.py`
- **Model Selection**: Balance performance and quality by selecting appropriate LLMs

## 🤝 Contributing

We welcome contributions to enhance this multi-agent system!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.


