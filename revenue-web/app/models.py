from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import random
import string

user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'))
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    roles = db.relationship('Role', secondary=user_roles, backref=db.backref('users', lazy='dynamic'))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, role_name):
        for role in self.roles:
            if role.name == role_name:
                return True
        return False
    
    def is_admin(self):
        return self.has_role('admin')


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    description = db.Column(db.String(255))

    @staticmethod
    def insert_roles():
        roles = {
            'user': 'Standard user with access to the user dashboard.',
            'admin': 'Administrator with full access to all features.'
        }
        for r_name, r_desc in roles.items():
            role = Role.query.filter_by(name=r_name).first()
            if role is None:
                role = Role(name=r_name, description=r_desc)
                db.session.add(role)
        db.session.commit()

class Otp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    otp_code = db.Column(db.String(6), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)

    user = db.relationship('User', backref='otps')

    def __init__(self, user_id):
        self.user_id = user_id
        self.otp_code = ''.join(random.choices(string.digits, k=6))
        self.expires_at = datetime.utcnow() + timedelta(minutes=5)

    def is_valid(self):
        return datetime.utcnow() < self.expires_at

class Job(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    status = db.Column(db.String(32), default='queued')
    
    user = db.relationship('User', backref='jobs')

    def __repr__(self):
        return f'<Job {self.name}>'
