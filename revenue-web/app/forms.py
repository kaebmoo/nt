from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from app.models import User

class LoginForm(FlaskForm):
    email = StringField('อีเมล', validators=[DataRequired(), Email()])
    password = PasswordField('รหัสผ่าน', validators=[DataRequired()])
    submit = SubmitField('เข้าสู่ระบบ')

class OtpForm(FlaskForm):
    otp_code = StringField('รหัส OTP 6 หลัก', validators=[DataRequired(), Length(min=6, max=6)])
    submit = SubmitField('ยืนยัน OTP')

class ConfigForm(FlaskForm):
    config_data = TextAreaField('JSON Configuration', render_kw={'rows': 20})
    submit = SubmitField('บันทึกการตั้งค่า')

class JobForm(FlaskForm):
    year = StringField('ปี (ค.ศ.)', validators=[DataRequired(), Length(min=4, max=4)])
    month = StringField('เดือน (1-12)', validators=[DataRequired(), Length(min=1, max=2)])
    submit = SubmitField('สั่งรันโปรแกรม')

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_email(self, email):
        # Allow only @ntplc.co.th emails
        if not email.data.endswith('@ntplc.co.th'):
            raise ValidationError('ต้องใช้อีเมลของ NT (@ntplc.co.th) เท่านั้น')
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('อีเมลนี้มีผู้ใช้งานในระบบแล้ว')
