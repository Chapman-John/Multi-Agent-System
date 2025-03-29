from typing import Dict, Any, List, Optional
from langchain_anthropic import ChatAnthropicMessages
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.documents import Document
from pydantic import BaseModel

class MCPMessage(BaseModel):
    """Model Context Protocol message format"""
    role: str
    content: str
    name: Optional[str] = None

class MCPContext(BaseModel):
    """Model Context Protocol context format"""
    messages: List[MCPMessage]
    documents: Optional[List[Dict[str, Any]]] = None
    config: Optional[Dict[str, Any]] = None

def create_mcp_llm(api_key: str, model_name: str = "claude-3-opus-20240229", temperature: float = 0.7):
    """
    Create a LangChain LLM that follows the Model Context Protocol
    
    Args:
        api_key (str): Anthropic API key
        model_name (str): Claude model name
        temperature (float): Temperature for generation
        
    Returns:
        ChatAnthropicMessages: LLM configured for MCP
    """
    return ChatAnthropicMessages(
        anthropic_api_key=api_key,
        model_name=model_name,
        temperature=temperature
    )

def format_documents_for_mcp(docs: List[Document]) -> List[Dict[str, Any]]:
    """
    Format LangChain documents to MCP document format
    
    Args:
        docs (List[Document]): LangChain documents
        
    Returns:
        List[Dict[str, Any]]: MCP formatted documents
    """
    return [
        {
            "id": f"doc-{i}",
            "text": doc.page_content,
            "metadata": doc.metadata
        }
        for i, doc in enumerate(docs)
    ]

def create_mcp_context(
    query: str, 
    system_prompt: Optional[str] = None,
    documents: Optional[List[Document]] = None,
    config: Optional[Dict[str, Any]] = None
) -> MCPContext:
    """
    Create MCP context from query and optional documents
    
    Args:
        query (str): User query
        system_prompt (str, optional): System prompt
        documents (List[Document], optional): Documents for RAG context
        config (Dict[str, Any], optional): Additional configuration
        
    Returns:
        MCPContext: Formatted MCP context
    """
    messages = []
    
    # Add system message if provided
    if system_prompt:
        messages.append(MCPMessage(role="system", content=system_prompt))
    
    # Add user query
    messages.append(MCPMessage(role="user", content=query))
    
    # Format documents if provided
    mcp_documents = format_documents_for_mcp(documents) if documents else None
    
    return MCPContext(
        messages=messages,
        documents=mcp_documents,
        config=config
    )

def mcp_context_to_langchain(context: MCPContext):
    """
    Convert MCP context to LangChain messages format
    
    Args:
        context (MCPContext): MCP context
        
    Returns:
        List: LangChain message objects
    """
    messages = []
    
    for msg in context.messages:
        if msg.role == "system":
            messages.append(SystemMessage(content=msg.content))
        elif msg.role == "user":
            messages.append(HumanMessage(content=msg.content))
    
    return messages

def create_mcp_prompt_with_rag(query: str, documents: List[Document]) -> str:
    """
    Create an MCP-compatible prompt with RAG documents
    
    Args:
        query (str): User query
        documents (List[Document]): Retrieved documents
        
    Returns:
        str: Formatted prompt with document context
    """
    # Format documents into text
    formatted_docs = "\n\n".join([
        f"Document {i+1}:\nTitle: {doc.metadata.get('title', 'Untitled')}\n"
        f"Source: {doc.metadata.get('source', 'Unknown')}\n"
        f"Content: {doc.page_content}"
        for i, doc in enumerate(documents)
    ])
    
    # Create prompt with document context
    prompt = f"""
    I'm going to provide you with some relevant information to help answer a query.
    
    Here are the documents:
    {formatted_docs}
    
    Based on the above information, please answer the following query:
    {query}
    
    If the provided documents don't contain enough information to fully answer the query, 
    please state that clearly and provide the best possible answer based on the available information.
    """
    
    return prompt