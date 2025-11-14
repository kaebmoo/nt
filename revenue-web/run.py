from app import create_app
import os

app = create_app()

# Automatically create database tables if the DB file does not exist
with app.app_context():
    from app import db
    # Assumes SQLite, parses the path from the URI
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if db_uri.startswith('sqlite:///'):
        db_path = db_uri.split('sqlite:///')[1]
        if not os.path.exists(db_path):
            print('--- Database file not found. Creating all tables... ---')
            db.create_all()
            print('--- Database tables created successfully. ---')

@app.shell_context_processor
def make_shell_context():
    from app import db
    from app.models import User, Role
    return {'db': db, 'User': User, 'Role': Role}
