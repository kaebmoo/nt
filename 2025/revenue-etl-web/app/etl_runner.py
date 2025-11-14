"""
ETL Runner - Wrapper สำหรับรัน ETL scripts
รัน subprocess เพื่อไม่ให้ block web application
"""

import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime
import json
import threading
import logging

logger = logging.getLogger(__name__)


class ETLRunner:
    """
    จัดการการรัน ETL scripts
    """
    
    def __init__(self, config_manager, json_logger):
        """
        Args:
            config_manager: ConfigManager instance
            json_logger: JSONLogger instance
        """
        self.config_manager = config_manager
        self.json_logger = json_logger
        
        # Base directory (parent ของ app/)
        self.base_dir = Path(__file__).parent.parent
        self.etl_dir = self.base_dir / "etl"
        
        # Scripts paths
        self.fi_script = self.etl_dir / "fi_revenue_expense.py"
        self.report_script = self.etl_dir / "revenue_etl_report.py"
        
        # Python interpreter
        self.python_cmd = sys.executable
        
        # Lock เพื่อป้องกันการรันพร้อมกัน
        self.running_lock = threading.Lock()
        self.is_running = False
    
    def check_scripts_exist(self) -> tuple:
        """
        ตรวจสอบว่า ETL scripts มีอยู่หรือไม่
        
        Returns:
            (all_exist, missing_files)
        """
        missing = []
        
        if not self.fi_script.exists():
            missing.append(str(self.fi_script))
        
        if not self.report_script.exists():
            missing.append(str(self.report_script))
        
        return len(missing) == 0, missing
    
    def can_run(self) -> tuple:
        """
        ตรวจสอบว่าสามารถรัน ETL ได้หรือไม่
        
        Returns:
            (can_run, message)
        """
        if self.is_running:
            return False, "มี ETL job กำลังทำงานอยู่ กรุณารอให้เสร็จก่อน"
        
        scripts_exist, missing = self.check_scripts_exist()
        if not scripts_exist:
            return False, f"ไม่พบ ETL scripts: {', '.join(missing)}"
        
        return True, "OK"
    
    def run_etl_pipeline(self, job_id: str, triggered_by: str = "system", 
                        year: str = None, month: str = None) -> dict:
        """
        รัน ETL pipeline ทั้งหมด (fi_revenue_expense.py -> revenue_etl_report.py)
        
        Args:
            job_id: Unique job identifier
            triggered_by: ผู้ที่สั่งรัน (email หรือ "system")
            year: ปีที่ต้องการประมวลผล (ถ้าไม่ระบุใช้จาก config)
            month: เดือนที่ต้องการประมวลผล (optional สำหรับ manual run)
        
        Returns:
            dict: ผลการรัน
        """
        # ตรวจสอบว่ารันได้หรือไม่
        can_run, message = self.can_run()
        if not can_run:
            return {
                "success": False,
                "error": message
            }
        
        # Lock เพื่อป้องกันการรันพร้อมกัน
        with self.running_lock:
            if self.is_running:
                return {
                    "success": False,
                    "error": "มี ETL job กำลังทำงานอยู่แล้ว"
                }
            self.is_running = True
        
        try:
            # ดึง config
            etl_config = self.config_manager.get_etl_config()
            if year is None:
                year = etl_config.get("year", "2025")
            
            # สร้าง job log
            parameters = {
                "year": year,
                "month": month,
                "scripts": [str(self.fi_script), str(self.report_script)]
            }
            
            job_file = self.json_logger.log_job_start(
                job_id=job_id,
                job_type="monthly_auto" if triggered_by == "system" else "manual_run",
                parameters=parameters,
                triggered_by=triggered_by
            )
            
            logger.info(f"Starting ETL pipeline - Job ID: {job_id}, Triggered by: {triggered_by}")
            self.json_logger.log_job_progress(job_file, "เริ่มต้น ETL Pipeline")
            
            # Step 1: รัน fi_revenue_expense.py
            logger.info(f"Running step 1: {self.fi_script.name}")
            self.json_logger.log_job_progress(
                job_file, 
                f"กำลังรัน Step 1: {self.fi_script.name}"
            )
            
            success1, output1, error1 = self._run_script(self.fi_script)
            
            if not success1:
                error_msg = f"Step 1 ล้มเหลว: {error1}"
                logger.error(error_msg)
                self.json_logger.log_job_progress(job_file, error_msg, "ERROR")
                self.json_logger.log_job_error(job_file, Exception(error_msg))
                self.json_logger.log_job_complete(
                    job_file,
                    status="failed",
                    result={
                        "failed_step": "fi_revenue_expense.py",
                        "error": error1
                    }
                )
                return {
                    "success": False,
                    "error": error_msg,
                    "job_file": job_file,
                    "job_id": job_id
                }
            
            logger.info(f"Step 1 completed successfully")
            self.json_logger.log_job_progress(
                job_file,
                f"✓ Step 1 เสร็จสมบูรณ์: {self.fi_script.name}"
            )
            
            # Step 2: รัน revenue_etl_report.py
            logger.info(f"Running step 2: {self.report_script.name}")
            self.json_logger.log_job_progress(
                job_file,
                f"กำลังรัน Step 2: {self.report_script.name}"
            )
            
            success2, output2, error2 = self._run_script(self.report_script)
            
            if not success2:
                error_msg = f"Step 2 ล้มเหลว: {error2}"
                logger.error(error_msg)
                self.json_logger.log_job_progress(job_file, error_msg, "ERROR")
                self.json_logger.log_job_error(job_file, Exception(error_msg))
                self.json_logger.log_job_complete(
                    job_file,
                    status="failed",
                    result={
                        "failed_step": "revenue_etl_report.py",
                        "error": error2,
                        "step1_completed": True
                    }
                )
                return {
                    "success": False,
                    "error": error_msg,
                    "job_file": job_file,
                    "job_id": job_id,
                    "partial": True  # Step 1 สำเร็จ แต่ Step 2 ล้มเหลว
                }
            
            logger.info(f"Step 2 completed successfully")
            self.json_logger.log_job_progress(
                job_file,
                f"✓ Step 2 เสร็จสมบูรณ์: {self.report_script.name}"
            )
            
            # สำเร็จทั้งหมด
            self.json_logger.log_job_progress(
                job_file,
                "✓ ETL Pipeline เสร็จสมบูรณ์ทั้งหมด"
            )
            
            # หา report files ที่ถูกสร้าง
            report_files = self._find_generated_reports(etl_config)
            
            self.json_logger.log_job_complete(
                job_file,
                status="success",
                result={
                    "report_files": report_files,
                    "year": year,
                    "month": month
                }
            )
            
            logger.info(f"ETL pipeline completed successfully - Job ID: {job_id}")
            
            return {
                "success": True,
                "job_file": job_file,
                "job_id": job_id,
                "report_files": report_files
            }
        
        except Exception as e:
            error_msg = f"ETL pipeline error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            if 'job_file' in locals():
                self.json_logger.log_job_error(job_file, e)
                self.json_logger.log_job_complete(
                    job_file,
                    status="failed",
                    result={"error": str(e)}
                )
            
            return {
                "success": False,
                "error": error_msg,
                "job_id": job_id
            }
        
        finally:
            # ปลด lock
            with self.running_lock:
                self.is_running = False
    
    def _run_script(self, script_path: Path) -> tuple:
        """
        รัน Python script ด้วย subprocess
        
        Args:
            script_path: Path ของ script
        
        Returns:
            (success, stdout, stderr)
        """
        try:
            # เปลี่ยน working directory เป็น etl/
            cwd = script_path.parent
            
            # รัน script
            result = subprocess.run(
                [self.python_cmd, script_path.name],
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=3600  # timeout 1 ชั่วโมง
            )
            
            success = result.returncode == 0
            
            # Log output
            if result.stdout:
                logger.info(f"Script output:\n{result.stdout[:500]}")  # Log first 500 chars
            
            if result.stderr and not success:
                logger.error(f"Script error:\n{result.stderr[:500]}")
            
            return success, result.stdout, result.stderr
        
        except subprocess.TimeoutExpired:
            error_msg = f"Script {script_path.name} timeout (>1 hour)"
            logger.error(error_msg)
            return False, "", error_msg
        
        except Exception as e:
            error_msg = f"Error running script {script_path.name}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, "", error_msg
    
    def _find_generated_reports(self, etl_config: dict) -> list:
        """
        หา report files ที่ถูกสร้างใหม่
        
        Args:
            etl_config: ETL configuration
        
        Returns:
            List of report file paths
        """
        report_files = []
        
        # ดูที่ output_path และ report_path
        paths_to_check = [
            etl_config.get("output_path"),
            etl_config.get("report_path")
        ]
        
        for path_str in paths_to_check:
            if not path_str:
                continue
            
            path = Path(path_str)
            if not path.exists():
                continue
            
            # หาไฟล์ Excel ที่สร้างใหม่ภายใน 1 ชั่วโมง
            now = datetime.now().timestamp()
            
            for file in path.glob("*.xlsx"):
                mtime = file.stat().st_mtime
                # ถ้าไฟล์ถูกสร้างภายใน 1 ชั่วโมง
                if (now - mtime) < 3600:
                    report_files.append({
                        "filename": file.name,
                        "path": str(file),
                        "size": file.stat().st_size,
                        "created": datetime.fromtimestamp(mtime).isoformat()
                    })
        
        return report_files
    
    def get_status(self) -> dict:
        """
        ดึงสถานะปัจจุบันของ ETL runner
        
        Returns:
            dict: สถานะต่าง ๆ
        """
        scripts_exist, missing = self.check_scripts_exist()
        
        return {
            "is_running": self.is_running,
            "scripts_exist": scripts_exist,
            "missing_scripts": missing,
            "etl_dir": str(self.etl_dir),
            "python_version": sys.version
        }
