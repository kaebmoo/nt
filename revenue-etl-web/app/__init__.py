"""
Flask Application Factory
"""

import os
from flask import Flask
from app.config import ConfigManager
from app.logger import JSONLogger
from app.utils.email_sender import EmailSender
from app.auth import AuthManager
from app.etl_runner import ETLRunner
from app.scheduler import JobScheduler


# Global instances
config_manager = None
logger = None
email_sender = None
auth_manager = None
etl_runner = None
job_scheduler = None


def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)

    # Load configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    # Initialize components
    global config_manager, logger, email_sender, auth_manager, etl_runner, job_scheduler

    config_manager = ConfigManager()
    logger = JSONLogger()
    email_sender = EmailSender(config_manager.get_email_config())
    auth_manager = AuthManager(config_manager, email_sender, logger)
    etl_runner = ETLRunner(config_manager, logger, email_sender)
    job_scheduler = JobScheduler(config_manager, etl_runner, logger)

    # Make instances available to app
    app.config_manager = config_manager
    app.logger_instance = logger
    app.email_sender = email_sender
    app.auth_manager = auth_manager
    app.etl_runner = etl_runner
    app.job_scheduler = job_scheduler

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.user import user_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)

    # Start scheduler
    job_scheduler.start()

    logger.info("Flask application initialized")

    return app
