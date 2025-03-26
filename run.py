from flask import Flask, Blueprint, render_template_string, jsonify
from app.routes.main_routes import main_bp
from config.settings import Config

# Create a blueprint for documentation
docs_bp = Blueprint('docs', __name__)

@docs_bp.route('/')
def index():
    """
    Root endpoint that provides API documentation
    """
    try:
        html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Multi-Agent System API</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            background-color: #ffffff;
            color: #333333;
        }
        .endpoint {
            background-color: #f5f5f5;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        code {
            background-color: #f0f0f0;
            padding: 2px 5px;
            border-radius: 3px;
            font-family: monospace;
        }
        pre {
            background-color: #f0f0f0;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            font-family: monospace;
            margin: 10px 0;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
            margin-top: 0;
        }
        h2 {
            color: #34495e;
            margin-top: 30px;
        }
        h3 {
            color: #2c3e50;
        }
        .error {
            color: #e74c3c;
            background-color: #fde8e8;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }
        p {
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <h1>Multi-Agent System API</h1>
    <p>Welcome to the Multi-Agent System API. This system uses multiple AI agents to process and analyze text input.</p>
    
    <h2>Available Endpoints</h2>
    
    <div class="endpoint">
        <h3>POST /api/process</h3>
        <p>Process text input using the multi-agent system.</p>
        
        <h4>Request Format:</h4>
        <pre>{
    "input": "Your text input here"
}</pre>
        
        <h4>Example Usage:</h4>
        <pre>curl -X POST http://127.0.0.1:5000/api/process \
     -H "Content-Type: application/json" \
     -d '{"input": "Your text input here"}'</pre>
        
        <h4>Response Format:</h4>
        <pre>{
    "status": "success",
    "output": "Processed output from the agents"
}</pre>
    </div>
    
    <h2>Error Handling</h2>
    <p>In case of errors, the API will return a response in the following format:</p>
    <pre>{
    "status": "error",
    "message": "Error description"
}</pre>
</body>
</html>
        """
        return render_template_string(html_content)
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error rendering documentation: {str(e)}"
        }), 500

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Register blueprints
    app.register_blueprint(docs_bp)  # No prefix for documentation
    app.register_blueprint(main_bp, url_prefix='/api')  # API routes with /api prefix
    
    # Add error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({
            "status": "error",
            "message": "The requested URL was not found on the server."
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            "status": "error",
            "message": "An internal server error occurred."
        }), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)