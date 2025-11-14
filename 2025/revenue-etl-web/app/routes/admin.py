"""
Admin Routes
สำหรับ admin - manage config, run jobs, view logs
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from .auth import admin_required, get_current_user
from app.utils.validators import validate_year, validate_month, validate_path
import logging

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin Dashboard"""
    user = get_current_user()
    
    # ดึงข้อมูลสถานะต่าง ๆ
    etl_runner = admin_bp.etl_runner
    scheduler = admin_bp.scheduler
    file_manager = admin_bp.file_manager
    json_logger = admin_bp.json_logger
    
    # ETL status
    etl_status = etl_runner.get_status()
    
    # Schedule info
    schedule_info = scheduler.get_schedule_info()
    
    # File statistics
    stats = file_manager.get_statistics()
    
    # Recent jobs
    recent_jobs = json_logger.get_recent_jobs(limit=10)
    
    # Log access
    json_logger.log_access(user['email'], "view_admin_dashboard")
    
    return render_template(
        'admin_dashboard.html',
        user=user,
        etl_status=etl_status,
        schedule_info=schedule_info,
        stats=stats,
        recent_jobs=recent_jobs
    )


# ========== Config Management ==========

@admin_bp.route('/config')
@admin_required
def config():
    """หน้า Config Management"""
    user = get_current_user()
    config_manager = admin_bp.config_manager
    
    # ดึง configs ทั้งหมด
    etl_config = config_manager.get_etl_config()
    email_config = config_manager.get_email_config()
    auth_config = config_manager.get_auth_config()
    
    # ซ่อน sensitive data
    email_config_display = email_config.copy()
    email_config_display['smtp_password'] = '****' if email_config.get('smtp_password') else ''
    
    # Log access
    json_logger = admin_bp.json_logger
    json_logger.log_access(user['email'], "view_config")
    
    return render_template(
        'admin_config.html',
        user=user,
        etl_config=etl_config,
        email_config=email_config_display,
        auth_config=auth_config
    )


@admin_bp.route('/config/update', methods=['POST'])
@admin_required
def update_config():
    """อัพเดท ETL Config"""
    user = get_current_user()
    config_manager = admin_bp.config_manager
    
    try:
        # ดึงค่าจาก form
        config_type = request.form.get('config_type')
        
        if config_type == 'etl':
            updates = {}
            
            # Paths
            if 'input_path' in request.form:
                path = request.form['input_path'].strip()
                is_valid, msg = validate_path(path)
                if not is_valid:
                    flash(f'Input Path: {msg}', 'error')
                    return redirect(url_for('admin.config'))
                updates['input_path'] = path
            
            if 'output_path' in request.form:
                path = request.form['output_path'].strip()
                is_valid, msg = validate_path(path)
                if not is_valid:
                    flash(f'Output Path: {msg}', 'error')
                    return redirect(url_for('admin.config'))
                updates['output_path'] = path
            
            if 'master_path' in request.form:
                path = request.form['master_path'].strip()
                is_valid, msg = validate_path(path)
                if not is_valid:
                    flash(f'Master Path: {msg}', 'error')
                    return redirect(url_for('admin.config'))
                updates['master_path'] = path
            
            if 'report_path' in request.form:
                path = request.form['report_path'].strip()
                is_valid, msg = validate_path(path)
                if not is_valid:
                    flash(f'Report Path: {msg}', 'error')
                    return redirect(url_for('admin.config'))
                updates['report_path'] = path
            
            # Year
            if 'year' in request.form:
                year = request.form['year'].strip()
                is_valid, msg = validate_year(year)
                if not is_valid:
                    flash(msg, 'error')
                    return redirect(url_for('admin.config'))
                updates['year'] = year
            
            # Reconciliation
            if 'enable_reconciliation' in request.form:
                updates['enable_reconciliation'] = request.form.get('enable_reconciliation') == 'on'
            
            if 'reconcile_tolerance' in request.form:
                try:
                    updates['reconcile_tolerance'] = float(request.form['reconcile_tolerance'])
                except ValueError:
                    flash('Reconcile Tolerance ต้องเป็นตัวเลข', 'error')
                    return redirect(url_for('admin.config'))
            
            # บันทึก
            config_manager.update_etl_config(updates)
            
            # Log
            json_logger = admin_bp.json_logger
            json_logger.log_access(
                user['email'],
                "update_etl_config",
                {"updates": list(updates.keys())}
            )
            
            flash('อัพเดท ETL Config สำเร็จ', 'success')
        
        else:
            flash('ประเภท config ไม่ถูกต้อง', 'error')
    
    except Exception as e:
        logger.error(f"Error updating config: {e}", exc_info=True)
        flash(f'เกิดข้อผิดพลาด: {str(e)}', 'error')
    
    return redirect(url_for('admin.config'))


