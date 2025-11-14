from flask_mail import Message
from app import mail
from flask import current_app, session
from threading import Thread
import smtplib
import time
import logging

logger = logging.getLogger(__name__)

def send_async_email(app, msg):
    """Send email asynchronously with retry logic for connection errors."""
    max_retries = 3
    retry_delay = 2  # seconds

    with app.app_context():
        for attempt in range(max_retries):
            try:
                mail.send(msg)
                logger.info(f"Email sent successfully to {msg.recipients}")
                return
            except (smtplib.SMTPServerDisconnected, ConnectionResetError, OSError) as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Email send attempt {attempt + 1} failed: {str(e)}. Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"Failed to send email after {max_retries} attempts: {str(e)}")
                    logger.error(f"Recipients: {msg.recipients}, Subject: {msg.subject}")
            except Exception as e:
                logger.error(f"Unexpected error sending email: {str(e)}")
                logger.error(f"Recipients: {msg.recipients}, Subject: {msg.subject}")
                break

def send_email(subject, recipients, text_body, html_body):
    """Send an email with the given parameters. Falls back to console logging in dev mode."""
    app = current_app._get_current_object()

    # Log email configuration for debugging
    logger.debug(f"MAIL_SERVER: {app.config.get('MAIL_SERVER')}")
    logger.debug(f"MAIL_PORT: {app.config.get('MAIL_PORT')}")
    logger.debug(f"MAIL_USE_TLS: {app.config.get('MAIL_USE_TLS')}")
    logger.debug(f"MAIL_USE_SSL: {app.config.get('MAIL_USE_SSL')}")
    logger.debug(f"MAIL_USERNAME: {app.config.get('MAIL_USERNAME')}")
    logger.debug(f"MAIL_PASSWORD exists: {bool(app.config.get('MAIL_PASSWORD'))}")

    # Check if email is properly configured
    if (not app.config.get('MAIL_SERVER') or
        not app.config.get('MAIL_USERNAME') or
        app.config.get('MAIL_USERNAME') == 'your-email@example.com' or
        not app.config.get('MAIL_PASSWORD')):
        logger.info('Email not configured - using dev mode (console output)')
        print('--- EMAIL START ---')
        print(f'Subject: {subject}')
        print(f'Recipients: {recipients}')
        print(f'Body: {text_body}')
        print('--- EMAIL END ---')

        # Extract OTP from text_body and store in session for dev mode
        if "Your OTP code is: " in text_body:
            otp_code = text_body.split("Your OTP code is: ")[1].strip()
            session['dev_otp_code'] = otp_code
            logger.info(f"OTP stored in session for dev mode: {otp_code}")
        return

    try:
        msg = Message(subject, recipients=recipients)
        msg.body = text_body
        msg.html = html_body
        Thread(target=send_async_email, args=(app, msg)).start()
        logger.info(f"Email queued for async delivery to {recipients}")
    except Exception as e:
        logger.error(f"Error queuing email: {str(e)}")
        raise
