"""
User Routes
สำหรับ user ทั่วไป - download reports
"""

from flask import Blueprint, render_template, request, send_file, flash, redirect, url_for, jsonify
from .auth import login_required, get_current_user
import logging

logger = logging.getLogger(__name__)

user_bp = Blueprint('user', __name__, url_prefix='/user')


@user_bp.route('/dashboard')
@login_required
def dashboard():
    """User Dashboard - แสดง reports ที่สามารถ download ได้"""
    user = get_current_user()
    file_manager = user_bp.file_manager
    
    # ดึง filter parameters
    year = request.args.get('year')
    month = request.args.get('month')
    
    # ดึง reports list
    reports = file_manager.list_reports(year=year, month=month, limit=50)
    
    # ดึงสถิติ
    stats = file_manager.get_statistics()
    
    # Log access
    json_logger = user_bp.json_logger
    json_logger.log_access(
        user['email'], 
        "view_dashboard",
        {"filters": {"year": year, "month": month}}
    )
    
    return render_template(
        'user_dashboard.html',
        user=user,
        reports=reports,
        stats=stats,
        filter_year=year,
        filter_month=month,
        years=stats['years']
    )


@user_bp.route('/download/<filename>')
@login_required
def download(filename):
    """Download report file"""
    user = get_current_user()
    file_manager = user_bp.file_manager
    
    # ตรวจสอบว่าไฟล์มีอยู่จริง
    report = file_manager.get_report_by_filename(filename)
    
    if not report:
        flash('ไม่พบไฟล์ที่ต้องการ', 'error')
        return redirect(url_for('user.dashboard'))
    
    try:
        # Log access
        json_logger = user_bp.json_logger
        json_logger.log_access(
            user['email'],
            "download_report",
            {
                "filename": filename,
                "size_mb": report['size_mb']
            }
        )
        
        # ส่งไฟล์
        return send_file(
            report['path'],
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    
    except Exception as e:
        logger.error(f"Error downloading file {filename}: {e}", exc_info=True)
        flash('เกิดข้อผิดพลาดในการดาวน์โหลดไฟล์', 'error')
        return redirect(url_for('user.dashboard'))


@user_bp.route('/api/reports')
@login_required
def api_reports():
    """API: List reports (JSON)"""
    user = get_current_user()
    file_manager = user_bp.file_manager
    
    year = request.args.get('year')
    month = request.args.get('month')
    limit = request.args.get('limit', 50, type=int)
    
    reports = file_manager.list_reports(year=year, month=month, limit=limit)
    
    return jsonify({
        "success": True,
        "reports": reports,
        "count": len(reports)
    })


@user_bp.route('/api/stats')
@login_required
def api_stats():
    """API: Get statistics (JSON)"""
    file_manager = user_bp.file_manager
    stats = file_manager.get_statistics()
    
    return jsonify({
        "success": True,
        "stats": stats
    })
