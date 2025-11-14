"""
Email Tasks for RQ Worker
Async email sending tasks
"""

from app.utils.email_sender import EmailSender
from app.config import ConfigManager


def send_otp_email_task(recipient_email: str, otp_code: str):
    """
    Task function for sending OTP email asynchronously

    Args:
        recipient_email: Recipient email address
        otp_code: OTP code to send

    Returns:
        Dict with success status and message
    """
    try:
        # Initialize config and email sender
        config_manager = ConfigManager()
        email_config = config_manager.get_email_config()
        email_sender = EmailSender(email_config)

        # Send OTP
        success = email_sender.send_otp(recipient_email, otp_code)

        if success:
            return {
                'success': True,
                'message': f'OTP sent successfully to {recipient_email}'
            }
        else:
            return {
                'success': False,
                'message': 'Failed to send OTP'
            }

    except Exception as e:
        return {
            'success': False,
            'message': f'Error sending OTP: {str(e)}'
        }


def send_notification_email_task(recipient_email: str, subject: str, message: str):
    """
    Task function for sending notification email asynchronously

    Args:
        recipient_email: Recipient email address
        subject: Email subject
        message: Email message

    Returns:
        Dict with success status and message
    """
    try:
        # Initialize config and email sender
        config_manager = ConfigManager()
        email_config = config_manager.get_email_config()
        email_sender = EmailSender(email_config)

        # Send notification
        success = email_sender.send_notification(recipient_email, subject, message)

        if success:
            return {
                'success': True,
                'message': f'Notification sent successfully to {recipient_email}'
            }
        else:
            return {
                'success': False,
                'message': 'Failed to send notification'
            }

    except Exception as e:
        return {
            'success': False,
            'message': f'Error sending notification: {str(e)}'
        }
