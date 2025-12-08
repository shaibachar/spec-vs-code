"""
Spec Compliance Checker Service - Main Application Entry Point
"""
import os
import logging
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

from src.api.routes import api_blueprint
from src.utils.logger import setup_logging

# Load environment variables
load_dotenv()

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Configure CORS
    CORS(app)
    
    # Configuration
    app.config['SERVICE_PORT'] = int(os.getenv('SERVICE_PORT', 8080))
    app.config['MAX_CONCURRENT_CHECKS'] = int(os.getenv('MAX_CONCURRENT_CHECKS', 3))
    app.config['API_KEY'] = os.getenv('API_KEY')
    
    # Register blueprints
    app.register_blueprint(api_blueprint, url_prefix='/api/v1')
    
    logger.info(f"Spec Compliance Checker Service initialized")
    logger.info(f"Ollama Host: {os.getenv('OLLAMA_HOST')}")
    logger.info(f"Service Port: {app.config['SERVICE_PORT']}")
    
    return app

def main():
    """Main entry point"""
    app = create_app()
    port = app.config['SERVICE_PORT']
    
    logger.info(f"Starting Spec Compliance Checker Service on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    main()
