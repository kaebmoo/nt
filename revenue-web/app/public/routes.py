from flask import render_template, flash, redirect, url_for, session, request
from flask_login import login_user, logout_user, current_user
from app import db
from app.public import bp
from app.email import send_email
from app.models import User, Otp, Role
from app.forms import LoginForm, OtpForm, RegistrationForm

@bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('user.dashboard'))
    return redirect(url_for('public.login'))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('public.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('อีเมลหรือรหัสผ่านไม่ถูกต้อง', 'danger')
            return redirect(url_for('public.login'))

        # Create and send OTP
        otp = Otp(user_id=user.id)
        db.session.add(otp)
        db.session.commit()
        
        send_email('Your OTP Code',
                   recipients=[user.email],
                   text_body=f'Your OTP code is: {otp.otp_code}',
                   html_body=f'<h3>Your OTP code is: {otp.otp_code}</h3>')
        
        session['user_id_for_otp'] = user.id
        flash('ระบบได้ส่งรหัส OTP 6 หลักไปที่อีเมลของคุณแล้ว', 'info')
        return redirect(url_for('public.verify_otp'))
        
    return render_template('public/login.html', title='Login', form=form)

@bp.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if 'user_id_for_otp' not in session:
        flash('กรุณาล็อกอินเพื่อขอรหัส OTP', 'warning')
        return redirect(url_for('public.login'))

    form = OtpForm()
    dev_otp_code = session.pop('dev_otp_code', None) # Retrieve OTP for dev mode display
    if form.validate_on_submit():
        user_id = session['user_id_for_otp']
        otp = Otp.query.filter_by(user_id=user_id, otp_code=form.otp_code.data).first()

        if otp and otp.is_valid():
            user = User.query.get(user_id)
            login_user(user)
            
            # Clean up OTPs
            Otp.query.filter_by(user_id=user_id).delete()
            db.session.commit()
            session.pop('user_id_for_otp', None)
            
            flash('เข้าสู่ระบบสำเร็จ', 'success')
            return redirect(url_for('public.index'))
        else:
            flash('รหัส OTP ไม่ถูกต้องหรือหมดอายุแล้ว', 'danger')
            
    return render_template('public/verify_otp.html', title='Verify OTP', form=form, dev_otp_code=dev_otp_code)

@bp.route('/logout')
def logout():
    logout_user()
    flash('ออกจากระบบสำเร็จ', 'info')
    return redirect(url_for('public.login'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('public.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data)
        user.set_password(form.password.data)
        user_role = Role.query.filter_by(name='user').first()
        if user_role is None:
            Role.insert_roles()
            user_role = Role.query.filter_by(name='user').first()
        user.roles.append(user_role)
        db.session.add(user)
        db.session.commit()
        flash('ลงทะเบียนสำเร็จ! กรุณาล็อกอิน', 'success')
        return redirect(url_for('public.login'))
    return render_template('public/register.html', title='Register', form=form)

@bp.route('/setup/roles')
def setup_roles():
    """A simple, unauthenticated route to set up the roles."""
    try:
        Role.insert_roles()
        flash('Roles inserted successfully.', 'success')
    except Exception as e:
        flash(f'Error inserting roles: {e}', 'danger')
        db.session.rollback()
    return redirect(url_for('public.index'))
