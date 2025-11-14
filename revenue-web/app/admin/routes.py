import os
import json
from flask import render_template, flash, redirect, url_for, current_app, abort, Response, request
from flask_login import login_required, current_user
from app import db
from app.admin import bp
from app.models import Job
from app.forms import ConfigForm, JobForm
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    form = JobForm()
    # Info for dashboard
    running_jobs = current_app.task_queue.jobs
    failed_jobs = current_app.task_queue.failed_job_registry.get_job_ids()
    log_dir = current_app.config['LOGS_DIR']
    log_files = sorted(
        [f for f in os.listdir(log_dir) if f.endswith('.log')],
        key=lambda f: os.path.getmtime(os.path.join(log_dir, f)),
        reverse=True
    )
    return render_template('admin/dashboard.html', 
                           form=form, 
                           running_jobs=running_jobs, 
                           failed_jobs=failed_jobs,
                           log_files=log_files)

@bp.route('/run-job', methods=['POST'])
@login_required
def run_job():
    if not current_user.is_admin:
        abort(403)
    
    year = request.form.get('year')
    month = request.form.get('month')
    job_type = request.form.get('job_type')

    if not year or not month:
        flash('Year and month are required.', 'danger')
        return redirect(url_for('admin.dashboard'))

    if job_type == 'fi_expense':
        task_function = 'jobs.tasks.run_fi_expense_task'
        job_name = f"FI/Expense for {month}/{year}"
    elif job_type == 'revenue_etl':
        task_function = 'jobs.tasks.run_revenue_etl_task'
        job_name = f"Revenue ETL for {month}/{year}"
    else:
        flash('Invalid job type specified.', 'danger')
        return redirect(url_for('admin.dashboard'))

    try:
        # Enqueue the job
        queue = current_app.task_queue
        job = queue.enqueue(task_function, year, month, job_timeout=3600)
        
        # Create a new Job record
        new_job = Job(
            id=job.get_id(),
            name=job_name,
            user_id=current_user.id,
            status='queued'
        )
        db.session.add(new_job)
        db.session.commit()
        
        flash(f'Job "{job_name}" has been queued.', 'success')
    except Exception as e:
        flash(f'Error queuing job: {e}', 'danger')
        current_app.logger.error(f"Failed to queue job: {e}", exc_info=True)

    return redirect(url_for('admin.dashboard'))

@bp.route('/config', methods=['GET', 'POST'])
@login_required
@admin_required
def config():
    form = ConfigForm()
    config_file = current_app.config['CONFIG_JSON_FILE']
    if form.validate_on_submit():
        try:
            # Validate if data is valid JSON
            json.loads(form.config_data.data)
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(form.config_data.data)
            flash('บันทึกการตั้งค่าสำเร็จ', 'success')
        except json.JSONDecodeError:
            flash('ข้อมูลไม่เป็น JSON format ที่ถูกต้อง', 'danger')
        except Exception as e:
            flash(f'เกิดข้อผิดพลาดในการบันทึก: {e}', 'danger')
        return redirect(url_for('admin.config'))

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            form.config_data.data = f.read()
    except FileNotFoundError:
        flash(f'ไม่พบไฟล์ {config_file}, สร้างไฟล์ใหม่', 'warning')
        form.config_data.data = '''{ "paths": {}, "master_files": {} }'''
    
    return render_template('admin/config.html', form=form)

@bp.route('/logs')
@login_required
@admin_required
def log_list():
    log_dir = current_app.config['LOGS_DIR']
    log_files = sorted(
        [f for f in os.listdir(log_dir) if f.endswith('.log')],
        key=lambda f: os.path.getmtime(os.path.join(log_dir, f)),
        reverse=True
    )
    return render_template('admin/logs.html', log_files=log_files)

@bp.route('/logs/<filename>')
@login_required
@admin_required
def view_log(filename):
    log_dir = current_app.config['LOGS_DIR']
    filepath = os.path.join(log_dir, filename)
    if not os.path.exists(filepath):
        abort(404)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    return Response(content, mimetype='text/plain')
