from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.retrievers import TavilySearchAPIRetriever
import os
import json
import hashlib
from langchain_community.vectorstores.utils import filter_complex_metadata



class SearchRAGTool:
    """Tool for web search and RAG integration"""
    
    def __init__(
        self, 
        tavily_api_key: str, 
        openai_api_key: str,
        persist_dir: str = "./agent_cache/vector_db"
    ):
        """
        Initialize search and RAG tools
        
        Args:
            tavily_api_key (str): Tavily API key for web search
            openai_api_key (str): OpenAI API key for embeddings
            persist_dir (str): Directory to persist vector store
        """
        self.tavily_api_key = tavily_api_key
        self.openai_api_key = openai_api_key
        self.persist_dir = persist_dir
        
        # Create directory if it doesn't exist
        os.makedirs(persist_dir, exist_ok=True)
        
        # Initialize search retriever
        self.search_retriever = TavilySearchAPIRetriever(
            tavily_api_key=tavily_api_key,
            k=5  # Number of search results to return
        )
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=openai_api_key
        )
        
        # Try to load existing vector store or create new one
        try:
            self.vector_store = Chroma(
                persist_directory=persist_dir,
                embedding_function=self.embeddings
            )
        except:
            self.vector_store = Chroma(
                embedding_function=self.embeddings,
                persist_directory=persist_dir
            )
    
    async def search_web(self, query: str) -> List[Document]:
        """
        Search the web using Tavily API
        
        Args:
            query (str): Query to search for
            
        Returns:
            List[Document]: Retrieved documents
        """
        
        results = await self.search_retriever.aget_relevant_documents(query)
        
        # Cache search results in vector store
        if results:
            self._add_to_vector_store(query, results)
        
        return results
    
    def _add_to_vector_store(self, query: str, documents: List[Document]):
        """
        Add documents to vector store with query as metadata
        
        Args:
            query (str): Original query
            documents (List[Document]): Documents to add
        """
        documents = filter_complex_metadata(documents)
        # Add query to metadata
        for doc in documents:
            # Before storing or after retrieving
            if "query" in doc.metadata:
                del doc.metadata["query"]  # Remove old query information
            doc.metadata["query"] = query
            doc.metadata["source_type"] = "web_search"
        
        # Add to vector store
        self.vector_store.add_documents(documents)
        self.vector_store.persist()
    
    def query_vector_store(self, query: str, k: int = 5) -> List[Document]:
        """
        Query the vector store for similar documents
        
        Args:
            query (str): Query to search for
            k (int): Number of documents to retrieve
            
        Returns:
            List[Document]: Retrieved documents
        """
        return self.vector_store.similarity_search(query, k=k)
    
    async def hybrid_search(self, query: str, use_web: bool = True) -> List[Document]:
        """
        Perform hybrid search using both vector store and web search
        
        Args:
            query (str): Query to search for
            use_web (bool): Whether to include web search
            
        Returns:
            List[Document]: Combined retrieved documents
        """
        # Get documents from vector store
        vector_docs = self.query_vector_store(query)
        
        if use_web:
            # Get documents from web search
            web_docs = await self.search_web(query)
            
            # Combine results with deduplication
            combined_docs = self._deduplicate_documents(vector_docs + web_docs)
            return combined_docs
        
        return vector_docs
    
    def _deduplicate_documents(self, documents: List[Document]) -> List[Document]:
        """
        Deduplicate documents based on content hash
        
        Args:
            documents (List[Document]): Documents to deduplicate
            
        Returns:
            List[Document]: Deduplicated documents
        """
        unique_docs = {}
        
        for doc in documents:
            # Create hash of content
            content_hash = hashlib.md5(doc.page_content.encode()).hexdigest()
            
            # Keep document if hash not seen or if it's from web search (prioritize web)
            if content_hash not in unique_docs or doc.metadata.get("source_type") == "web_search":
                unique_docs[content_hash] = doc
        
        return list(unique_docs.values())
    
    def add_documents(self, documents: List[Document]):
        """
        Add documents to vector store
        
        Args:
            documents (List[Document]): Documents to add
        """
        self.vector_store.add_documents(documents)
        self.vector_store.persist()

    def __del__(self):
        """Destructor to clean up resources"""
        self.close()

    def close(self):
        """
        Close the vector store and release resources
        """
        if hasattr(self, 'vector_store'):
            try:
                # Some vector stores have explicit cleanup methods
                if hasattr(self.vector_store, '_client'):
                    self.vector_store._client.close()
                # Other cleanup as needed
            except Exception as e:
                print(f"Error closing vector store: {e}")