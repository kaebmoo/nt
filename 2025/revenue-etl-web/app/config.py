"""
Configuration Management สำหรับ Revenue ETL Web Application
ใช้ JSON files แทน database เพื่อความเรียบง่าย
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    จัดการ configuration ทั้งหมดผ่าน JSON files
    """
    
    def __init__(self, base_dir: str = None):
        """
        Args:
            base_dir: Base directory ของ application (default: parent ของ app/)
        """
        if base_dir is None:
            base_dir = Path(__file__).parent.parent
        
        self.base_dir = Path(base_dir)
        self.config_dir = self.base_dir / "data" / "config"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # กำหนด paths ของ config files
        self.etl_config_file = self.config_dir / "etl_config.json"
        self.email_config_file = self.config_dir / "email_config.json"
        self.auth_config_file = self.config_dir / "auth_config.json"
        
        # โหลด configs
        self._ensure_config_files()
        self.etl_config = self._load_json(self.etl_config_file)
        self.email_config = self._load_json(self.email_config_file)
        self.auth_config = self._load_json(self.auth_config_file)
    
    def _ensure_config_files(self):
        """สร้าง config files ถ้ายังไม่มี พร้อม default values"""
        
        # ETL Config
        if not self.etl_config_file.exists():
            default_etl_config = {
                "input_path": "/path/to/input/",
                "output_path": "/path/to/output/",
                "master_path": "/path/to/master/",
                "report_path": "/path/to/reports/",
                "year": "2025",
                "reconcile_tolerance": 0.00,
                "enable_reconciliation": True,
                "schedule": {
                    "enabled": True,
                    "day_of_month": 5,  # วันที่ 5 ของทุกเดือน
                    "hour": 2,          # เวลา 02:00
                    "minute": 0
                }
            }
            self._save_json(self.etl_config_file, default_etl_config)
            logger.info(f"Created default ETL config: {self.etl_config_file}")
        
        # Email Config
        if not self.email_config_file.exists():
            default_email_config = {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "smtp_use_tls": True,
                "smtp_username": "your-email@gmail.com",
                "smtp_password": "your-app-password",
                "sender_email": "your-email@gmail.com",
                "sender_name": "Revenue ETL System",
                "otp_expiry_minutes": 10
            }
            self._save_json(self.email_config_file, default_email_config)
            logger.info(f"Created default email config: {self.email_config_file}")
        
        # Auth Config
        if not self.auth_config_file.exists():
            default_auth_config = {
                "allowed_domains": ["example.com"],  # อนุญาตเฉพาะ email @example.com
                "admin_emails": ["admin@example.com"],  # Admin users
                "session_timeout_minutes": 120,
                "max_otp_attempts": 3
            }
            self._save_json(self.auth_config_file, default_auth_config)
            logger.info(f"Created default auth config: {self.auth_config_file}")
    
    def _load_json(self, filepath: Path) -> Dict[str, Any]:
        """โหลด JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {filepath}: {e}")
            return {}
    
    def _save_json(self, filepath: Path, data: Dict[str, Any]):
        """บันทึก JSON file"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved config to {filepath}")
        except Exception as e:
            logger.error(f"Error saving {filepath}: {e}")
            raise
    
    # ========== ETL Config Methods ==========
    
    def get_etl_config(self) -> Dict[str, Any]:
        """ดึง ETL configuration ทั้งหมด"""
        return self.etl_config.copy()
    
    def update_etl_config(self, updates: Dict[str, Any]):
        """อัพเดท ETL configuration"""
        self.etl_config.update(updates)
        self._save_json(self.etl_config_file, self.etl_config)
    
    def get_etl_paths(self) -> Dict[str, str]:
        """ดึง paths สำหรับ ETL"""
        return {
            "input_path": self.etl_config.get("input_path", ""),
            "output_path": self.etl_config.get("output_path", ""),
            "master_path": self.etl_config.get("master_path", ""),
            "report_path": self.etl_config.get("report_path", "")
        }
    
    # ========== Email Config Methods ==========
    
    def get_email_config(self) -> Dict[str, Any]:
        """ดึง email configuration ทั้งหมด"""
        return self.email_config.copy()
    
    def update_email_config(self, updates: Dict[str, Any]):
        """อัพเดท email configuration"""
        self.email_config.update(updates)
        self._save_json(self.email_config_file, self.email_config)
    
    # ========== Auth Config Methods ==========
    
    def get_auth_config(self) -> Dict[str, Any]:
        """ดึง auth configuration ทั้งหมด"""
        return self.auth_config.copy()
    
    def update_auth_config(self, updates: Dict[str, Any]):
        """อัพเดท auth configuration"""
        self.auth_config.update(updates)
        self._save_json(self.auth_config_file, self.auth_config)
    
    def is_allowed_domain(self, email: str) -> bool:
        """ตรวจสอบว่า email อยู่ใน allowed domains หรือไม่"""
        allowed_domains = self.auth_config.get("allowed_domains", [])
        email_domain = email.split('@')[-1].lower()
        return email_domain in [d.lower() for d in allowed_domains]
    
    def is_admin(self, email: str) -> bool:
        """ตรวจสอบว่าเป็น admin หรือไม่"""
        admin_emails = self.auth_config.get("admin_emails", [])
        return email.lower() in [e.lower() for e in admin_emails]
    
    # ========== Schedule Config Methods ==========
    
    def get_schedule_config(self) -> Dict[str, Any]:
        """ดึง schedule configuration"""
        return self.etl_config.get("schedule", {})
    
    def update_schedule(self, updates: Dict[str, Any]):
        """อัพเดท schedule configuration"""
        if "schedule" not in self.etl_config:
            self.etl_config["schedule"] = {}
        self.etl_config["schedule"].update(updates)
        self._save_json(self.etl_config_file, self.etl_config)


class FlaskConfig:
    """
    Flask-specific configuration
    """
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Session
    PERMANENT_SESSION_LIFETIME = 7200  # 2 hours
    SESSION_COOKIE_SECURE = True  # HTTPS only
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # File upload
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max
    
    # Scheduler
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = "Asia/Bangkok"
