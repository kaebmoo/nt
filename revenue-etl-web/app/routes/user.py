"""
User Routes
Dashboard, download reports
"""

import os
from pathlib import Path
from flask import Blueprint, render_template, send_file, current_app, session
from app.auth import login_required

user_bp = Blueprint('user', __name__, url_prefix='/user')


@user_bp.route('/')
@user_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard - view and download reports"""
    config = current_app.config_manager.get_etl_config()
    reports_dir = Path(config.get('paths', {}).get('output', 'reports'))

    # Get list of report files
    reports = []
    if reports_dir.exists():
        for file_path in sorted(reports_dir.glob('*.xlsx'), reverse=True):
            reports.append({
                'filename': file_path.name,
                'size': file_path.stat().st_size,
                'modified': file_path.stat().st_mtime
            })

    return render_template(
        'user/dashboard.html',
        reports=reports,
        email=session.get('email')
    )


@user_bp.route('/download/<filename>')
@login_required
def download_report(filename):
    """Download report file"""
    # Validate filename (prevent directory traversal)
    if '..' in filename or '/' in filename or '\\' in filename:
        return "Invalid filename", 400

    config = current_app.config_manager.get_etl_config()
    reports_dir = Path(config.get('paths', {}).get('output', 'reports'))
    file_path = reports_dir / filename

    if not file_path.exists():
        return "File not found", 404

    # Log download
    current_app.logger_instance.log_access(
        session.get('email'),
        'download_report',
        {'filename': filename}
    )

    return send_file(
        file_path,
        as_attachment=True,
        download_name=filename
    )
