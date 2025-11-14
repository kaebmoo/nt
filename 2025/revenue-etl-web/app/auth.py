"""
OTP Authentication System
ใช้ OTP ผ่าน email แทน password
"""

import json
import secrets
import string
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class OTPManager:
    """
    จัดการ OTP sessions แบบ JSON file
    """
    
    def __init__(self, config_manager, base_dir: str = None):
        """
        Args:
            config_manager: ConfigManager instance
            base_dir: Base directory ของ application
        """
        self.config_manager = config_manager
        
        if base_dir is None:
            base_dir = Path(__file__).parent.parent
        
        self.base_dir = Path(base_dir)
        self.sessions_dir = self.base_dir / "data" / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        
        self.otp_file = self.sessions_dir / "otp_sessions.json"
        self.login_sessions_file = self.sessions_dir / "login_sessions.json"
        
        # โหลด sessions
        self.otp_sessions = self._load_sessions(self.otp_file)
        self.login_sessions = self._load_sessions(self.login_sessions_file)
        
        # Config
        auth_config = self.config_manager.get_auth_config()
        self.otp_expiry_minutes = self.config_manager.email_config.get(
            "otp_expiry_minutes", 10
        )
        self.max_attempts = auth_config.get("max_otp_attempts", 3)
        self.session_timeout_minutes = auth_config.get("session_timeout_minutes", 120)
    
    def _load_sessions(self, filepath: Path) -> Dict[str, Any]:
        """โหลด sessions จากไฟล์"""
        if not filepath.exists():
            return {}
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading sessions from {filepath}: {e}")
            return {}
    
    def _save_sessions(self, filepath: Path, sessions: Dict[str, Any]):
        """บันทึก sessions ลงไฟล์"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(sessions, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving sessions to {filepath}: {e}")
            raise
    
    def _cleanup_expired(self):
        """ลบ sessions ที่หมดอายุ"""
        now = datetime.now()
        
        # Cleanup OTP sessions
        expired_otps = []
        for email, data in self.otp_sessions.items():
            expires_at = datetime.fromisoformat(data["expires_at"])
            if now > expires_at:
                expired_otps.append(email)
        
        for email in expired_otps:
            del self.otp_sessions[email]
            logger.info(f"Removed expired OTP for {email}")
        
        if expired_otps:
            self._save_sessions(self.otp_file, self.otp_sessions)
        
        # Cleanup login sessions
        expired_sessions = []
        for session_id, data in self.login_sessions.items():
            expires_at = datetime.fromisoformat(data["expires_at"])
            if now > expires_at:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.login_sessions[session_id]
            logger.info(f"Removed expired login session {session_id}")
        
        if expired_sessions:
            self._save_sessions(self.login_sessions_file, self.login_sessions)
    
    def generate_otp(self, length: int = 6) -> str:
        """
        สร้าง OTP แบบตัวเลข
        
        Args:
            length: ความยาวของ OTP
        
        Returns:
            OTP string
        """
        return ''.join(secrets.choice(string.digits) for _ in range(length))
    
    def create_otp_session(self, email: str) -> Tuple[str, datetime]:
        """
        สร้าง OTP session
        
        Args:
            email: User email
        
        Returns:
            (otp, expires_at)
        """
        # Cleanup expired sessions ก่อน
        self._cleanup_expired()
        
        # สร้าง OTP
        otp = self.generate_otp()
        expires_at = datetime.now() + timedelta(minutes=self.otp_expiry_minutes)
        
        # บันทึก session
        self.otp_sessions[email] = {
            "otp": otp,
            "created_at": datetime.now().isoformat(),
            "expires_at": expires_at.isoformat(),
            "attempts": 0,
            "max_attempts": self.max_attempts
        }
        
        self._save_sessions(self.otp_file, self.otp_sessions)
        
        logger.info(f"Created OTP session for {email}, expires at {expires_at}")
        return otp, expires_at
    
    def verify_otp(self, email: str, otp: str) -> Tuple[bool, str]:
        """
        ตรวจสอบ OTP
        
        Args:
            email: User email
            otp: OTP ที่กรอกมา
        
        Returns:
            (success, message)
        """
        # Cleanup expired sessions ก่อน
        self._cleanup_expired()
        
        # ตรวจสอบว่ามี session หรือไม่
        if email not in self.otp_sessions:
            return False, "ไม่พบ OTP session กรุณาขอ OTP ใหม่"
        
        session = self.otp_sessions[email]
        
        # ตรวจสอบว่าหมดอายุหรือไม่
        expires_at = datetime.fromisoformat(session["expires_at"])
        if datetime.now() > expires_at:
            del self.otp_sessions[email]
            self._save_sessions(self.otp_file, self.otp_sessions)
            return False, "OTP หมดอายุแล้ว กรุณาขอ OTP ใหม่"
        
        # ตรวจสอบจำนวนครั้งที่พยายาม
        if session["attempts"] >= session["max_attempts"]:
            del self.otp_sessions[email]
            self._save_sessions(self.otp_file, self.otp_sessions)
            return False, f"พยายามเกิน {self.max_attempts} ครั้ง กรุณาขอ OTP ใหม่"
        
        # เพิ่มจำนวนครั้งที่พยายาม
        session["attempts"] += 1
        
        # ตรวจสอบ OTP
        if session["otp"] == otp:
            # ถูกต้อง - ลบ OTP session
            del self.otp_sessions[email]
            self._save_sessions(self.otp_file, self.otp_sessions)
            logger.info(f"OTP verified successfully for {email}")
            return True, "ยืนยัน OTP สำเร็จ"
        else:
            # ไม่ถูกต้อง - บันทึกจำนวนครั้งที่พยายาม
            self._save_sessions(self.otp_file, self.otp_sessions)
            remaining = session["max_attempts"] - session["attempts"]
            return False, f"OTP ไม่ถูกต้อง เหลือโอกาสอีก {remaining} ครั้ง"
    
    def create_login_session(self, email: str) -> str:
        """
        สร้าง login session หลังจาก verify OTP สำเร็จ
        
        Args:
            email: User email
        
        Returns:
            session_id
        """
        # Cleanup expired sessions ก่อน
        self._cleanup_expired()
        
        # สร้าง session ID
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(minutes=self.session_timeout_minutes)
        
        # ตรวจสอบว่าเป็น admin หรือไม่
        is_admin = self.config_manager.is_admin(email)
        
        # บันทึก session
        self.login_sessions[session_id] = {
            "email": email,
            "is_admin": is_admin,
            "created_at": datetime.now().isoformat(),
            "expires_at": expires_at.isoformat(),
            "last_activity": datetime.now().isoformat()
        }
        
        self._save_sessions(self.login_sessions_file, self.login_sessions)
        
        logger.info(f"Created login session for {email} (admin={is_admin}), expires at {expires_at}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        ดึงข้อมูล session
        
        Args:
            session_id: Session ID
        
        Returns:
            Session data หรือ None ถ้าไม่พบหรือหมดอายุ
        """
        # Cleanup expired sessions ก่อน
        self._cleanup_expired()
        
        if session_id not in self.login_sessions:
            return None
        
        session = self.login_sessions[session_id]
        
        # ตรวจสอบว่าหมดอายุหรือไม่
        expires_at = datetime.fromisoformat(session["expires_at"])
        if datetime.now() > expires_at:
            del self.login_sessions[session_id]
            self._save_sessions(self.login_sessions_file, self.login_sessions)
            return None
        
        # อัพเดท last_activity
        session["last_activity"] = datetime.now().isoformat()
        self._save_sessions(self.login_sessions_file, self.login_sessions)
        
        return session
    
    def delete_session(self, session_id: str):
        """
        ลบ session (logout)
        
        Args:
            session_id: Session ID
        """
        if session_id in self.login_sessions:
            email = self.login_sessions[session_id]["email"]
            del self.login_sessions[session_id]
            self._save_sessions(self.login_sessions_file, self.login_sessions)
            logger.info(f"Deleted login session for {email}")
    
    def validate_email(self, email: str) -> Tuple[bool, str]:
        """
        ตรวจสอบความถูกต้องของ email
        
        Args:
            email: Email address
        
        Returns:
            (valid, message)
        """
        # ตรวจสอบ format พื้นฐาน
        if '@' not in email or '.' not in email.split('@')[1]:
            return False, "รูปแบบ email ไม่ถูกต้อง"
        
        # ตรวจสอบ allowed domains
        if not self.config_manager.is_allowed_domain(email):
            allowed_domains = self.config_manager.auth_config.get("allowed_domains", [])
            return False, f"อนุญาตเฉพาะ email จาก domain: {', '.join(allowed_domains)}"
        
        return True, "Email ถูกต้อง"
