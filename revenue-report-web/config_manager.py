"""
Config Manager Module
=====================
จัดการ configuration จาก config.json และ .env
รองรับการแก้ไข config ผ่าน web interface (admin only)
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ConfigManager:
    """จัดการ configuration files"""

    def __init__(self, config_file: str = "config.json"):
        """
        Initialize ConfigManager

        Args:
            config_file: ชื่อไฟล์ config (default: config.json)
        """
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """โหลด configuration จาก JSON file"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Merge with environment variables
            config = self._merge_env_vars(config)

            return config
        except FileNotFoundError:
            raise FileNotFoundError(f"Config file not found: {self.config_file}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")

    def _merge_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """ผสาน environment variables เข้ากับ config"""

        # Override with environment variables
        if os.getenv('DEV_MODE') is not None:
            config['app']['dev_mode'] = os.getenv('DEV_MODE', 'True').lower() == 'true'

        # SMTP credentials จาก .env
        if 'email' in config:
            config['email']['smtp_username'] = os.getenv('SMTP_USERNAME', '')
            config['email']['smtp_password'] = os.getenv('SMTP_PASSWORD', '')

        # Admin emails
        admin_emails = os.getenv('ADMIN_EMAILS', '').split(',')
        config['admin_emails'] = [email.strip() for email in admin_emails if email.strip()]

        # Secret key
        config['secret_key'] = os.getenv('SECRET_KEY', 'default-secret-key')

        return config

    def save_config(self, new_config: Dict[str, Any]) -> bool:
        """
        บันทึก configuration ลง JSON file
        (ไม่บันทึก sensitive data เช่น passwords)

        Args:
            new_config: configuration ใหม่

        Returns:
            bool: True ถ้าบันทึกสำเร็จ
        """
        try:
            # Remove sensitive data before saving
            config_to_save = new_config.copy()

            if 'email' in config_to_save:
                # ไม่บันทึก credentials ลง JSON (เก็บใน .env เท่านั้น)
                config_to_save['email'].pop('smtp_username', None)
                config_to_save['email'].pop('smtp_password', None)

            # ไม่บันทึก admin_emails และ secret_key (อยู่ใน .env)
            config_to_save.pop('admin_emails', None)
            config_to_save.pop('secret_key', None)

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=2, ensure_ascii=False)

            # Reload config
            self.config = self.load_config()

            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        ดึงค่า config ด้วย dot notation

        Args:
            key_path: เช่น 'app.name', 'paths.reports_base_path'
            default: ค่า default ถ้าไม่พบ

        Returns:
            ค่าจาก config หรือ default
        """
        keys = key_path.split('.')
        value = self.config

        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key_path: str, value: Any) -> bool:
        """
        ตั้งค่า config ด้วย dot notation

        Args:
            key_path: เช่น 'app.dev_mode', 'paths.reports_year'
            value: ค่าที่ต้องการตั้ง

        Returns:
            bool: True ถ้าสำเร็จ
        """
        keys = key_path.split('.')
        config = self.config

        try:
            # Navigate to the parent
            for key in keys[:-1]:
                if key not in config:
                    config[key] = {}
                config = config[key]

            # Set the value
            config[keys[-1]] = value

            return True
        except Exception as e:
            print(f"Error setting config: {e}")
            return False

    def get_reports_path(self) -> str:
        """
        สร้าง full path ของ reports directory

        Returns:
            str: Full path ของ reports
        """
        base_path = self.get('paths.reports_base_path', '')
        year = self.get('paths.reports_year', '2025')
        relative_path = self.get('paths.reports_relative_path', 'all/revenue/{year}')

        # Replace {year} placeholder
        relative_path = relative_path.replace('{year}', year)

        full_path = os.path.join(base_path, relative_path)
        return full_path

    def is_dev_mode(self) -> bool:
        """ตรวจสอบว่าอยู่ใน dev mode หรือไม่"""
        return self.get('app.dev_mode', False)

    def get_allowed_email_domain(self) -> str:
        """ดึง email domain ที่อนุญาต"""
        return self.get('app.allowed_email_domain', 'ntplc.co.th')

    def get_admin_emails(self) -> list:
        """ดึงรายชื่อ admin emails"""
        return self.get('admin_emails', [])

    def get_smtp_config(self) -> Dict[str, Any]:
        """ดึง SMTP configuration"""
        return {
            'server': self.get('email.smtp_server', ''),
            'port': self.get('email.smtp_port', 465),
            'username': self.get('email.smtp_username', ''),
            'password': self.get('email.smtp_password', ''),
            'use_ssl': self.get('email.use_ssl', True),
            'from_email': self.get('email.from_email', ''),
            'sender_name': self.get('email.sender_name', '')
        }

    def get_otp_config(self) -> Dict[str, Any]:
        """ดึง OTP configuration"""
        return {
            'code_length': self.get('otp.code_length', 6),
            'expiry_minutes': self.get('otp.expiry_minutes', 5),
            'max_attempts': self.get('otp.max_attempts', 3)
        }


# Singleton instance
_config_manager = None


def get_config_manager() -> ConfigManager:
    """
    Get singleton ConfigManager instance

    Returns:
        ConfigManager: instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


if __name__ == "__main__":
    # Test
    config = get_config_manager()

    print("App Name:", config.get('app.name'))
    print("Dev Mode:", config.is_dev_mode())
    print("Reports Path:", config.get_reports_path())
    print("Admin Emails:", config.get_admin_emails())
    print("SMTP Server:", config.get('email.smtp_server'))
