"""
Input Validators
"""

import re
from typing import Tuple


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validate email format
    
    Args:
        email: Email address
    
    Returns:
        (is_valid, message)
    """
    if not email:
        return False, "กรุณากรอก email"
    
    # Basic email pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        return False, "รูปแบบ email ไม่ถูกต้อง"
    
    return True, "OK"


def validate_otp(otp: str) -> Tuple[bool, str]:
    """
    Validate OTP format
    
    Args:
        otp: OTP code
    
    Returns:
        (is_valid, message)
    """
    if not otp:
        return False, "กรุณากรอก OTP"
    
    # ต้องเป็นตัวเลข 6 หลัก
    if not otp.isdigit():
        return False, "OTP ต้องเป็นตัวเลขเท่านั้น"
    
    if len(otp) != 6:
        return False, "OTP ต้องเป็นตัวเลข 6 หลัก"
    
    return True, "OK"


def validate_year(year: str) -> Tuple[bool, str]:
    """
    Validate year format
    
    Args:
        year: Year string
    
    Returns:
        (is_valid, message)
    """
    if not year:
        return False, "กรุณากรอกปี"
    
    if not year.isdigit():
        return False, "ปีต้องเป็นตัวเลขเท่านั้น"
    
    if len(year) != 4:
        return False, "ปีต้องเป็นตัวเลข 4 หลัก"
    
    year_int = int(year)
    if not 2000 <= year_int <= 2100:
        return False, "ปีต้องอยู่ระหว่าง 2000-2100"
    
    return True, "OK"


def validate_month(month: str) -> Tuple[bool, str]:
    """
    Validate month format
    
    Args:
        month: Month string (1-12)
    
    Returns:
        (is_valid, message)
    """
    if not month:
        return True, "OK"  # Month is optional
    
    if not month.isdigit():
        return False, "เดือนต้องเป็นตัวเลขเท่านั้น"
    
    month_int = int(month)
    if not 1 <= month_int <= 12:
        return False, "เดือนต้องอยู่ระหว่าง 1-12"
    
    return True, "OK"


def validate_path(path: str) -> Tuple[bool, str]:
    """
    Validate file path
    
    Args:
        path: File path
    
    Returns:
        (is_valid, message)
    """
    if not path:
        return False, "กรุณากรอก path"
    
    # ตรวจสอบ characters ที่อันตราย
    dangerous_chars = ['..', ';', '|', '&', '$', '`']
    for char in dangerous_chars:
        if char in path:
            return False, f"Path ประกอบด้วย characters ที่ไม่อนุญาต: {char}"
    
    return True, "OK"


def sanitize_filename(filename: str) -> str:
    """
    ทำความสะอาด filename เพื่อความปลอดภัย
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename
    """
    # เอาเฉพาะตัวอักษร ตัวเลข . - _
    sanitized = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
    return sanitized
