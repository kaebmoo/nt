import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_mail import Mail
from flask_migrate import Migrate
from redis import Redis
import rq
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
mail = Mail()

# Redirect users based on role after login
def role_based_redirect():
    if current_user.is_authenticated:
        if current_user.has_role('admin'):
            return redirect(url_for('admin.dashboard'))
        elif current_user.has_role('user'):
            return redirect(url_for('user.dashboard'))
    return redirect(url_for('public.login'))

login.login_view = 'public.login'
login.login_message = 'กรุณาล็อกอินเพื่อเข้าใช้งาน'
login.login_message_category = 'info'

@login.user_loader
def load_user(id):
    from app.models import User
    return User.query.get(int(id))


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)

    app.redis = Redis.from_url(app.config['REDIS_URL'])
    app.task_queue = rq.Queue('revenue-jobs', connection=app.redis)

    # Register Blueprints
    from app.public import bp as public_bp
    app.register_blueprint(public_bp)

    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from app.user import bp as user_bp
    app.register_blueprint(user_bp, url_prefix='/user')
    
    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    if not app.debug and not app.testing:
        if not os.path.exists(app.config['LOGS_DIR']):
            os.mkdir(app.config['LOGS_DIR'])
        file_handler = RotatingFileHandler(
            os.path.join(app.config['LOGS_DIR'], 'revenue_web.log'),
            maxBytes=10240, backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Revenue Web startup')

    from app import models
    return app