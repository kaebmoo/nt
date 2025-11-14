"""
Flask Application Factory
"""

from flask import Flask
from pathlib import Path
import logging

# Import components
from .config import ConfigManager, FlaskConfig
from .logger import JSONLogger, setup_app_logging
from .auth import OTPManager
from .utils.email_sender import EmailSender
from .utils.file_manager import FileManager
from .etl_runner import ETLRunner
from .scheduler import ETLScheduler


def create_app(config_class=FlaskConfig):
    """
    Application Factory
    
    Args:
        config_class: Configuration class
    
    Returns:
        Flask application
    """
    # สร้าง Flask app
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # =============== Setup Logging ===============
    base_dir = Path(app.root_path).parent
    logs_dir = base_dir / "data" / "logs"
    setup_app_logging(logs_dir)
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info("Starting Revenue ETL Web Application")
    logger.info("=" * 80)
    
    # =============== Initialize Components ===============
    
    # Config Manager
    logger.info("Initializing ConfigManager...")
    config_manager = ConfigManager(base_dir=base_dir)
    
    # JSON Logger
    logger.info("Initializing JSONLogger...")
    json_logger = JSONLogger(base_dir=base_dir)
    
    # OTP Manager
    logger.info("Initializing OTPManager...")
    otp_manager = OTPManager(config_manager, base_dir=base_dir)
    
    # Email Sender
    logger.info("Initializing EmailSender...")
    email_sender = EmailSender(config_manager)
    
    # File Manager
    logger.info("Initializing FileManager...")
    file_manager = FileManager(config_manager)
    
    # ETL Runner
    logger.info("Initializing ETLRunner...")
    etl_runner = ETLRunner(config_manager, json_logger)
    
    # ETL Scheduler
    logger.info("Initializing ETLScheduler...")
    scheduler = ETLScheduler(
        config_manager,
        etl_runner,
        json_logger,
        email_sender
    )
    
    # =============== Register Components with Blueprints ===============
    # ให้ blueprints สามารถเข้าถึง components ได้
    
    from .routes import auth, user, admin
    
    # Auth blueprint
    auth.auth_bp.config_manager = config_manager
    auth.auth_bp.otp_manager = otp_manager
    auth.auth_bp.email_sender = email_sender
    auth.auth_bp.json_logger = json_logger
    
    # User blueprint
    user.user_bp.file_manager = file_manager
    user.user_bp.json_logger = json_logger
    
    # Admin blueprint
    admin.admin_bp.config_manager = config_manager
    admin.admin_bp.etl_runner = etl_runner
    admin.admin_bp.scheduler = scheduler
    admin.admin_bp.file_manager = file_manager
    admin.admin_bp.json_logger = json_logger
    
    # =============== Register Routes ===============
    logger.info("Registering routes...")
    from .routes import register_routes
    register_routes(app)
    
    # =============== Error Handlers ===============
    
    @app.errorhandler(404)
    def not_found(error):
        return "404 - ไม่พบหน้าที่ต้องการ", 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal error: {error}", exc_info=True)
        return "500 - เกิดข้อผิดพลาดภายในระบบ", 500
    
    # =============== Context Processors ===============
    # ทำให้ templates เข้าถึงข้อมูลบางอย่างได้โดยอัตโนมัติ
    
    @app.context_processor
    def inject_app_info():
        return {
            'app_name': 'Revenue ETL System',
            'app_version': '1.0.0'
        }
    
    # =============== Start Scheduler ===============
    # Start scheduler เมื่อ app เริ่มทำงาน
    
    @app.before_first_request
    def start_scheduler():
        logger.info("Starting ETL Scheduler...")
        scheduler.start()
        logger.info("Scheduler started")
    
    # =============== Cleanup on Shutdown ===============
    
    import atexit
    
    def shutdown():
        logger.info("Shutting down application...")
        if scheduler.is_started:
            scheduler.stop()
        logger.info("Application stopped")
    
    atexit.register(shutdown)
    
    # =============== Ready ===============
    
    logger.info("Application initialization complete")
    logger.info(f"Base directory: {base_dir}")
    logger.info(f"ETL directory: {base_dir / 'etl'}")
    logger.info(f"Data directory: {base_dir / 'data'}")
    logger.info("=" * 80)
    
    return app