@admin_bp.route('/config/schedule/update', methods=['POST'])
@admin_required
def update_schedule():
    """อัพเดท Schedule Config"""
    user = get_current_user()
    scheduler = admin_bp.scheduler
    
    try:
        enabled = request.form.get('enabled') == 'on'
        day = int(request.form.get('day', 10))
        hour = int(request.form.get('hour', 2))
        minute = int(request.form.get('minute', 0))
        
        result = scheduler.update_schedule(
            enabled=enabled,
            day=day,
            hour=hour,
            minute=minute
        )
        
        if result['success']:
            # Log
            json_logger = admin_bp.json_logger
            json_logger.log_access(
                user['email'],
                "update_schedule",
                {
                    "enabled": enabled,
                    "day": day,
                    "hour": hour,
                    "minute": minute
                }
            )
            
            flash('อัพเดท Schedule สำเร็จ', 'success')
        else:
            flash(f'เกิดข้อผิดพลาด: {result["error"]}', 'error')
    
    except Exception as e:
        logger.error(f"Error updating schedule: {e}", exc_info=True)
        flash(f'เกิดข้อผิดพลาด: {str(e)}', 'error')
    
    return redirect(url_for('admin.config'))


# ========== Job Management ==========

@admin_bp.route('/jobs')
@admin_required
def jobs():
    """หน้า Job Management"""
    user = get_current_user()
    json_logger = admin_bp.json_logger
    etl_runner = admin_bp.etl_runner
    
    # ดึง recent jobs
    limit = request.args.get('limit', 20, type=int)
    recent_jobs = json_logger.get_recent_jobs(limit=limit)
    
    # ETL status
    etl_status = etl_runner.get_status()
    
    # Log access
    json_logger.log_access(user['email'], "view_jobs")
    
    return render_template(
        'admin_jobs.html',
        user=user,
        recent_jobs=recent_jobs,
        etl_status=etl_status
    )


@admin_bp.route('/jobs/run', methods=['POST'])
@admin_required
def run_job():
    """Manual Run ETL Job"""
    user = get_current_user()
    scheduler = admin_bp.scheduler
    
    # ดึง parameters (optional)
    year = request.form.get('year', '').strip() or None
    month = request.form.get('month', '').strip() or None
    
    # Validate
    if year:
        is_valid, msg = validate_year(year)
        if not is_valid:
            return jsonify({"success": False, "error": msg}), 400
    
    if month:
        is_valid, msg = validate_month(month)
        if not is_valid:
            return jsonify({"success": False, "error": msg}), 400
    
    try:
        # Trigger manual run
        result = scheduler.trigger_manual_run(
            triggered_by=user['email'],
            year=year,
            month=month
        )
        
        if result['success']:
            flash(f'เริ่มรัน ETL Job แล้ว (Job ID: {result["job_id"]})', 'success')
            
            if request.is_json:
                return jsonify(result)
            else:
                return redirect(url_for('admin.jobs'))
        else:
            flash(f'ไม่สามารถรัน Job ได้: {result["error"]}', 'error')
            
            if request.is_json:
                return jsonify(result), 400
            else:
                return redirect(url_for('admin.jobs'))
    
    except Exception as e:
        logger.error(f"Error running job: {e}", exc_info=True)
        error_msg = f'เกิดข้อผิดพลาด: {str(e)}'
        
        if request.is_json:
            return jsonify({"success": False, "error": error_msg}), 500
        else:
            flash(error_msg, 'error')
            return redirect(url_for('admin.jobs'))


@admin_bp.route('/jobs/<job_id>')
@admin_required
def job_detail(job_id):
    """ดูรายละเอียด Job"""
    user = get_current_user()
    json_logger = admin_bp.json_logger
    
    # ดึงข้อมูล job
    job = json_logger.get_job_by_id(job_id)
    
    if not job:
        flash('ไม่พบ Job ที่ต้องการ', 'error')
        return redirect(url_for('admin.jobs'))
    
    # Log access
    json_logger.log_access(
        user['email'],
        "view_job_detail",
        {"job_id": job_id}
    )
    
    return render_template(
        'admin_job_detail.html',
        user=user,
        job=job
    )


# ========== Logs ==========

@admin_bp.route('/logs')
@admin_required
def logs():
    """หน้า Logs"""
    user = get_current_user()
    json_logger = admin_bp.json_logger
    
    # ดึง access logs
    limit = request.args.get('limit', 100, type=int)
    filter_email = request.args.get('email')
    
    access_logs = json_logger.get_access_logs(limit=limit, email=filter_email)
    
    # Log access
    json_logger.log_access(user['email'], "view_logs")
    
    return render_template(
        'admin_logs.html',
        user=user,
        access_logs=access_logs,
        filter_email=filter_email
    )


# ========== API Endpoints ==========

@admin_bp.route('/api/status')
@admin_required
def api_status():
    """API: Get system status"""
    etl_runner = admin_bp.etl_runner
    scheduler = admin_bp.scheduler
    file_manager = admin_bp.file_manager
    
    return jsonify({
        "success": True,
        "etl_status": etl_runner.get_status(),
        "schedule_info": scheduler.get_schedule_info(),
        "stats": file_manager.get_statistics()
    })


@admin_bp.route('/api/jobs/<job_id>')
@admin_required
def api_job(job_id):
    """API: Get job details"""
    json_logger = admin_bp.json_logger
    job = json_logger.get_job_by_id(job_id)
    
    if not job:
        return jsonify({"success": False, "error": "Job not found"}), 404
    
    return jsonify({
        "success": True,
        "job": job
    })
