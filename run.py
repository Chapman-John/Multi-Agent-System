from flask import Flask, Blueprint, render_template_string, jsonify, send_file
from app.routes.main_routes import main_bp
from config.settings import Config
import io

# Create a blueprint for documentation
docs_bp = Blueprint('docs', __name__)

@docs_bp.route('/')
def index():
    """
    Root endpoint that serves the multi-agent system frontend
    """
    try:
        return render_template_string("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Multi-Agent AI System</title>
    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            background-color: #f4f4f4;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        h1 {
            color: #333;
            text-align: center;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }
        #query-input {
            width: 100%;
            padding: 10px;
            margin-bottom: 15px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        #submit-btn {
            width: 100%;
            padding: 10px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        #submit-btn:hover {
            background-color: #45a049;
        }
        #result {
            margin-top: 20px;
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 4px;
            border: 1px solid #eee;
            min-height: 100px;
            white-space: pre-wrap;
        }
        #loading {
            display: none;
            text-align: center;
            color: #666;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Multi-Agent AI System</h1>
        
        <input type="text" id="query-input" placeholder="Enter your query...">
        <button id="submit-btn">Process Query</button>
        
        <div id="loading">Processing your query...</div>
        <div id="result"></div>
    </div>

    <script>
        document.getElementById('submit-btn').addEventListener('click', async () => {
            const queryInput = document.getElementById('query-input');
            const resultDiv = document.getElementById('result');
            const loadingDiv = document.getElementById('loading');
            
            // Reset previous state
            resultDiv.textContent = '';
            loadingDiv.style.display = 'block';
            
            try {
                // Send request to the multi-agent processing endpoint
                const response = await axios.post('/api/process', {
                    input: queryInput.value
                });
                
                // Display the result
                resultDiv.textContent = response.data.output || 'No output received';
            } catch (error) {
                // Handle any errors
                resultDiv.textContent = `Error: ${error.response ? error.response.data.message : error.message}`;
            } finally {
                // Hide loading indicator
                loadingDiv.style.display = 'none';
            }
        });
    </script>
</body>
</html>""")
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error rendering frontend: {str(e)}"
        }), 500

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Register blueprints
    app.register_blueprint(docs_bp)  # Root route serves frontend
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