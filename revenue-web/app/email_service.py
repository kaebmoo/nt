# email_service.py
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr
import os
import logging
import traceback

logger = logging.getLogger(__name__)

class EmailService:
    """Email service using SMTP SSL"""
    
    def __init__(self):
        self.smtp_server = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
        self.port = int(os.environ.get('MAIL_PORT', 465))
        
        # ✅ แก้ไข: กำหนดค่าเริ่มต้นเป็นสตริงว่าง '' เพื่อให้เป็น str เสมอ
        self.sender_email = os.environ.get('MAIL_USERNAME', '')
        self.sender_password = os.environ.get('MAIL_PASSWORD', '')
        self.sender_name = os.environ.get('MAIL_FROM_NAME', 'Meeting Registration System')
        self.sender_from_address = os.environ.get('MAIL_FROM', self.sender_email)

        # เพิ่มการตรวจสอบว่ามีการตั้งค่าที่จำเป็นหรือไม่
        if not self.sender_email or not self.sender_password:
            logger.critical("CRITICAL: MAIL_USERNAME and MAIL_PASSWORD must be set in environment variables.")
        
    def send_otp_email(self, recipient_email: str, recipient_name: str, otp: str, purpose: str = 'login'):
        """Send OTP email with proper encoding"""
        
        # ตรวจสอบค่า config ก่อนส่ง
        if not self.sender_email or not self.sender_password:
            logger.error("Cannot send email because sender credentials are not configured.")
            return False

        try:
            message = MIMEMultipart('alternative')
            
            if purpose == 'register':
                subject = "ยืนยัน Email - ระบบลงทะเบียนการประชุม"
            else:
                subject = "เข้าสู่ระบบ - รหัส OTP"
            
            # ✅ แก้ไข: แปลง Header object เป็น string ด้วย str() เพื่อให้ Type Checker พอใจ
            message["Subject"] = str(Header(subject, 'utf-8'))
            
            # ✅ แก้ไข: ไม่ต้อง .encode() ที่ Header เพราะ formataddr จะจัดการให้เอง
            # และมั่นใจแล้วว่า self.sender_email เป็น str
            message["From"] = formataddr((self.sender_name, self.sender_from_address))
            message["To"] = formataddr((recipient_name or recipient_email, recipient_email))
            
            # Plain text version
            text_content = f"""
สวัสดี {recipient_name or 'คุณ'},

รหัส OTP ของคุณคือ: {otp}

รหัสนี้จะหมดอายุใน 10 นาที
กรุณาอย่าแชร์รหัสนี้กับผู้อื่น

ขอบคุณ,
ระบบลงทะเบียนการประชุม
            """
            
            # HTML version
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Sarabun', Arial, sans-serif; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #2185d0; color: white; padding: 20px; text-align: center; border-radius: 5px; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .otp-code {{ 
            font-size: 32px; 
            font-weight: bold; 
            color: #2185d0; 
            text-align: center; 
            padding: 20px;
            background-color: white;
            border: 2px dashed #2185d0;
            margin: 20px 0;
            letter-spacing: 5px;
            border-radius: 5px;
        }}
        .footer {{ text-align: center; padding: 10px; color: #666; font-size: 12px; }}
        .warning {{ color: #ff6b6b; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>{'ยืนยัน Email' if purpose == 'register' else 'เข้าสู่ระบบ'}</h2>
        </div>
        <div class="content">
            <p>สวัสดี <strong>{recipient_name or 'คุณ'}</strong>,</p>
            <p>รหัส OTP ของคุณคือ:</p>
            <div class="otp-code">{otp}</div>
            <p>⏱️ <span class="warning">รหัสนี้จะหมดอายุใน 10 นาที</span></p>
            <p>🔒 กรุณาอย่าแชร์รหัสนี้กับผู้อื่น</p>
        </div>
        <div class="footer">
            <p>ขอบคุณที่ใช้บริการ<br>ระบบลงทะเบียนการประชุม</p>
            <p>อีเมลนี้ส่งถึง: {recipient_email}</p>
        </div>
    </div>
</body>
</html>
            """
            
            part1 = MIMEText(text_content, 'plain', 'utf-8')
            part2 = MIMEText(html_content, 'html', 'utf-8')
            
            message.attach(part1)
            message.attach(part2)
            
            context = ssl.create_default_context()
            
            with smtplib.SMTP_SSL(self.smtp_server, self.port, context=context) as server:
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)
                
            logger.info(f"✅ OTP email sent to: {recipient_email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ SMTP Authentication failed. Check MAIL_USERNAME and MAIL_PASSWORD. Error: {str(e)}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"❌ SMTP error for {recipient_email}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to send email to {recipient_email}: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    def test_connection(self):
        """Test SMTP connection"""
        if not self.sender_email or not self.sender_password:
            logger.error("Cannot test connection because sender credentials are not configured.")
            return False
            
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(self.smtp_server, self.port, context=context) as server:
                server.ehlo()
                server.login(self.sender_email, self.sender_password)
                logger.info("✅ SMTP connection successful")
                return True
        except Exception as e:
            logger.error(f"❌ SMTP connection failed: {str(e)}")
            return False
