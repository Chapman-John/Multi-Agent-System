from flask import Blueprint, request, jsonify
from app.graph.multi_agent_workflow import create_multi_agent_graph
from config.settings import create_agents

main_bp = Blueprint('main', __name__)

@main_bp.route('/process', methods=['POST'])
def process_request():
    """
    Main endpoint for multi-agent processing
    """
    try:
        # Get input from request
        data = request.json
        input_text = data.get('input', '')
        
        # Initialize agents using the configuration
        researcher, writer, reviewer = create_agents()
        
        # Create workflow graph
        graph = create_multi_agent_graph(researcher, writer, reviewer)
        
        # Run the workflow (synchronous call)
        result = graph.invoke({"input": input_text})
        
        return jsonify({
            "status": "success",
            "output": result.get('final_output')
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500