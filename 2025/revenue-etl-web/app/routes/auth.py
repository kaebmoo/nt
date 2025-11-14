"""
Authentication Routes
Login/Logout/OTP
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from app.utils.validators import validate_email, validate_otp
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    """หน้าแรก - redirect ไป login หรือ dashboard"""
    if 'session_id' in session:
        # ตรวจสอบ session
        otp_manager = auth_bp.otp_manager
        session_data = otp_manager.get_session(session['session_id'])
        
        if session_data:
            # Session ยังใช้ได้ - redirect ไป dashboard
            if session_data['is_admin']:
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('user.dashboard'))
    
    # ไม่มี session หรือหมดอายุ - redirect ไป login
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """หน้า Login"""
    # ถ้า login อยู่แล้ว redirect ไป dashboard
    if 'session_id' in session:
        otp_manager = auth_bp.otp_manager
        session_data = otp_manager.get_session(session['session_id'])
        
        if session_data:
            if session_data['is_admin']:
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('user.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        # Validate email
        is_valid, message = validate_email(email)
        if not is_valid:
            flash(message, 'error')
            return render_template('login.html', email=email)
        
        # ตรวจสอบ domain
        otp_manager = auth_bp.otp_manager
        is_valid, message = otp_manager.validate_email(email)
        
        if not is_valid:
            flash(message, 'error')
            return render_template('login.html', email=email)
        
        # สร้าง OTP
        try:
            otp, expires_at = otp_manager.create_otp_session(email)
            
            # ส่ง OTP email
            email_sender = auth_bp.email_sender
            success = email_sender.send_otp_email(email, otp, expires_at)
            
            if success:
                # Log access
                json_logger = auth_bp.json_logger
                json_logger.log_access(email, "request_otp")
                
                # เก็บ email ใน session ชั่วคราว
                session['pending_email'] = email
                
                flash(f'OTP ถูกส่งไปที่ {email} แล้ว', 'success')
                return redirect(url_for('auth.verify_otp'))
            else:
                flash('ไม่สามารถส่ง OTP ได้ กรุณาลองใหม่', 'error')
                return render_template('login.html', email=email)
        
        except Exception as e:
            logger.error(f"Error in login: {e}", exc_info=True)
            flash('เกิดข้อผิดพลาด กรุณาลองใหม่', 'error')
            return render_template('login.html', email=email)
    
    return render_template('login.html')


@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    """หน้า Verify OTP"""
    # ต้องมี pending_email ใน session
    if 'pending_email' not in session:
        flash('กรุณา request OTP ก่อน', 'error')
        return redirect(url_for('auth.login'))
    
    email = session['pending_email']
    
    if request.method == 'POST':
        otp = request.form.get('otp', '').strip()
        
        # Validate OTP format
        is_valid, message = validate_otp(otp)
        if not is_valid:
            flash(message, 'error')
            return render_template('verify_otp.html', email=email)
        
        # Verify OTP
        otp_manager = auth_bp.otp_manager
        success, message = otp_manager.verify_otp(email, otp)
        
        if success:
            # OTP ถูกต้อง - สร้าง login session
            session_id = otp_manager.create_login_session(email)
            
            # เก็บ session_id
            session['session_id'] = session_id
            session.pop('pending_email', None)
            
            # Log access
            json_logger = auth_bp.json_logger
            json_logger.log_access(email, "login_success")
            
            # Check if admin
            session_data = otp_manager.get_session(session_id)
            
            flash('เข้าสู่ระบบสำเร็จ', 'success')
            
            if session_data['is_admin']:
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('user.dashboard'))
        else:
            flash(message, 'error')
            return render_template('verify_otp.html', email=email)
    
    return render_template('verify_otp.html', email=email)


@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    """ส่ง OTP ใหม่"""
    if 'pending_email' not in session:
        return jsonify({"success": False, "error": "ไม่พบ email session"}), 400
    
    email = session['pending_email']
    
    try:
        # สร้าง OTP ใหม่
        otp_manager = auth_bp.otp_manager
        otp, expires_at = otp_manager.create_otp_session(email)
        
        # ส่ง email
        email_sender = auth_bp.email_sender
        success = email_sender.send_otp_email(email, otp, expires_at)
        
        if success:
            # Log access
            json_logger = auth_bp.json_logger
            json_logger.log_access(email, "resend_otp")
            
            return jsonify({
                "success": True,
                "message": f"OTP ใหม่ถูกส่งไปที่ {email} แล้ว"
            })
        else:
            return jsonify({
                "success": False,
                "error": "ไม่สามารถส่ง OTP ได้"
            }), 500
    
    except Exception as e:
        logger.error(f"Error resending OTP: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": "เกิดข้อผิดพลาด"
        }), 500


@auth_bp.route('/logout')
def logout():
    """Logout"""
    if 'session_id' in session:
        # ลบ session
        otp_manager = auth_bp.otp_manager
        session_data = otp_manager.get_session(session['session_id'])
        
        if session_data:
            # Log access
            json_logger = auth_bp.json_logger
            json_logger.log_access(session_data['email'], "logout")
        
        otp_manager.delete_session(session['session_id'])
    
    # Clear Flask session
    session.clear()
    
    flash('ออกจากระบบเรียบร้อย', 'info')
    return redirect(url_for('auth.login'))


# Decorator สำหรับตรวจสอบ authentication
def login_required(f):
    """Decorator: ต้อง login ก่อน"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'session_id' not in session:
            flash('กรุณา login ก่อน', 'error')
            return redirect(url_for('auth.login'))
        
        # ตรวจสอบ session
        otp_manager = auth_bp.otp_manager
        session_data = otp_manager.get_session(session['session_id'])
        
        if not session_data:
            session.clear()
            flash('Session หมดอายุ กรุณา login ใหม่', 'error')
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    
    return decorated_function


def admin_required(f):
    """Decorator: ต้องเป็น admin"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'session_id' not in session:
            flash('กรุณา login ก่อน', 'error')
            return redirect(url_for('auth.login'))
        
        # ตรวจสอบ session
        otp_manager = auth_bp.otp_manager
        session_data = otp_manager.get_session(session['session_id'])
        
        if not session_data:
            session.clear()
            flash('Session หมดอายุ กรุณา login ใหม่', 'error')
            return redirect(url_for('auth.login'))
        
        if not session_data['is_admin']:
            flash('ต้องมีสิทธิ์ admin', 'error')
            return redirect(url_for('user.dashboard'))
        
        return f(*args, **kwargs)
    
    return decorated_function


def get_current_user():
    """ดึงข้อมูล current user"""
    if 'session_id' not in session:
        return None
    
    otp_manager = auth_bp.otp_manager
    return otp_manager.get_session(session['session_id'])
