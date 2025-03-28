from flask import Blueprint, request, jsonify
from app.graph.multi_agent_workflow import create_multi_agent_graph
from config.settings import create_agents
import traceback

main_bp = Blueprint('main', __name__)

@main_bp.route('/process', methods=['POST'])
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
        researcher, writer, reviewer = create_agents()
        
        # Create workflow graph
        graph = create_multi_agent_graph(researcher, writer, reviewer)
        
        # Run the workflow
        result = await graph.ainvoke({"input": input_text})
        
        # Add more detailed logging
        print("Workflow Result:", result)
        
        output = result.get('final_output', 'No output generated')
        
        return jsonify({
            "status": "success",
            "output": output
        })
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Detailed Error in process_request:\n{error_trace}")
        return jsonify({
            "status": "error", 
            "message": str(e),
            "trace": error_trace
        }), 500