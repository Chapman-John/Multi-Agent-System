from flask import Blueprint, request, jsonify
from app.graph.multi_agent_workflow import create_multi_agent_graph
from config.settings import create_agents
import traceback
import json
from langchain_core.documents import Document

main_bp = Blueprint('main', __name__)

@main_bp.route('/process', methods=['POST'])
@rate_limit(tier='free')
async def process_request():
    """
    Main endpoint for multi-agent processing
    """
    try:
        # Get input from request
        data = request.json
        if not data or 'input' not in data:
            return jsonify({
                "status": "error",
                "message": "Missing 'input' field in request body"
            }), 400

        input_text = data.get('input', '')
        
        # Initialize agents using the configuration
        rag_agent, researcher, writer, reviewer = create_agents()
        
        # Create workflow graph
        graph = create_multi_agent_graph(rag_agent, researcher, writer, reviewer)
        
        # Run the workflow
        result = await graph.ainvoke({"input": input_text})
        
        # Add more detailed logging
        print("Workflow Result:", result)
        
        # Format documents for response
        documents = []
        if result.get('rag_documents'):
            for doc in result.get('rag_documents'):
                # Convert Document objects to dictionaries
                if isinstance(doc, Document):
                    documents.append({
                        'content': doc.page_content,
                        'metadata': doc.metadata
                    })
        
        output = result.get('final_output', 'No output generated')
        
        return jsonify({
            "status": "success",
            "output": output,
            "documents": documents,
            "research_result": result.get('research_result', '')
        })
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Detailed Error in process_request:\n{error_trace}")
        return jsonify({
            "status": "error", 
            "message": str(e),
            "trace": error_trace
        }), 500

@main_bp.route('/search', methods=['POST'])
async def search():
    """
    Endpoint for searching documents directly
    """
    try:
        # Get input from request
        data = request.json
        if not data or 'query' not in data:
            return jsonify({
                "status": "error",
                "message": "Missing 'query' field in request body"
            }), 400

        query = data.get('query', '')
        
        # Initialize RAG agent
        rag_agent, _, _, _ = create_agents()
        
        # Retrieve documents
        documents = await rag_agent.retrieve_documents(query)
        
        # Format documents for response
        formatted_docs = []
        for doc in documents:
            formatted_docs.append({
                'content': doc.page_content,
                'metadata': doc.metadata
            })
        
        return jsonify({
            "status": "success",
            "documents": formatted_docs,
            "count": len(formatted_docs)
        })
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Detailed Error in search:\n{error_trace}")
        return jsonify({
            "status": "error", 
            "message": str(e),
            "trace": error_trace
        }), 500