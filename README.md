# Multi-Agent Generative AI System

## Overview

This project represents a cutting-edge multi-agent AI application leveraging advanced language model technologies and intelligent system design.

- LangChain
- LangGraph
- OpenAI
- Flask
- Docker

The multi-agent system now follows this workflow:
Query → RAG Processing → Research → Writing → Review → Final Output

### Core Technologies
- **LangChain & LangGraph**: Advanced frameworks for building intelligent, event-driven AI workflows
- **Large Language Models (LLMs)**: Intelligent reasoning and decision-making engines
- **Cloud-Native Architecture**: Designed for scalability and flexibility
- **Event-Driven System**: Enables complex, adaptive agent interactions

## Architecture Highlights

### Intelligent Agent Ecosystem
- **Modular Agent Design**: Specialized agents with distinct roles and capabilities
- **Dynamic Workflow Orchestration**: Agents collaborate and communicate seamlessly
- **Adaptive Problem-Solving**: Intelligent routing and task allocation

### Key Components
- **Researcher Agent**: Conducts comprehensive information gathering
- **Writer Agent**: Synthesizes research into coherent content
- **Reviewer Agent**: Provides critical analysis and quality assurance
- **Advanced Communication Protocol**: Standardized inter-agent messaging
- **Contextual Memory System**: Persistent learning and knowledge retention

## Technical Architecture

### Event-Driven Workflow
- Leverages LangGraph for state-based workflow management
- Implements intelligent conditional routing
- Supports complex, adaptive task sequences

### Tool Integration
- Multiple search source support
- Dynamic tool registry
- Extensible tool management system

### Cloud and Scalability
- **Cloud-Ready**: Containerized with Docker
- **Deployment Flexibility**: Supports multiple cloud platforms (GCP, AWS)
- **Horizontal Scalability**: Designed for distributed computing

## Prerequisites

- Python 3.9+
- OpenAI API Key
- Docker (optional)

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/Chapman-John/multi-agent-system.git
cd multi-agent-system
```

### 2. Setup Virtual Environment
```bash
# python3 -m venv env
python3.11 -m venv env 
source env/bin/activate  # On Windows: multiagent_env\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
Create a `.env` file:
```
OPENAI_API_KEY=your_openai_api_key
SECRET_KEY=your_secret_key
```

### 5. Run the Application
```bash
python run.py
```

### 6. Docker Deployment (Optional)
```bash
docker build -t multi-agent-ai .
docker run -p 5000:5000 multi-agent-ai
```

## Configuration Options

### Agent Customization
- Modify `config/settings.py` to adjust agent behaviors
- Configure LLM parameters
- Add custom tools in `app/utils/tools.py`

## Advanced Features

- **Contextual Memory**: Agents learn and retain information
- **Multi-Source Search**: Comprehensive information gathering
- **Adaptive Workflows**: Dynamic task routing

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.
