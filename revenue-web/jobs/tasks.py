import time
from app import create_app
from app.models import Job, User
from app import db
import sys
import os
from rq import get_current_job
from flask import current_app
import json
import logging
from datetime import datetime

# Add scripts directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))
from fi_revenue_expense import run_fi_script
from revenue_etl_report import run_etl_report

app = create_app()
app.app_context().push()

def _set_job_progress(progress, error=None):
    """Helper function to update job progress in the database."""
    job = get_current_job()
    if job:
        job.meta['progress'] = progress
        if error:
            job.meta['error'] = str(error)
        job.save_meta()
        
        # Update the Job model in the database
        job_model = Job.query.get(job.get_id())
        if job_model:
            job_model.progress = progress
            if error:
                job_model.status = 'failed'
                job_model.error_message = str(error)
            elif progress == 100:
                job_model.status = 'finished'
            db.session.commit()

def setup_logger(job_name, job_id):
    """Sets up a dedicated logger for a job."""
    log_dir = current_app.config['LOGS_DIR']
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    log_filename = os.path.join(log_dir, f'job_{job_name}_{job_id}_{timestamp}.log')
    
    logger = logging.getLogger(f'rq.job.{job_name}.{job_id}')
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicate logs
    if logger.hasHandlers():
        logger.handlers.clear()
        
    # Create a file handler
    handler = logging.FileHandler(log_filename)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger, log_filename

def run_fi_expense_task(year, month):
    """
    Background task to run the FI/Expense script.
    """
    job = get_current_job()
    logger, log_filename = setup_logger('fi_expense', job.id)
    
    job_model = Job.query.get(job.get_id())
    if job_model:
        job_model.log_file = log_filename
        db.session.commit()

    try:
        logger.info(f"Starting FI/Expense task for {month}/{year}...")
        _set_job_progress(0)

        with open('config.json') as f:
            config = json.load(f)
        
        logger.info("Configuration loaded.")
        _set_job_progress(10)

        result = run_fi_script(config, year, month, logger)

        if result.get('status') == 'success':
            logger.info(f"FI/Expense script finished successfully. Output: {result.get('output_file')}")
            _set_job_progress(100)
        else:
            error_message = result.get('message', 'Unknown error')
            logger.error(f"FI/Expense script failed: {error_message}")
            _set_job_progress(100, error=error_message)

    except Exception as e:
        logger.error("Unhandled exception in FI/Expense task.", exc_info=True)
        _set_job_progress(100, error=e)
        raise

def run_revenue_etl_task(year, month):
    """
    Background task to run the main Revenue ETL report script.
    """
    job = get_current_job()
    logger, log_filename = setup_logger('revenue_etl', job.id)

    job_model = Job.query.get(job.get_id())
    if job_model:
        job_model.log_file = log_filename
        db.session.commit()

    try:
        logger.info(f"Starting Revenue ETL task for {month}/{year}...")
        _set_job_progress(0)

        with open('config.json') as f:
            config = json.load(f)
        
        logger.info("Configuration loaded.")
        _set_job_progress(10)

        result = run_etl_report(config, year, month, logger)

        if result.get('status') == 'success':
            logger.info(f"Revenue ETL script finished successfully. Output: {result.get('output_file')}")
            _set_job_progress(100)
        else:
            error_message = result.get('message', 'Unknown error')
            logger.error(f"Revenue ETL script failed: {error_message}")
            _set_job_progress(100, error=error_message)

    except Exception as e:
        logger.error("Unhandled exception in Revenue ETL task.", exc_info=True)
        _set_job_progress(100, error=e)
        raise
