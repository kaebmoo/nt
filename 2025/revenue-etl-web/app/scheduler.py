"""
Scheduler สำหรับจัดการ ETL jobs
ใช้ APScheduler สำหรับ scheduled jobs และ manual triggers
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import uuid
import logging
import threading

logger = logging.getLogger(__name__)


class ETLScheduler:
    """
    จัดการ scheduled jobs สำหรับ ETL pipeline
    """
    
    def __init__(self, config_manager, etl_runner, json_logger, email_sender=None):
        """
        Args:
            config_manager: ConfigManager instance
            etl_runner: ETLRunner instance
            json_logger: JSONLogger instance
            email_sender: EmailSender instance (optional)
        """
        self.config_manager = config_manager
        self.etl_runner = etl_runner
        self.json_logger = json_logger
        self.email_sender = email_sender
        
        # สร้าง scheduler
        self.scheduler = BackgroundScheduler(timezone='Asia/Bangkok')
        
        # Flag สำหรับ track สถานะ
        self.is_started = False
        
        logger.info("ETL Scheduler initialized")
    
    def start(self):
        """เริ่ม scheduler"""
        if self.is_started:
            logger.warning("Scheduler already started")
            return
        
        # โหลด schedule config
        schedule_config = self.config_manager.get_schedule_config()
        
        if schedule_config.get("enabled", False):
            # เพิ่ม scheduled job
            day = schedule_config.get("day_of_month", 10)
            hour = schedule_config.get("hour", 2)
            minute = schedule_config.get("minute", 0)
            
            # สร้าง cron trigger สำหรับทุกเดือน
            trigger = CronTrigger(
                day=day,
                hour=hour,
                minute=minute,
                timezone='Asia/Bangkok'
            )
            
            self.scheduler.add_job(
                func=self._run_scheduled_etl,
                trigger=trigger,
                id='monthly_etl',
                name='Monthly ETL Pipeline',
                replace_existing=True
            )
            
            logger.info(f"Scheduled monthly ETL job: day={day}, time={hour:02d}:{minute:02d}")
        else:
            logger.info("Auto scheduling is disabled")
        
        # Start scheduler
        self.scheduler.start()
        self.is_started = True
        logger.info("Scheduler started")
    
    def stop(self):
        """หยุด scheduler"""
        if not self.is_started:
            return
        
        self.scheduler.shutdown(wait=True)
        self.is_started = False
        logger.info("Scheduler stopped")
    
    def _run_scheduled_etl(self):
        """
        รัน ETL แบบ scheduled (ถูกเรียกโดย scheduler อัตโนมัติ)
        """
        logger.info("Running scheduled ETL pipeline")
        
        job_id = f"auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # รัน ETL pipeline
            result = self.etl_runner.run_etl_pipeline(
                job_id=job_id,
                triggered_by="system"
            )
            
            if result["success"]:
                logger.info(f"Scheduled ETL completed successfully - Job ID: {job_id}")
                
                # ส่ง email notification (ถ้ามี email sender)
                if self.email_sender:
                    self._send_completion_notification(result)
            else:
                logger.error(f"Scheduled ETL failed - Job ID: {job_id}, Error: {result.get('error')}")
                
                # ส่ง email แจ้ง error ให้ admin
                if self.email_sender:
                    self._send_error_notification(result)
        
        except Exception as e:
            logger.error(f"Error in scheduled ETL: {e}", exc_info=True)
    
    def trigger_manual_run(self, triggered_by: str, year: str = None, 
                          month: str = None) -> dict:
        """
        Trigger manual ETL run (ถูกเรียกโดย admin ผ่าน web interface)
        
        Args:
            triggered_by: Email ของผู้ที่สั่งรัน
            year: ปีที่ต้องการประมวลผล (optional)
            month: เดือนที่ต้องการประมวลผล (optional)
        
        Returns:
            dict: ผลการ trigger
        """
        # ตรวจสอบว่ารันได้หรือไม่
        can_run, message = self.etl_runner.can_run()
        if not can_run:
            logger.warning(f"Manual run rejected: {message}")
            return {
                "success": False,
                "error": message
            }
        
        # สร้าง job ID
        job_id = f"manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        
        logger.info(f"Manual ETL triggered by {triggered_by} - Job ID: {job_id}")
        
        # รันใน background thread
        thread = threading.Thread(
            target=self._run_manual_etl,
            args=(job_id, triggered_by, year, month),
            daemon=True
        )
        thread.start()
        
        return {
            "success": True,
            "job_id": job_id,
            "message": "ETL job started in background"
        }
    
    def _run_manual_etl(self, job_id: str, triggered_by: str, 
                       year: str = None, month: str = None):
        """
        รัน ETL แบบ manual (ใน background thread)
        
        Args:
            job_id: Job identifier
            triggered_by: Email ของผู้ที่สั่งรัน
            year: ปี (optional)
            month: เดือน (optional)
        """
        try:
            # รัน ETL pipeline
            result = self.etl_runner.run_etl_pipeline(
                job_id=job_id,
                triggered_by=triggered_by,
                year=year,
                month=month
            )
            
            if result["success"]:
                logger.info(f"Manual ETL completed successfully - Job ID: {job_id}")
                
                # ส่ง email notification
                if self.email_sender:
                    self._send_completion_notification(result, triggered_by)
            else:
                logger.error(f"Manual ETL failed - Job ID: {job_id}, Error: {result.get('error')}")
                
                # ส่ง email แจ้ง error
                if self.email_sender:
                    self._send_error_notification(result, triggered_by)
        
        except Exception as e:
            logger.error(f"Error in manual ETL: {e}", exc_info=True)
    
    def _send_completion_notification(self, result: dict, recipient: str = None):
        """
        ส่ง email notification เมื่อ ETL เสร็จสมบูรณ์
        
        Args:
            result: ผลการรัน ETL
            recipient: Email ผู้รับ (ถ้าไม่ระบุจะส่งให้ admins)
        """
        if not self.email_sender:
            return
        
        try:
            report_files = result.get("report_files", [])
            
            if not report_files:
                logger.warning("No report files found to notify")
                return
            
            # หา recipients
            recipients = []
            if recipient:
                recipients = [recipient]
            else:
                # ส่งให้ admins ทั้งหมด
                auth_config = self.config_manager.get_auth_config()
                recipients = auth_config.get("admin_emails", [])
            
            # ส่ง email
            for email in recipients:
                for report in report_files:
                    # แปลง month/year จาก filename
                    period = self._extract_period_from_filename(report["filename"])
                    
                    self.email_sender.send_report_notification(
                        to_email=email,
                        report_name=report["filename"],
                        report_period=period
                    )
            
            logger.info(f"Sent completion notifications to {len(recipients)} recipients")
        
        except Exception as e:
            logger.error(f"Error sending completion notification: {e}")
    
    def _send_error_notification(self, result: dict, recipient: str = None):
        """
        ส่ง email notification เมื่อ ETL ล้มเหลว
        (ยังไม่ implement - สามารถเพิ่มได้ในอนาคต)
        
        Args:
            result: ผลการรัน ETL
            recipient: Email ผู้รับ
        """
        # TODO: Implement error notification email
        logger.warning("Error notification not implemented yet")
    
    def _extract_period_from_filename(self, filename: str) -> str:
        """
        แปลง filename เป็น period string (เช่น "ตุลาคม 2025")
        
        Args:
            filename: Report filename
        
        Returns:
            Period string
        """
        # ตัวอย่าง: pl_combined_output_202510.xlsx -> "ตุลาคม 2025"
        import re
        
        match = re.search(r'(\d{4})(\d{2})', filename)
        if match:
            year = match.group(1)
            month_num = int(match.group(2))
            
            thai_months = [
                "", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", 
                "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม",
                "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
            ]
            
            if 1 <= month_num <= 12:
                return f"{thai_months[month_num]} {year}"
        
        return filename
    
    def get_next_run_time(self) -> str:
        """
        ดึงเวลาที่จะรัน job ถัดไป
        
        Returns:
            ISO format datetime string หรือ None
        """
        if not self.is_started:
            return None
        
        job = self.scheduler.get_job('monthly_etl')
        if job and job.next_run_time:
            return job.next_run_time.isoformat()
        
        return None
    
    def get_schedule_info(self) -> dict:
        """
        ดึงข้อมูล schedule configuration
        
        Returns:
            dict: Schedule info
        """
        schedule_config = self.config_manager.get_schedule_config()
        
        return {
            "enabled": schedule_config.get("enabled", False),
            "day_of_month": schedule_config.get("day_of_month", 10),
            "hour": schedule_config.get("hour", 2),
            "minute": schedule_config.get("minute", 0),
            "next_run": self.get_next_run_time(),
            "is_running": self.is_started
        }
    
    def update_schedule(self, enabled: bool = None, day: int = None, 
                       hour: int = None, minute: int = None) -> dict:
        """
        อัพเดท schedule configuration
        
        Args:
            enabled: เปิด/ปิด auto scheduling
            day: วันที่ของเดือน (1-31)
            hour: ชั่วโมง (0-23)
            minute: นาที (0-59)
        
        Returns:
            dict: ผลการอัพเดท
        """
        try:
            schedule_config = self.config_manager.get_schedule_config()
            
            # อัพเดท config
            updates = {}
            if enabled is not None:
                updates["enabled"] = enabled
            if day is not None:
                if not 1 <= day <= 31:
                    return {"success": False, "error": "วันที่ต้องอยู่ระหว่าง 1-31"}
                updates["day_of_month"] = day
            if hour is not None:
                if not 0 <= hour <= 23:
                    return {"success": False, "error": "ชั่วโมงต้องอยู่ระหว่าง 0-23"}
                updates["hour"] = hour
            if minute is not None:
                if not 0 <= minute <= 59:
                    return {"success": False, "error": "นาทีต้องอยู่ระหว่าง 0-59"}
                updates["minute"] = minute
            
            # บันทึก config
            self.config_manager.update_schedule(updates)
            
            # Restart scheduler เพื่อใช้ config ใหม่
            if self.is_started:
                self.stop()
                self.start()
            
            logger.info(f"Schedule updated: {updates}")
            
            return {
                "success": True,
                "message": "อัพเดท schedule สำเร็จ",
                "schedule": self.get_schedule_info()
            }
        
        except Exception as e:
            logger.error(f"Error updating schedule: {e}")
            return {
                "success": False,
                "error": str(e)
            }
