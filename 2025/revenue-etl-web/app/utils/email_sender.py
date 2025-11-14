"""
Email Sender สำหรับส่ง OTP
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EmailSender:
    """
    จัดการการส่ง email ผ่าน SMTP
    """
    
    def __init__(self, config_manager):
        """
        Args:
            config_manager: ConfigManager instance
        """
        self.config_manager = config_manager
        self.email_config = config_manager.get_email_config()
    
    def send_otp_email(self, to_email: str, otp: str, expires_at: datetime) -> bool:
        """
        ส่ง OTP email
        
        Args:
            to_email: Recipient email
            otp: OTP code
            expires_at: OTP expiration time
        
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # สร้าง message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = 'OTP สำหรับเข้าสู่ระบบ Revenue ETL'
            msg['From'] = f"{self.email_config['sender_name']} <{self.email_config['sender_email']}>"
            msg['To'] = to_email
            
            # สร้าง email body
            expires_str = expires_at.strftime('%H:%M น. วันที่ %d/%m/%Y')
            
            text_body = f"""
สวัสดีครับ/ค่ะ

รหัส OTP สำหรับเข้าสู่ระบบ Revenue ETL ของคุณคือ:

{otp}

รหัสนี้จะหมดอายุเวลา {expires_str}

*** กรุณาอย่าแชร์รหัสนี้กับผู้อื่น ***

หากคุณไม่ได้ขอรหัสนี้ กรุณาเพิกเฉยต่ออีเมลนี้

ขอแสดงความนับถือ
ระบบ Revenue ETL
"""
            
            html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: 'Sarabun', 'Tahoma', sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
        }}
        .content {{
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .otp {{
            font-size: 32px;
            font-weight: bold;
            color: #2563eb;
            text-align: center;
            padding: 20px;
            margin: 20px 0;
            background-color: #eff6ff;
            border-radius: 8px;
            letter-spacing: 8px;
        }}
        .warning {{
            color: #dc2626;
            font-weight: bold;
            text-align: center;
            margin: 20px 0;
        }}
        .footer {{
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
            font-size: 14px;
            color: #6b7280;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="content">
            <h2 style="color: #1f2937;">🔐 รหัส OTP สำหรับเข้าสู่ระบบ</h2>
            <p>สวัสดีครับ/ค่ะ</p>
            <p>รหัส OTP สำหรับเข้าสู่ระบบ Revenue ETL ของคุณคือ:</p>
            
            <div class="otp">{otp}</div>
            
            <p style="text-align: center;">
                <strong>หมดอายุเวลา:</strong> {expires_str}
            </p>
            
            <div class="warning">
                ⚠️ กรุณาอย่าแชร์รหัสนี้กับผู้อื่น
            </div>
            
            <div class="footer">
                <p>หากคุณไม่ได้ขอรหัสนี้ กรุณาเพิกเฉยต่ออีเมลนี้</p>
                <p>ขอแสดงความนับถือ<br>ระบบ Revenue ETL</p>
            </div>
        </div>
    </div>
</body>
</html>
"""
            
            # Attach parts
            part1 = MIMEText(text_body, 'plain', 'utf-8')
            part2 = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(part1)
            msg.attach(part2)
            
            # ส่ง email
            with smtplib.SMTP(
                self.email_config['smtp_server'], 
                self.email_config['smtp_port']
            ) as server:
                if self.email_config.get('smtp_use_tls', True):
                    server.starttls()
                
                server.login(
                    self.email_config['smtp_username'],
                    self.email_config['smtp_password']
                )
                
                server.send_message(msg)
            
            logger.info(f"OTP email sent successfully to {to_email}")
            return True
        
        except Exception as e:
            logger.error(f"Error sending OTP email to {to_email}: {e}")
            return False
    
    def send_report_notification(self, to_email: str, report_name: str, 
                                 report_period: str) -> bool:
        """
        ส่ง email แจ้งเตือนว่ามีรายงานใหม่
        
        Args:
            to_email: Recipient email
            report_name: Report filename
            report_period: Report period (e.g., "ตุลาคม 2025")
        
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f'รายงานรายได้ {report_period} พร้อมแล้ว'
            msg['From'] = f"{self.email_config['sender_name']} <{self.email_config['sender_email']}>"
            msg['To'] = to_email
            
            text_body = f"""
สวัสดีครับ/ค่ะ

รายงานรายได้ประจำเดือน {report_period} ได้ถูกสร้างเรียบร้อยแล้ว

ชื่อไฟล์: {report_name}

คุณสามารถเข้าสู่ระบบเพื่อดาวน์โหลดรายงานได้ที่:
[URL ของ web app]

ขอแสดงความนับถือ
ระบบ Revenue ETL
"""
            
            html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: 'Sarabun', 'Tahoma', sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
        }}
        .content {{
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .report-box {{
            background-color: #f0fdf4;
            border-left: 4px solid #22c55e;
            padding: 15px;
            margin: 20px 0;
        }}
        .footer {{
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
            font-size: 14px;
            color: #6b7280;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="content">
            <h2 style="color: #1f2937;">✅ รายงานพร้อมแล้ว</h2>
            <p>สวัสดีครับ/ค่ะ</p>
            <p>รายงานรายได้ประจำเดือน <strong>{report_period}</strong> ได้ถูกสร้างเรียบร้อยแล้ว</p>
            
            <div class="report-box">
                <p style="margin: 0;"><strong>📊 ชื่อไฟล์:</strong> {report_name}</p>
            </div>
            
            <p>คุณสามารถเข้าสู่ระบบเพื่อดาวน์โหลดรายงานได้ที่:</p>
            <p style="text-align: center;">
                <a href="[URL]" style="display: inline-block; padding: 12px 24px; background-color: #2563eb; color: white; text-decoration: none; border-radius: 6px; font-weight: bold;">
                    เข้าสู่ระบบ
                </a>
            </p>
            
            <div class="footer">
                <p>ขอแสดงความนับถือ<br>ระบบ Revenue ETL</p>
            </div>
        </div>
    </div>
</body>
</html>
"""
            
            part1 = MIMEText(text_body, 'plain', 'utf-8')
            part2 = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(part1)
            msg.attach(part2)
            
            # ส่ง email
            with smtplib.SMTP(
                self.email_config['smtp_server'], 
                self.email_config['smtp_port']
            ) as server:
                if self.email_config.get('smtp_use_tls', True):
                    server.starttls()
                
                server.login(
                    self.email_config['smtp_username'],
                    self.email_config['smtp_password']
                )
                
                server.send_message(msg)
            
            logger.info(f"Report notification sent to {to_email}")
            return True
        
        except Exception as e:
            logger.error(f"Error sending notification to {to_email}: {e}")
            return False
