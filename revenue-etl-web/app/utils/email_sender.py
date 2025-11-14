"""
Email Sender Utility
Handles sending OTP codes and notifications via SMTP
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional


class EmailSender:
    """Email sender for OTP and notifications"""

    def __init__(self, config: dict):
        """
        Initialize email sender with SMTP configuration

        Args:
            config: Email configuration dict with 'smtp' and 'sender' keys
        """
        self.smtp_config = config.get('smtp', {})
        self.sender_config = config.get('sender', {})

    def send_otp(self, to_email: str, otp_code: str) -> bool:
        """
        Send OTP code to email

        Args:
            to_email: Recipient email address
            otp_code: OTP code to send

        Returns:
            True if sent successfully, False otherwise
        """
        subject = "Your OTP Code - Revenue ETL System"

        # HTML email body
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background: #f5f5f5; padding: 30px; border-radius: 10px;">
                    <h2 style="color: #333;">Revenue ETL System</h2>
                    <p style="font-size: 16px; color: #666;">
                        Your One-Time Password (OTP) is:
                    </p>
                    <div style="background: white; padding: 20px; text-align: center; border-radius: 5px; margin: 20px 0;">
                        <span style="font-size: 32px; font-weight: bold; color: #007bff; letter-spacing: 5px;">
                            {otp_code}
                        </span>
                    </div>
                    <p style="font-size: 14px; color: #999;">
                        This code will expire in 10 minutes.<br>
                        If you didn't request this code, please ignore this email.
                    </p>
                </div>
            </body>
        </html>
        """

        # Plain text fallback
        text_body = f"""
        Revenue ETL System

        Your One-Time Password (OTP) is: {otp_code}

        This code will expire in 10 minutes.
        If you didn't request this code, please ignore this email.
        """

        return self._send_email(to_email, subject, html_body, text_body)

    def send_notification(self, to_email: str, subject: str, message: str) -> bool:
        """
        Send notification email

        Args:
            to_email: Recipient email address
            subject: Email subject
            message: Email message (plain text)

        Returns:
            True if sent successfully, False otherwise
        """
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto;">
                    <h3 style="color: #333;">{subject}</h3>
                    <div style="background: #f5f5f5; padding: 20px; border-radius: 5px;">
                        <pre style="white-space: pre-wrap; font-family: monospace; font-size: 14px;">
{message}
                        </pre>
                    </div>
                </div>
            </body>
        </html>
        """

        return self._send_email(to_email, subject, html_body, message)

    def _send_email(self, to_email: str, subject: str, html_body: str, text_body: str) -> bool:
        """
        Internal method to send email via SMTP

        Args:
            to_email: Recipient email
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.sender_config.get('name', 'System')} <{self.sender_config.get('email')}>"
            msg['To'] = to_email

            # Attach both plain text and HTML versions
            part1 = MIMEText(text_body, 'plain', 'utf-8')
            part2 = MIMEText(html_body, 'html', 'utf-8')

            msg.attach(part1)
            msg.attach(part2)

            # Connect to SMTP server and send
            host = self.smtp_config.get('host')
            port = self.smtp_config.get('port', 587)
            use_tls = self.smtp_config.get('use_tls', True)
            username = self.smtp_config.get('username')
            password = self.smtp_config.get('password')

            if not host or not username:
                print("SMTP configuration incomplete")
                return False

            # Connect and send
            server = smtplib.SMTP(host, port, timeout=30)

            if use_tls:
                server.starttls()

            if password:
                server.login(username, password)

            server.send_message(msg)
            server.quit()

            return True

        except Exception as e:
            print(f"Error sending email: {e}")
            return False
