"""
Logger Utilities
=================
Centralized logging system สำหรับ Revenue ETL System
บันทึก log ทั้ง console และ file พร้อมกัน

Author: Revenue ETL System
Version: 1.0.0
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class ETLLogger:
    """
    Centralized Logger สำหรับระบบ Revenue ETL
    - บันทึก log ทั้ง console และ file
    - รองรับหลาย level (DEBUG, INFO, WARNING, ERROR, SUCCESS)
    - สร้าง log file ต่อวัน
    """

    _instances = {}  # Singleton per module

    def __init__(self, name: str, log_dir: str = "logs", enable_file_logging: bool = True):
        """
        Initialize Logger

        Args:
            name: ชื่อ module (เช่น 'fi_module', 'etl_module')
            log_dir: โฟลเดอร์สำหรับเก็บ log files
            enable_file_logging: เปิด/ปิด การบันทึกลงไฟล์
        """
        self.name = name
        self.log_dir = Path(log_dir)
        self.enable_file_logging = enable_file_logging

        # สร้าง logger instance
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # ป้องกันการ duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()

    def _setup_handlers(self):
        """ตั้งค่า handlers สำหรับ console และ file"""

        # Format สำหรับ log messages
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Console Handler (แสดงบน terminal)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # File Handler (บันทึกลงไฟล์)
        if self.enable_file_logging:
            self.log_dir.mkdir(parents=True, exist_ok=True)

            # สร้างชื่อไฟล์ตามวันที่
            today = datetime.now().strftime('%Y%m%d')
            log_file = self.log_dir / f"{self.name}_{today}.log"

            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)  # บันทึกทุก level ลงไฟล์
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def debug(self, message: str):
        """Log level DEBUG"""
        self.logger.debug(message)

    def info(self, message: str):
        """Log level INFO"""
        self.logger.info(message)

    def warning(self, message: str):
        """Log level WARNING"""
        self.logger.warning(message)

    def error(self, message: str):
        """Log level ERROR"""
        self.logger.error(message)

    def success(self, message: str):
        """Log level SUCCESS (custom - ใช้ INFO)"""
        # ใช้ INFO level แต่เพิ่มเครื่องหมาย ✓
        self.logger.info(f"✓ {message}")

    def log(self, message: str, level: str = "INFO"):
        """
        Log message with specified level

        Args:
            message: ข้อความที่ต้องการ log
            level: ระดับของ log (INFO, WARNING, ERROR, SUCCESS, DEBUG)
        """
        level = level.upper()

        if level == "DEBUG":
            self.debug(message)
        elif level == "INFO":
            self.info(message)
        elif level == "WARNING":
            self.warning(message)
        elif level == "ERROR":
            self.error(message)
        elif level == "SUCCESS":
            self.success(message)
        else:
            self.info(message)

    @classmethod
    def get_logger(cls, name: str, log_dir: str = "logs", enable_file_logging: bool = True) -> 'ETLLogger':
        """
        Factory method สำหรับดึง logger instance (Singleton pattern)

        Args:
            name: ชื่อ module
            log_dir: โฟลเดอร์สำหรับเก็บ log files
            enable_file_logging: เปิด/ปิด การบันทึกลงไฟล์

        Returns:
            ETLLogger instance
        """
        if name not in cls._instances:
            cls._instances[name] = cls(name, log_dir, enable_file_logging)
        return cls._instances[name]


def setup_logging(config: dict) -> ETLLogger:
    """
    Setup logging จาก configuration

    Args:
        config: Configuration dictionary

    Returns:
        ETLLogger instance สำหรับ main system
    """
    logging_config = config.get('logging', {})

    log_dir = logging_config.get('log_directory', 'logs')
    enable_file_logging = logging_config.get('enable_file_logging', True)

    # สร้าง main logger
    logger = ETLLogger.get_logger('system', log_dir, enable_file_logging)

    return logger


if __name__ == "__main__":
    # ทดสอบ logger
    logger = ETLLogger.get_logger('test_module')

    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.success("This is a success message")
    logger.debug("This is a debug message")

    print(f"\n✓ Log file created at: logs/test_module_{datetime.now().strftime('%Y%m%d')}.log")
