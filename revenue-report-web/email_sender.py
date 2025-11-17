"""
Email Sender Module
===================
ส่ง email พร้อม Excel file attachments
รองรับ Dev Mode (แสดงเนื้อหาแทนการส่งจริง)
"""

import smtplib
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from config_manager import get_config_manager


class EmailSender:
    """จัดการส่ง email พร้อม attachments"""

    def __init__(self, log_file: str = "data/email_logs.json"):
        """
        Initialize EmailSender

        Args:
            log_file: path ของไฟล์ log
        """
        self.log_file = log_file
        self.config = get_config_manager()
        self._ensure_log_file()

    def _ensure_log_file(self):
        """ตรวจสอบว่าไฟล์ log มีอยู่"""
        if not Path(self.log_file).exists():
            self._save_logs({"emails": []})

    def _load_logs(self) -> Dict[str, list]:
        """โหลด email logs จากไฟล์"""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"emails": []}

    def _save_logs(self, data: Dict[str, list]) -> bool:
        """บันทึก email logs ลงไฟล์"""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving email logs: {e}")
            return False

    def _log_email(self, to_emails: List[str], subject: str,
                   attachments: List[str], status: str, error: str = None):
        """
        บันทึก log การส่ง email

        Args:
            to_emails: รายชื่อผู้รับ
            subject: หัวเรื่อง
            attachments: รายชื่อไฟล์แนบ
            status: สถานะ (sent/failed/dev_mode)
            error: ข้อความ error (ถ้ามี)
        """
        data = self._load_logs()

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "to": to_emails,
            "subject": subject,
            "attachments": attachments,
            "status": status,
            "error": error
        }

        data['emails'].append(log_entry)
        self._save_logs(data)

    def create_html_email(self, subject: str, body_html: str,
                         recipient_name: str = None) -> str:
        """
        สร้าง HTML email template

        Args:
            subject: หัวเรื่อง
            body_html: เนื้อหา HTML
            recipient_name: ชื่อผู้รับ (optional)

        Returns:
            str: HTML email
        """
        greeting = f"สวัสดีครับคุณ {recipient_name}" if recipient_name else "สวัสดีครับ"

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: 'Sarabun', 'Arial', sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background-color: #0066cc;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 5px 5px 0 0;
        }}
        .content {{
            background-color: #f9f9f9;
            padding: 20px;
            border: 1px solid #ddd;
        }}
        .footer {{
            background-color: #f1f1f1;
            padding: 15px;
            text-align: center;
            font-size: 12px;
            color: #666;
            border-radius: 0 0 5px 5px;
        }}
        .attachment-info {{
            background-color: #e8f4f8;
            padding: 10px;
            margin: 10px 0;
            border-left: 4px solid #0066cc;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>{subject}</h2>
        </div>
        <div class="content">
            <p>{greeting},</p>
            {body_html}
        </div>
        <div class="footer">
            <p>Email นี้ส่งโดยระบบ Revenue Report Distribution System</p>
            <p>กรุณาอย่า reply email นี้</p>
        </div>
    </div>
</body>
</html>
        """
        return html

    def send_email(self, to_emails: List[str], subject: str,
                   body_html: str, attachments: List[str] = None,
                   recipient_name: str = None) -> Dict[str, Any]:
        """
        ส่ง email พร้อม attachments

        Args:
            to_emails: รายชื่อ email ผู้รับ
            subject: หัวเรื่อง
            body_html: เนื้อหา HTML
            attachments: รายชื่อ path ของไฟล์แนบ
            recipient_name: ชื่อผู้รับ (สำหรับ greeting)

        Returns:
            Dict: {"success": bool, "message": str, "dev_mode": bool}
        """
        if attachments is None:
            attachments = []

        # ตรวจสอบว่าอยู่ใน dev mode หรือไม่
        dev_mode = self.config.is_dev_mode()

        smtp_config = self.config.get_smtp_config()

        # Validate SMTP configuration
        if not all([smtp_config['server'], smtp_config['username'], smtp_config['password']]):
            error_msg = "SMTP configuration incomplete (missing server/username/password)"
            self._log_email(to_emails, subject, attachments, "failed", error_msg)
            return {
                "success": False,
                "message": error_msg,
                "dev_mode": dev_mode
            }

        # สร้าง email message
        try:
            msg = MIMEMultipart()
            msg['From'] = f"{smtp_config['sender_name']} <{smtp_config['from_email']}>"
            msg['To'] = ", ".join(to_emails)
            msg['Subject'] = subject

            # สร้าง HTML body
            html_content = self.create_html_email(subject, body_html, recipient_name)
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))

            # แนบไฟล์
            attached_files = []
            for file_path in attachments:
                if Path(file_path).exists():
                    with open(file_path, 'rb') as f:
                        part = MIMEApplication(f.read(), Name=Path(file_path).name)
                    part['Content-Disposition'] = f'attachment; filename="{Path(file_path).name}"'
                    msg.attach(part)
                    attached_files.append(Path(file_path).name)
                else:
                    print(f"Warning: Attachment not found: {file_path}")

            # Dev Mode: แสดงเนื้อหาแทนการส่งจริง
            if dev_mode:
                print("\n" + "="*80)
                print("📧 DEV MODE - Email Preview (ไม่ได้ส่งจริง)")
                print("="*80)
                print(f"From: {msg['From']}")
                print(f"To: {msg['To']}")
                print(f"Subject: {subject}")
                print(f"Attachments: {', '.join(attached_files) if attached_files else 'None'}")
                print("-"*80)
                print("Body Preview:")
                print(body_html[:500] + "..." if len(body_html) > 500 else body_html)
                print("="*80 + "\n")

                self._log_email(to_emails, subject, attached_files, "dev_mode")

                return {
                    "success": True,
                    "message": f"✓ Dev Mode: Email preview displayed (ไม่ได้ส่งจริง)",
                    "dev_mode": True,
                    "preview": {
                        "from": msg['From'],
                        "to": to_emails,
                        "subject": subject,
                        "attachments": attached_files
                    }
                }

            # Production Mode: ส่ง email จริง
            with smtplib.SMTP_SSL(smtp_config['server'], smtp_config['port']) as server:
                server.login(smtp_config['username'], smtp_config['password'])
                server.send_message(msg)

            self._log_email(to_emails, subject, attached_files, "sent")

            return {
                "success": True,
                "message": f"✓ Email sent successfully to {len(to_emails)} recipient(s)",
                "dev_mode": False,
                "sent_to": to_emails,
                "attachments": attached_files
            }

        except smtplib.SMTPAuthenticationError:
            error_msg = "SMTP authentication failed (check username/password)"
            self._log_email(to_emails, subject, attachments, "failed", error_msg)
            return {
                "success": False,
                "message": error_msg,
                "dev_mode": dev_mode
            }
        except smtplib.SMTPException as e:
            error_msg = f"SMTP error: {str(e)}"
            self._log_email(to_emails, subject, attachments, "failed", error_msg)
            return {
                "success": False,
                "message": error_msg,
                "dev_mode": dev_mode
            }
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self._log_email(to_emails, subject, attachments, "failed", error_msg)
            return {
                "success": False,
                "message": error_msg,
                "dev_mode": dev_mode
            }

    def send_otp_email(self, to_email: str, otp_code: str, expires_at: datetime) -> Dict[str, Any]:
        """
        ส่ง OTP email

        Args:
            to_email: email ผู้รับ
            otp_code: OTP code
            expires_at: เวลาหมดอายุ

        Returns:
            Dict: result จาก send_email()
        """
        # Format expiry time
        expiry_str = expires_at.strftime("%H:%M:%S")

        subject = "Your OTP Code - Revenue Report System"

        body_html = f"""
        <p>รหัส OTP ของคุณคือ:</p>
        <div style="background-color: #e8f4f8; padding: 20px; text-align: center; font-size: 24px; font-weight: bold; letter-spacing: 5px; margin: 20px 0;">
            {otp_code}
        </div>
        <p><strong>⏰ รหัสนี้จะหมดอายุเวลา: {expiry_str}</strong></p>
        <p style="color: #d9534f;">⚠️ กรุณาอย่าแชร์รหัส OTP นี้กับผู้อื่น</p>
        <p>หากคุณไม่ได้ร้องขอรหัสนี้ กรุณาเพิกเฉยต่อ email นี้</p>
        """

        return self.send_email([to_email], subject, body_html)

    def send_report_email(self, to_emails: List[str], report_files: List[str],
                         month: int = None, year: int = None) -> Dict[str, Any]:
        """
        ส่ง email รายงานพร้อมไฟล์ Excel

        Args:
            to_emails: รายชื่อ email ผู้รับ
            report_files: รายชื่อ path ของไฟล์รายงาน
            month: เดือน (optional)
            year: ปี (optional)

        Returns:
            Dict: result จาก send_email()
        """
        # สร้าง subject
        if month and year:
            thai_months = ["", "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
                          "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]
            month_str = thai_months[month] if 1 <= month <= 12 else str(month)
            subject = f"รายงานรายได้ประจำเดือน {month_str} {year}"
        else:
            subject = "รายงานรายได้"

        # สร้าง body
        file_list = "<ul>"
        for file_path in report_files:
            file_name = Path(file_path).name
            file_list += f"<li>{file_name}</li>"
        file_list += "</ul>"

        body_html = f"""
        <p>เรียน ผู้รับรายงาน</p>
        <p>ส่งรายงานรายได้ตามไฟล์แนบด้านล่างนี้:</p>
        <div class="attachment-info">
            <strong>📎 ไฟล์แนบ ({len(report_files)} ไฟล์):</strong>
            {file_list}
        </div>
        <p>หากมีข้อสงสัยหรือพบปัญหา กรุณาติดต่อผู้ดูแลระบบ</p>
        <p>ขอบคุณครับ</p>
        """

        return self.send_email(
            to_emails=to_emails,
            subject=subject,
            body_html=body_html,
            attachments=report_files
        )

    def get_email_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        ดึง email logs

        Args:
            limit: จำนวน logs ที่ต้องการ (ล่าสุด)

        Returns:
            List[Dict]: รายการ email logs
        """
        data = self._load_logs()
        emails = data.get('emails', [])

        # เรียงตามเวลาล่าสุด
        emails.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

        return emails[:limit]


# Singleton instance
_email_sender = None


def get_email_sender() -> EmailSender:
    """
    Get singleton EmailSender instance

    Returns:
        EmailSender: instance
    """
    global _email_sender
    if _email_sender is None:
        _email_sender = EmailSender()
    return _email_sender


if __name__ == "__main__":
    # Test
    sender = get_email_sender()

    # Test send OTP (dev mode)
    from datetime import timedelta
    expires_at = datetime.now() + timedelta(minutes=5)
    result = sender.send_otp_email("pornthep.n@ntplc.co.th", "123456", expires_at)
    print(f"\nOTP Email Result: {result}")

    # Test send report email (dev mode)
    # Note: ไฟล์ไม่จำเป็นต้องมีจริงใน dev mode
    result = sender.send_report_email(
        to_emails=["pornthep.n@ntplc.co.th"],
        report_files=["test_report.xlsx"],
        month=8,
        year=2025
    )
    print(f"\nReport Email Result: {result}")

    # Show email logs
    print("\n📋 Email Logs:")
    logs = sender.get_email_logs(limit=5)
    for log in logs:
        print(f"  {log['timestamp']}: {log['status']} - {log['subject']}")
