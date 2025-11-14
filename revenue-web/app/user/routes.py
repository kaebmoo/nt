import os
import json
from flask import render_template, flash, current_app, abort, send_from_directory
from flask_login import login_required, current_user
from app.user import bp
from functools import wraps

def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.has_role('user'):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/dashboard')
@login_required
@user_required
def dashboard():
    config_file = current_app.config['CONFIG_JSON_FILE']
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        report_dir_name = config_data.get('paths', {}).get('final_output', 'reports')
        report_dir = os.path.join(os.path.dirname(config_file), report_dir_name)
    except (FileNotFoundError, json.JSONDecodeError):
        report_dir = current_app.config['REPORTS_DIR']

    if not os.path.exists(report_dir):
        os.makedirs(report_dir)
        flash('ไม่พบโฟลเดอร์เก็บรายงาน, ได้สร้างโฟลเดอร์ใหม่แล้ว', 'warning')
        report_files = []
    else:
        report_files = sorted(
            [f for f in os.listdir(report_dir) if f.endswith('.xlsx')],
            key=lambda f: os.path.getmtime(os.path.join(report_dir, f)),
            reverse=True
        )
        
    return render_template('user/dashboard.html', report_files=report_files)

@bp.route('/download/<filename>')
@login_required
@user_required
def download_file(filename):
    config_file = current_app.config['CONFIG_JSON_FILE']
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        report_dir_name = config_data.get('paths', {}).get('final_output', 'reports')
        report_dir = os.path.join(os.path.dirname(config_file), report_dir_name)
    except (FileNotFoundError, json.JSONDecodeError):
        report_dir = current_app.config['REPORTS_DIR']
        
    return send_from_directory(directory=report_dir, path=filename, as_attachment=True)
