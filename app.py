# app.py - MCP Server Main Application
"""
Model Context Protocol (MCP) Server for Power BI
Stores and manages Power BI model metadata to enhance analyst bot capabilities
"""

import os
import logging
from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Import configuration
from config.settings import Config
from config.database import init_db

# Import routes
from api.routes import api_bp
from api.workspace_routes import workspace_bp
from api.dataset_routes import dataset_bp
from api.query_routes import query_bp
from api.context_routes import context_bp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
CORS(app)
db = init_db(app)
migrate = Migrate(app, db)

# Register blueprints
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(workspace_bp, url_prefix='/api/workspaces')
app.register_blueprint(dataset_bp, url_prefix='/api/datasets')
app.register_blueprint(query_bp, url_prefix='/api/queries')
app.register_blueprint(context_bp, url_prefix='/api/context')

@app.route('/')
def index():
    """Root endpoint"""
    return jsonify({
        'name': 'MCP Power BI Server',
        'version': '1.0.0',
        'description': 'Model Context Protocol server for Power BI metadata',
        'endpoints': {
            'workspaces': '/api/workspaces',
            'datasets': '/api/datasets',
            'queries': '/api/queries',
            'context': '/api/context',
            'health': '/health'
        }
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        # Check database connection
        db.session.execute('SELECT 1')
        db_status = 'healthy'
    except Exception as e:
        db_status = f'unhealthy: {str(e)}'
    
    return jsonify({
        'status': 'healthy' if db_status == 'healthy' else 'degraded',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'database': db_status,
            'api': 'healthy'
        }
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Create tables if they don't exist
    with app.app_context():
        db.create_all()
        logger.info("Database tables created")
    
    # Run the application
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"Starting MCP Server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)