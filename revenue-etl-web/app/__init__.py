"""
Flask Application Factory
"""

import os
from flask import Flask
from app.config import ConfigManager
from app.logger import JSONLogger
from app.utils.email_sender import EmailSender
from app.utils.queue_manager import QueueManager
from app.auth import AuthManager
from app.etl_runner import ETLRunner
from app.scheduler import JobScheduler


# Global instances
config_manager = None
logger = None
email_sender = None
queue_manager = None
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
    global config_manager, logger, email_sender, queue_manager, auth_manager, etl_runner, job_scheduler

    config_manager = ConfigManager()
    logger = JSONLogger()
    email_sender = EmailSender(config_manager.get_email_config())
    queue_manager = QueueManager()
    auth_manager = AuthManager(config_manager, email_sender, logger, queue_manager)
    etl_runner = ETLRunner(config_manager, logger, email_sender)
    job_scheduler = JobScheduler(config_manager, etl_runner, logger)

    # Make instances available to app
    app.config_manager = config_manager
    app.logger_instance = logger
    app.email_sender = email_sender
    app.queue_manager = queue_manager
    app.auth_manager = auth_manager
    app.etl_runner = etl_runner
    app.job_scheduler = job_scheduler

    # Register blueprints
    from flask import redirect, url_for
    from app.routes.auth import auth_bp
    from app.routes.user import user_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)

    # Custom Jinja2 filters
    @app.template_filter('timestamp_to_datetime')
    def timestamp_to_datetime_filter(timestamp):
        """Convert Unix timestamp to readable datetime string"""
        try:
            from datetime import datetime
            dt = datetime.fromtimestamp(float(timestamp))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            return str(timestamp)

    # Root route - redirect to login
    @app.route('/')
    def index():
        """Redirect root to login page"""
        return redirect(url_for('auth.login'))

    # Start scheduler
    job_scheduler.start()

    logger.info("Flask application initialized")

    return app
