"""
Logging Management สำหรับ Revenue ETL Web Application
เก็บ logs แบบ JSON และ text files
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import traceback


class JSONLogger:
    """
    Logger ที่เก็บข้อมูลแบบ JSON สำหรับ structured logging
    """
    
    def __init__(self, base_dir: str = None):
        """
        Args:
            base_dir: Base directory ของ application
        """
        if base_dir is None:
            base_dir = Path(__file__).parent.parent
        
        self.base_dir = Path(base_dir)
        self.logs_dir = self.base_dir / "data" / "logs"
        self.jobs_dir = self.logs_dir / "jobs"
        
        # สร้าง directories
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        
        # กำหนด log files
        self.app_log = self.logs_dir / "app.log"
        self.access_log = self.logs_dir / "access.log"
    
    def log_access(self, email: str, action: str, details: Dict[str, Any] = None):
        """
        บันทึก user access log
        
        Args:
            email: User email
            action: Action performed (login, download, etc.)
            details: Additional details
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "email": email,
            "action": action,
            "details": details or {}
        }
        
        self._append_to_file(self.access_log, log_entry)
    
    def log_job_start(self, job_id: str, job_type: str, parameters: Dict[str, Any], 
                     triggered_by: str = "system") -> str:
        """
        บันทึกการเริ่มต้น job
        
        Args:
            job_id: Unique job identifier
            job_type: ประเภท job (monthly_auto, manual_run, etc.)
            parameters: Parameters ที่ใช้ใน job
            triggered_by: ผู้ที่สั่งรัน (email หรือ "system")
        
        Returns:
            job_file_path: Path ของ job log file
        """
        timestamp = datetime.now()
        job_file = self.jobs_dir / f"job_{timestamp.strftime('%Y%m%d_%H%M%S')}_{job_id}.json"
        
        log_entry = {
            "job_id": job_id,
            "job_type": job_type,
            "status": "running",
            "started_at": timestamp.isoformat(),
            "triggered_by": triggered_by,
            "parameters": parameters,
            "progress": [],
            "errors": [],
            "completed_at": None,
            "result": None
        }
        
        with open(job_file, 'w', encoding='utf-8') as f:
            json.dump(log_entry, f, indent=2, ensure_ascii=False)
        
        return str(job_file)
    
    def log_job_progress(self, job_file_path: str, message: str, level: str = "INFO"):
        """
        บันทึก progress ของ job
        
        Args:
            job_file_path: Path ของ job log file
            message: Progress message
            level: Log level (INFO, WARNING, ERROR)
        """
        try:
            with open(job_file_path, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
            
            progress_entry = {
                "timestamp": datetime.now().isoformat(),
                "level": level,
                "message": message
            }
            
            log_data["progress"].append(progress_entry)
            
            with open(job_file_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            logging.error(f"Error logging job progress: {e}")
    
    def log_job_error(self, job_file_path: str, error: Exception):
        """
        บันทึก error ของ job
        
        Args:
            job_file_path: Path ของ job log file
            error: Exception object
        """
        try:
            with open(job_file_path, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
            
            error_entry = {
                "timestamp": datetime.now().isoformat(),
                "error_type": type(error).__name__,
                "error_message": str(error),
                "traceback": traceback.format_exc()
            }
            
            log_data["errors"].append(error_entry)
            
            with open(job_file_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            logging.error(f"Error logging job error: {e}")
    
    def log_job_complete(self, job_file_path: str, status: str, result: Dict[str, Any] = None):
        """
        บันทึกการเสร็จสิ้น job
        
        Args:
            job_file_path: Path ของ job log file
            status: Status (success, failed, partial)
            result: Result details
        """
        try:
            with open(job_file_path, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
            
            log_data["status"] = status
            log_data["completed_at"] = datetime.now().isoformat()
            log_data["result"] = result or {}
            
            # คำนวณ duration
            started = datetime.fromisoformat(log_data["started_at"])
            completed = datetime.fromisoformat(log_data["completed_at"])
            duration_seconds = (completed - started).total_seconds()
            log_data["duration_seconds"] = duration_seconds
            
            with open(job_file_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            logging.error(f"Error logging job completion: {e}")
    
    def get_recent_jobs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        ดึง job logs ล่าสุด
        
        Args:
            limit: จำนวน jobs ที่ต้องการ
        
        Returns:
            List of job log entries (sorted by newest first)
        """
        job_files = sorted(self.jobs_dir.glob("job_*.json"), reverse=True)
        jobs = []
        
        for job_file in job_files[:limit]:
            try:
                with open(job_file, 'r', encoding='utf-8') as f:
                    job_data = json.load(f)
                    job_data["log_file"] = job_file.name
                    jobs.append(job_data)
            except Exception as e:
                logging.error(f"Error reading job file {job_file}: {e}")
        
        return jobs
    
    def get_job_by_id(self, job_id: str) -> Dict[str, Any]:
        """
        ดึง job log โดยใช้ job_id
        
        Args:
            job_id: Job identifier
        
        Returns:
            Job log entry หรือ None ถ้าไม่พบ
        """
        job_files = self.jobs_dir.glob(f"job_*_{job_id}.json")
        
        for job_file in job_files:
            try:
                with open(job_file, 'r', encoding='utf-8') as f:
                    job_data = json.load(f)
                    job_data["log_file"] = job_file.name
                    return job_data
            except Exception as e:
                logging.error(f"Error reading job file {job_file}: {e}")
        
        return None
    
    def _append_to_file(self, filepath: Path, data: Dict[str, Any]):
        """เพิ่มข้อมูลลงใน log file (JSON Lines format)"""
        try:
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
        except Exception as e:
            logging.error(f"Error appending to {filepath}: {e}")
    
    def get_access_logs(self, limit: int = 100, email: str = None) -> List[Dict[str, Any]]:
        """
        ดึง access logs
        
        Args:
            limit: จำนวน log entries
            email: Filter by email (optional)
        
        Returns:
            List of access log entries (newest first)
        """
        if not self.access_log.exists():
            return []
        
        logs = []
        try:
            with open(self.access_log, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # อ่านจากท้ายไปหน้า (newest first)
            for line in reversed(lines[-limit:]):
                try:
                    log_entry = json.loads(line.strip())
                    if email is None or log_entry.get("email") == email:
                        logs.append(log_entry)
                except json.JSONDecodeError:
                    continue
        
        except Exception as e:
            logging.error(f"Error reading access logs: {e}")
        
        return logs


def setup_app_logging(log_dir: Path, level: int = logging.INFO):
    """
    Setup standard Python logging สำหรับ application
    
    Args:
        log_dir: Directory สำหรับเก็บ log files
        level: Logging level
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Format
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    file_handler = logging.FileHandler(log_dir / 'app.log', encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # ลด noise จาก libraries
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('apscheduler').setLevel(logging.INFO)
