"""
Authentication Manager Module
==============================
จัดการ OTP-based authentication (ไม่ใช้ password)
- สร้าง OTP 6 หลัก
- ส่ง OTP ทาง email
- Verify OTP
- Session management
"""

import json
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

from config_manager import get_config_manager
from user_manager import get_user_manager


class AuthManager:
    """จัดการ authentication ผ่าน OTP"""

    def __init__(self, otps_file: str = "data/otps.json"):
        """
        Initialize AuthManager

        Args:
            otps_file: path ของไฟล์ otps.json
        """
        self.otps_file = otps_file
        self.config = get_config_manager()
        self.user_manager = get_user_manager()
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """ตรวจสอบว่าไฟล์ otps.json มีอยู่"""
        if not Path(self.otps_file).exists():
            self._save_otps({"otps": []})

    def _load_otps(self) -> Dict[str, list]:
        """โหลด OTPs จากไฟล์"""
        try:
            with open(self.otps_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"otps": []}

    def _save_otps(self, data: Dict[str, list]) -> bool:
        """บันทึก OTPs ลงไฟล์"""
        try:
            with open(self.otps_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving OTPs: {e}")
            return False

    def _cleanup_expired_otps(self):
        """ลบ OTPs ที่หมดอายุและใช้แล้ว"""
        data = self._load_otps()
        otps = data.get('otps', [])

        # Filter out expired and used OTPs
        now = datetime.now()
        active_otps = []

        for otp in otps:
            expires_at = datetime.fromisoformat(otp['expires_at'])
            # เก็บเฉพาะ OTPs ที่ยังไม่หมดอายุและยังไม่ได้ใช้
            if expires_at > now and not otp.get('used', False):
                active_otps.append(otp)

        data['otps'] = active_otps
        self._save_otps(data)

    def generate_otp(self, email: str) -> Tuple[str, datetime]:
        """
        สร้าง OTP สำหรับ email

        Args:
            email: email ของผู้ใช้

        Returns:
            Tuple[str, datetime]: (otp_code, expires_at)

        Raises:
            ValueError: ถ้าผู้ใช้ไม่พบหรือไม่ active
        """
        # ตรวจสอบว่าผู้ใช้มีอยู่และ active
        user = self.user_manager.get_user_by_email(email)
        if not user:
            raise ValueError(f"User not found: {email}")

        if not user.get('is_active', False):
            raise ValueError(f"User is not active: {email}")

        # Cleanup old OTPs
        self._cleanup_expired_otps()

        # สร้าง OTP code
        otp_config = self.config.get_otp_config()
        code_length = otp_config['code_length']
        expiry_minutes = otp_config['expiry_minutes']

        otp_code = ''.join([str(secrets.randbelow(10)) for _ in range(code_length)])

        # คำนวณเวลาหมดอายุ
        created_at = datetime.now()
        expires_at = created_at + timedelta(minutes=expiry_minutes)

        # บันทึก OTP
        data = self._load_otps()
        otp_entry = {
            "email": email.lower(),
            "otp_code": otp_code,
            "created_at": created_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "used": False
        }
        data['otps'].append(otp_entry)
        self._save_otps(data)

        return otp_code, expires_at

    def verify_otp(self, email: str, otp_code: str) -> bool:
        """
        ตรวจสอบ OTP

        Args:
            email: email ของผู้ใช้
            otp_code: OTP code ที่กรอก

        Returns:
            bool: True ถ้า OTP ถูกต้อง
        """
        self._cleanup_expired_otps()

        data = self._load_otps()
        otps = data.get('otps', [])

        now = datetime.now()

        for i, otp in enumerate(otps):
            if (otp['email'].lower() == email.lower() and
                otp['otp_code'] == otp_code and
                not otp.get('used', False)):

                # ตรวจสอบว่าหมดอายุหรือไม่
                expires_at = datetime.fromisoformat(otp['expires_at'])
                if expires_at > now:
                    # Mark as used
                    otps[i]['used'] = True
                    data['otps'] = otps
                    self._save_otps(data)

                    # Update last login
                    self.user_manager.update_last_login(email)

                    return True

        return False

    def is_valid_email_domain(self, email: str) -> bool:
        """
        ตรวจสอบว่า email domain ตรงกับที่กำหนดหรือไม่

        Args:
            email: email ที่ต้องการตรวจสอบ

        Returns:
            bool: True ถ้า domain ถูกต้อง
        """
        allowed_domain = self.config.get_allowed_email_domain()

        if '@' not in email:
            return False

        domain = email.split('@')[1]
        return domain.lower() == allowed_domain.lower()

    def normalize_email(self, email: str) -> str:
        """
        ปรับ email ให้เป็นรูปแบบมาตรฐาน
        - ถ้าไม่มี @ ให้เติม domain
        - แปลงเป็น lowercase

        Args:
            email: email input

        Returns:
            str: normalized email
        """
        email = email.strip().lower()

        # ถ้าไม่มี @ ให้เติม domain
        if '@' not in email:
            allowed_domain = self.config.get_allowed_email_domain()
            email = f"{email}@{allowed_domain}"

        return email

    def get_otp_attempts(self, email: str) -> int:
        """
        นับจำนวนครั้งที่พยายาม generate OTP

        Args:
            email: email ของผู้ใช้

        Returns:
            int: จำนวนครั้งที่พยายาม (ใน 1 ชั่วโมงล่าสุด)
        """
        data = self._load_otps()
        otps = data.get('otps', [])

        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)

        count = 0
        for otp in otps:
            if otp['email'].lower() == email.lower():
                created_at = datetime.fromisoformat(otp['created_at'])
                if created_at > one_hour_ago:
                    count += 1

        return count


# Singleton instance
_auth_manager = None


def get_auth_manager() -> AuthManager:
    """
    Get singleton AuthManager instance

    Returns:
        AuthManager: instance
    """
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager


if __name__ == "__main__":
    # Test
    auth = get_auth_manager()

    # Test normalize email
    print("Normalized:", auth.normalize_email("pornthep.n"))

    # Test email domain
    print("Valid domain:", auth.is_valid_email_domain("pornthep.n@ntplc.co.th"))

    # Test generate OTP
    try:
        otp_code, expires_at = auth.generate_otp("pornthep.n@ntplc.co.th")
        print(f"Generated OTP: {otp_code} (expires at {expires_at})")

        # Test verify OTP
        result = auth.verify_otp("pornthep.n@ntplc.co.th", otp_code)
        print(f"OTP verified: {result}")

    except ValueError as e:
        print(f"Error: {e}")
