# config/database.py - MCP Server Database Configuration
"""
Database configuration and initialization for MCP Server
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    """Initialize database with the Flask app"""
    db.init_app(app)
    return db