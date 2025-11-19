# anomaly_web/config.py
"""
Configuration settings for Anomaly Detection Web Application
"""

import os
from datetime import timedelta

class Config:
    """Base configuration"""
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # File Upload
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), 'outputs')
    CONFIG_FOLDER = os.path.join(os.path.dirname(__file__), 'configs')
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500 MB max file size
    
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
    
    # Application
    APP_NAME = 'Anomaly Detection System'
    APP_VERSION = '1.0.0'
    
    # Pagination
    ROWS_PER_PAGE = 20
    
    # Progress tracking
    PROGRESS_FOLDER = os.path.join(os.path.dirname(__file__), 'progress')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    # Override with environment variables in production
    SECRET_KEY = os.environ.get('SECRET_KEY')

# Default configuration
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
