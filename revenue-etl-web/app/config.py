"""
Configuration Management System
Handles JSON-based configuration files for ETL, Email, and Authentication
"""

import os
import json
from pathlib import Path
from typing import Dict, Any


class ConfigManager:
    """Manages application configuration from JSON files"""

    def __init__(self, config_dir: str = "data/config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Configuration file paths
        self.etl_config_path = self.config_dir / "etl_config.json"
        self.email_config_path = self.config_dir / "email_config.json"
        self.auth_config_path = self.config_dir / "auth_config.json"

        # Initialize configs
        self._init_configs()

    def _init_configs(self):
        """Initialize configuration files with defaults if they don't exist"""
        # ETL Configuration
        if not self.etl_config_path.exists():
            default_etl = {
                "paths": {
                    "data_input": "/path/to/input/data",
                    "master_files": "/path/to/master/files",
                    "output": "reports",
                    "etl_scripts": "etl"
                },
                "schedule": {
                    "enabled": False,
                    "day_of_month": 10,
                    "hour": 2,
                    "minute": 0,
                    "timezone": "Asia/Bangkok"
                },
                "scripts": {
                    "fi_revenue_expense": "fi_revenue_expense.py",
                    "revenue_etl_report": "revenue_etl_report.py",
                    "revenue_reconciliation": "revenue_reconciliation.py"
                },
                "notifications": {
                    "enabled": True,
                    "on_success": True,
                    "on_failure": True,
                    "recipients": []
                }
            }
            self._save_config(self.etl_config_path, default_etl)

        # Email Configuration
        if not self.email_config_path.exists():
            default_email = {
                "smtp": {
                    "host": "mail.example.com",
                    "port": 587,
                    "use_tls": True,
                    "username": "noreply@example.com",
                    "password": ""
                },
                "sender": {
                    "name": "Revenue ETL System",
                    "email": "noreply@example.com"
                },
                "otp": {
                    "length": 6,
                    "expiry_minutes": 10
                }
            }
            self._save_config(self.email_config_path, default_email)

        # Authentication Configuration
        if not self.auth_config_path.exists():
            default_auth = {
                "allowed_domains": [
                    "example.com"
                ],
                "admin_emails": [
                    "admin@example.com"
                ],
                "session": {
                    "timeout_minutes": 60
                }
            }
            self._save_config(self.auth_config_path, default_auth)

    def _load_config(self, path: Path) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config from {path}: {e}")
            return {}

    def _save_config(self, path: Path, config: Dict[str, Any]):
        """Save configuration to JSON file"""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config to {path}: {e}")

    # ETL Configuration
    def get_etl_config(self) -> Dict[str, Any]:
        """Get ETL configuration"""
        return self._load_config(self.etl_config_path)

    def update_etl_config(self, config: Dict[str, Any]):
        """Update ETL configuration"""
        self._save_config(self.etl_config_path, config)

    # Email Configuration
    def get_email_config(self) -> Dict[str, Any]:
        """Get email configuration"""
        return self._load_config(self.email_config_path)

    def update_email_config(self, config: Dict[str, Any]):
        """Update email configuration"""
        self._save_config(self.email_config_path, config)

    # Authentication Configuration
    def get_auth_config(self) -> Dict[str, Any]:
        """Get authentication configuration"""
        return self._load_config(self.auth_config_path)

    def update_auth_config(self, config: Dict[str, Any]):
        """Update authentication configuration"""
        self._save_config(self.auth_config_path, config)

    # Helper methods
    def is_allowed_domain(self, email: str) -> bool:
        """Check if email domain is allowed"""
        auth_config = self.get_auth_config()
        domain = email.split('@')[-1] if '@' in email else ''
        return domain in auth_config.get('allowed_domains', [])

    def is_admin(self, email: str) -> bool:
        """Check if email is an admin"""
        auth_config = self.get_auth_config()
        return email in auth_config.get('admin_emails', [])
