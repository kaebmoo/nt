"""
Admin Routes
Dashboard, config management, run jobs, view logs
"""

from pathlib import Path
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session, jsonify
from app.auth import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/')
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin dashboard - overview"""
    # Get scheduler status
    scheduler_status = current_app.job_scheduler.get_scheduler_status()

    # Get recent jobs
    recent_jobs = current_app.logger_instance.get_recent_jobs(limit=10)

    # Get reports count
    config = current_app.config_manager.get_etl_config()
    reports_dir = Path(config.get('paths', {}).get('output', 'reports'))
    reports_count = len(list(reports_dir.glob('*.xlsx'))) if reports_dir.exists() else 0

    return render_template(
        'admin/dashboard.html',
        email=session.get('email'),
        scheduler_status=scheduler_status,
        recent_jobs=recent_jobs,
        reports_count=reports_count
    )


@admin_bp.route('/config', methods=['GET', 'POST'])
@admin_required
def config():
    """Configuration management"""
    if request.method == 'POST':
        config_type = request.form.get('config_type')

        if config_type == 'etl':
            # Update ETL config
            etl_config = current_app.config_manager.get_etl_config()

            # Update paths
            etl_config['paths']['data_input'] = request.form.get('data_input', '')
            etl_config['paths']['master_files'] = request.form.get('master_files', '')

            # Update schedule
            etl_config['schedule']['enabled'] = 'schedule_enabled' in request.form
            etl_config['schedule']['day_of_month'] = int(request.form.get('day_of_month', 10))
            etl_config['schedule']['hour'] = int(request.form.get('hour', 2))
            etl_config['schedule']['minute'] = int(request.form.get('minute', 0))

            # Update notifications
            etl_config['notifications']['enabled'] = 'notifications_enabled' in request.form

            current_app.config_manager.update_etl_config(etl_config)

            # Restart scheduler to apply changes
            current_app.job_scheduler.shutdown()
            current_app.job_scheduler.start()

            current_app.logger_instance.log_access(
                session.get('email'),
                'update_config',
                {'type': 'etl'}
            )

            flash('บันทึกการตั้งค่าเรียบร้อยแล้ว', 'success')

        elif config_type == 'email':
            # Update Email config
            email_config = current_app.config_manager.get_email_config()

            email_config['smtp']['host'] = request.form.get('smtp_host', '')
            email_config['smtp']['port'] = int(request.form.get('smtp_port', 587))
            email_config['smtp']['username'] = request.form.get('smtp_username', '')

            smtp_password = request.form.get('smtp_password', '')
            if smtp_password:  # Only update if provided
                email_config['smtp']['password'] = smtp_password

            email_config['sender']['email'] = request.form.get('sender_email', '')
            email_config['sender']['name'] = request.form.get('sender_name', '')

            current_app.config_manager.update_email_config(email_config)

            # Reinitialize email sender
            current_app.email_sender = current_app.email_sender.__class__(email_config)

            current_app.logger_instance.log_access(
                session.get('email'),
                'update_config',
                {'type': 'email'}
            )

            flash('บันทึกการตั้งค่าอีเมลเรียบร้อยแล้ว', 'success')

        elif config_type == 'auth':
            # Update Auth config
            auth_config = current_app.config_manager.get_auth_config()

            # Parse domains (one per line)
            domains_text = request.form.get('allowed_domains', '')
            auth_config['allowed_domains'] = [
                d.strip() for d in domains_text.split('\n') if d.strip()
            ]

            # Parse admin emails (one per line)
            admins_text = request.form.get('admin_emails', '')
            auth_config['admin_emails'] = [
                e.strip().lower() for e in admins_text.split('\n') if e.strip()
            ]

            auth_config['session']['timeout_minutes'] = int(request.form.get('session_timeout', 60))

            current_app.config_manager.update_auth_config(auth_config)

            current_app.logger_instance.log_access(
                session.get('email'),
                'update_config',
                {'type': 'auth'}
            )

            flash('บันทึกการตั้งค่า Authentication เรียบร้อยแล้ว', 'success')

        return redirect(url_for('admin.config'))

    # GET - show config forms
    etl_config = current_app.config_manager.get_etl_config()
    email_config = current_app.config_manager.get_email_config()
    auth_config = current_app.config_manager.get_auth_config()

    return render_template(
        'admin/config.html',
        email=session.get('email'),
        etl_config=etl_config,
        email_config=email_config,
        auth_config=auth_config
    )


@admin_bp.route('/jobs')
@admin_required
def jobs():
    """View job history"""
    # Get recent jobs
    limit = request.args.get('limit', 50, type=int)
    recent_jobs = current_app.logger_instance.get_recent_jobs(limit=limit)

    return render_template(
        'admin/jobs.html',
        email=session.get('email'),
        jobs=recent_jobs
    )


@admin_bp.route('/jobs/<job_id>')
@admin_required
def job_detail(job_id):
    """View job detail"""
    job = current_app.logger_instance.get_job_log(job_id)

    if not job:
        flash('ไม่พบงานที่ระบุ', 'error')
        return redirect(url_for('admin.jobs'))

    return render_template(
        'admin/job_detail.html',
        email=session.get('email'),
        job=job
    )


@admin_bp.route('/run-job', methods=['POST'])
@admin_required
def run_job():
    """Run ETL job manually"""
    script_name = request.form.get('script')

    if not script_name:
        flash('กรุณาเลือก script ที่ต้องการรัน', 'error')
        return redirect(url_for('admin.dashboard'))

    # Get script choices from config
    etl_config = current_app.config_manager.get_etl_config()
    scripts = etl_config.get('scripts', {})

    # Validate script name
    valid_scripts = list(scripts.values())
    if script_name not in valid_scripts:
        flash('Script ไม่ถูกต้อง', 'error')
        return redirect(url_for('admin.dashboard'))

    # Run job
    result = current_app.job_scheduler.run_manual_job(
        script_name,
        triggered_by=session.get('email')
    )

    if result['status'] == 'completed':
        flash(f'รันงานสำเร็จ: {script_name}', 'success')
    else:
        flash(f'รันงานล้มเหลว: {result.get("error")}', 'error')

    return redirect(url_for('admin.job_detail', job_id=result['job_id']))


@admin_bp.route('/logs')
@admin_required
def logs():
    """View access logs"""
    limit = request.args.get('limit', 100, type=int)
    access_logs = current_app.logger_instance.get_access_logs(limit=limit)

    return render_template(
        'admin/logs.html',
        email=session.get('email'),
        logs=access_logs
    )


@admin_bp.route('/api/scheduler-status')
@admin_required
def api_scheduler_status():
    """API endpoint for scheduler status"""
    status = current_app.job_scheduler.get_scheduler_status()
    return jsonify(status)


@admin_bp.route('/api/recent-jobs')
@admin_required
def api_recent_jobs():
    """API endpoint for recent jobs"""
    limit = request.args.get('limit', 10, type=int)
    jobs = current_app.logger_instance.get_recent_jobs(limit=limit)
    return jsonify(jobs)
