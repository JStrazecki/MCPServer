# config/settings.py - MCP Server Configuration Settings
"""
Configuration settings for the MCP Power BI Server
"""

import os
from datetime import timedelta

class Config:
    """Base configuration"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'postgresql://mcp_user:mcp_password@localhost:5432/mcp_powerbi'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }
    
    # Power BI settings
    POWERBI_TENANT_ID = os.environ.get('POWERBI_TENANT_ID')
    POWERBI_CLIENT_ID = os.environ.get('POWERBI_CLIENT_ID')
    POWERBI_CLIENT_SECRET = os.environ.get('POWERBI_CLIENT_SECRET')
    POWERBI_API_BASE_URL = 'https://api.powerbi.com/v1.0/myorg'
    
    # Cache settings
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    
    # Sync settings
    SYNC_INTERVAL_MINUTES = int(os.environ.get('SYNC_INTERVAL_MINUTES', 60))
    
    # Query history settings
    QUERY_HISTORY_RETENTION_DAYS = int(os.environ.get('QUERY_HISTORY_RETENTION_DAYS', 90))
    MAX_QUERY_HISTORY_PER_USER = 1000
    
    # Context generation settings
    CONTEXT_CACHE_TIMEOUT = timedelta(minutes=15)
    MAX_CONTEXT_LENGTH = 10000  # characters
    
    # API settings
    API_RATE_LIMIT = '100 per hour'
    API_KEY = os.environ.get('MCP_API_KEY')  # Optional API key for authentication
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Business rules
    BUSINESS_RULES_VERSION = '1.0'
    
    # Supported workspaces (initially just Onetribe Demo)
    INITIAL_WORKSPACES = [
        {
            'name': 'Onetribe Demo',
            'description': 'Demo workspace with Finance and Inventory models'
        }
    ]
    
    # Supported datasets
    INITIAL_DATASETS = [
        {
            'name': 'Demo - Model Inventory',
            'workspace': 'Onetribe Demo',
            'description': 'Inventory management model',
            'business_area': 'Operations'
        },
        {
            'name': 'Onetribe Demo - Model Finance',
            'workspace': 'Onetribe Demo',
            'description': 'Financial analysis model',
            'business_area': 'Finance'
        }
    ]

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_ECHO = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'default')
    return config.get(env, config['default'])