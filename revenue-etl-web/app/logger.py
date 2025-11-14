"""
Logging System
JSON-based logging for application events, user access, and ETL jobs
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class JSONLogger:
    """JSON-based logging system"""

    def __init__(self, log_dir: str = "data/logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.jobs_dir = self.log_dir / "jobs"
        self.jobs_dir.mkdir(exist_ok=True)

        # Setup standard Python logger for app logs
        self.app_logger = self._setup_app_logger()

    def _setup_app_logger(self) -> logging.Logger:
        """Setup application logger"""
        logger = logging.getLogger('revenue_etl')
        logger.setLevel(logging.INFO)

        # File handler
        log_file = self.log_dir / "app.log"
        handler = logging.FileHandler(log_file)
        handler.setLevel(logging.INFO)

        # Format
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)

        # Add handler if not already added
        if not logger.handlers:
            logger.addHandler(handler)

        return logger

    def log_access(self, email: str, action: str, details: Optional[Dict[str, Any]] = None):
        """Log user access and actions"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "email": email,
            "action": action,
            "details": details or {}
        }

        # Append to access log file (JSON Lines format)
        access_log = self.log_dir / "access.log"
        with open(access_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

    def log_job_start(self, job_id: str, script: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Log ETL job start"""
        job_data = {
            "job_id": job_id,
            "script": script,
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "params": params or {},
            "output": [],
            "error": None
        }

        job_file = self.jobs_dir / f"{job_id}.json"
        self._save_json(job_file, job_data)

        self.app_logger.info(f"Job {job_id} started: {script}")
        return str(job_file)

    def log_job_output(self, job_id: str, line: str):
        """Append output line to job log"""
        job_file = self.jobs_dir / f"{job_id}.json"
        if job_file.exists():
            job_data = self._load_json(job_file)
            job_data["output"].append({
                "timestamp": datetime.now().isoformat(),
                "line": line
            })
            self._save_json(job_file, job_data)

    def log_job_complete(self, job_id: str, success: bool, error: Optional[str] = None):
        """Log ETL job completion"""
        job_file = self.jobs_dir / f"{job_id}.json"
        if job_file.exists():
            job_data = self._load_json(job_file)
            job_data["status"] = "completed" if success else "failed"
            job_data["end_time"] = datetime.now().isoformat()
            if error:
                job_data["error"] = error
            self._save_json(job_file, job_data)

            status = "completed successfully" if success else f"failed: {error}"
            self.app_logger.info(f"Job {job_id} {status}")

    def get_job_log(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job log by ID"""
        job_file = self.jobs_dir / f"{job_id}.json"
        if job_file.exists():
            return self._load_json(job_file)
        return None

    def get_recent_jobs(self, limit: int = 20) -> list:
        """Get recent job logs"""
        job_files = sorted(
            self.jobs_dir.glob("*.json"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )[:limit]

        jobs = []
        for job_file in job_files:
            job_data = self._load_json(job_file)
            if job_data:
                jobs.append(job_data)

        return jobs

    def get_access_logs(self, limit: int = 100) -> list:
        """Get recent access logs"""
        access_log = self.log_dir / "access.log"
        if not access_log.exists():
            return []

        logs = []
        with open(access_log, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Get last N lines
        for line in lines[-limit:]:
            try:
                logs.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                continue

        return list(reversed(logs))  # Most recent first

    def _load_json(self, path: Path) -> Optional[Dict[str, Any]]:
        """Load JSON file"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.app_logger.error(f"Error loading {path}: {e}")
            return None

    def _save_json(self, path: Path, data: Dict[str, Any]):
        """Save JSON file"""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.app_logger.error(f"Error saving {path}: {e}")

    def info(self, message: str):
        """Log info message"""
        self.app_logger.info(message)

    def error(self, message: str):
        """Log error message"""
        self.app_logger.error(message)

    def warning(self, message: str):
        """Log warning message"""
        self.app_logger.warning(message)
