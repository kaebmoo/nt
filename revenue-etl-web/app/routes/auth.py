"""
Authentication Routes
Login, OTP verification, logout
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page - enter email"""
    if 'session_id' in session:
        # Already logged in
        if session.get('is_admin'):
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('user.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()

        if not email:
            flash('กรุณากรอกอีเมล', 'error')
            return render_template('auth/login.html')

        # Check if domain is allowed
        auth_manager = current_app.auth_manager

        if not auth_manager.config.is_allowed_domain(email):
            flash('อีเมลนี้ไม่ได้รับอนุญาตให้เข้าใช้งาน', 'error')
            return render_template('auth/login.html')

        # Send OTP
        if auth_manager.send_otp(email):
            session['pending_email'] = email
            flash('รหัส OTP ถูกส่งไปยังอีเมลของคุณแล้ว', 'success')
            return redirect(url_for('auth.verify_otp'))
        else:
            flash('ไม่สามารถส่ง OTP ได้ กรุณาลองใหม่อีกครั้ง', 'error')

    return render_template('auth/login.html')


@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    """OTP verification page"""
    email = session.get('pending_email')

    if not email:
        flash('กรุณาเข้าสู่ระบบก่อน', 'error')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        otp_code = request.form.get('otp', '').strip()

        if not otp_code:
            flash('กรุณากรอกรหัส OTP', 'error')
            return render_template('auth/verify_otp.html', email=email)

        # Verify OTP
        auth_manager = current_app.auth_manager

        if auth_manager.verify_otp(email, otp_code):
            # Clear pending email
            session.pop('pending_email', None)

            # Redirect based on role
            if session.get('is_admin'):
                flash('เข้าสู่ระบบสำเร็จ (Admin)', 'success')
                return redirect(url_for('admin.dashboard'))
            else:
                flash('เข้าสู่ระบบสำเร็จ', 'success')
                return redirect(url_for('user.dashboard'))
        else:
            flash('รหัส OTP ไม่ถูกต้อง หรือหมดอายุแล้ว', 'error')

    return render_template('auth/verify_otp.html', email=email)


@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    """Resend OTP code"""
    email = session.get('pending_email')

    if not email:
        flash('กรุณาเข้าสู่ระบบก่อน', 'error')
        return redirect(url_for('auth.login'))

    auth_manager = current_app.auth_manager

    if auth_manager.send_otp(email):
        flash('ส่งรหัส OTP ใหม่แล้ว', 'success')
    else:
        flash('ไม่สามารถส่ง OTP ได้ กรุณาลองใหม่อีกครั้ง', 'error')

    return redirect(url_for('auth.verify_otp'))


@auth_bp.route('/logout')
def logout():
    """Logout user"""
    session_id = session.get('session_id')

    if session_id:
        auth_manager = current_app.auth_manager
        auth_manager.destroy_session(session_id)

    flash('ออกจากระบบเรียบร้อยแล้ว', 'success')
    return redirect(url_for('auth.login'))
