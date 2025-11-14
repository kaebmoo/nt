from flask_mail import Message
from app import mail
from flask import current_app, session
from threading import Thread

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, recipients, text_body, html_body):
    app = current_app._get_current_object()
    
    # Debugging print statements
    print(f"--- DEBUG: MAIL_SERVER: {app.config.get('MAIL_SERVER')}")
    print(f"--- DEBUG: MAIL_USERNAME: {app.config.get('MAIL_USERNAME')}")
    print(f"--- DEBUG: MAIL_PASSWORD exists: {bool(app.config.get('MAIL_PASSWORD'))}")

    if (not app.config.get('MAIL_SERVER') or 
        not app.config.get('MAIL_USERNAME') or 
        app.config.get('MAIL_USERNAME') == 'your-email@example.com' or
        not app.config.get('MAIL_PASSWORD')):
        print('--- EMAIL START ---')
        print(f'Subject: {subject}')
        print(f'Recipients: {recipients}')
        print(f'Body: {text_body}')
        print('--- EMAIL END ---')
        
        # Extract OTP from text_body and store in session for dev mode
        if "Your OTP code is: " in text_body:
            otp_code = text_body.split("Your OTP code is: ")[1].strip()
            session['dev_otp_code'] = otp_code
            print(f"OTP stored in session for dev mode: {otp_code}")
        return

    msg = Message(subject, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(app, msg)).start()
