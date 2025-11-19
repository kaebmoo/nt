"""
Revenue Report Distribution System
===================================
Web application สำหรับ browse และส่ง email รายงาน Revenue
- OTP-based authentication (ไม่ใช้ password)
- User management
- Browse Excel reports
- Send email with attachments
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import os
import sys

# ========== Guard: Ensure Web App's Modules Are Used ==========
# Prevent sys.modules pollution from ETL imports
_current_dir = os.path.dirname(os.path.abspath(__file__))

# Check and clean up modules that might be polluted by ETL imports
_web_app_modules = ['config_manager', 'user_manager', 'auth_manager', 'email_sender']
for module_name in _web_app_modules:
    if module_name in sys.modules:
        module = sys.modules[module_name]
        module_file = getattr(module, '__file__', '')
        # If module is not from current directory (web app), remove it
        if module_file and _current_dir not in module_file:
            del sys.modules[module_name]

from config_manager import get_config_manager
from user_manager import get_user_manager
from auth_manager import get_auth_manager
from email_sender import get_email_sender
# NOTE: etl_admin_tab imported lazily to avoid sys.path pollution


# Page config
st.set_page_config(
    page_title="Revenue Report Distribution",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize managers
config = get_config_manager()
user_manager = get_user_manager()
auth_manager = get_auth_manager()
email_sender = get_email_sender()


# ========== Session State ==========
def init_session_state():
    """Initialize session state - ต้อง initialize ทุกตัวแปรที่นี่เพื่อป้องกัน error เมื่อผ่าน nginx"""

    # Authentication & User
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    if 'user_data' not in st.session_state:
        st.session_state.user_data = None
    if 'otp_sent' not in st.session_state:
        st.session_state.otp_sent = False
    if 'otp_expires_at' not in st.session_state:
        st.session_state.otp_expires_at = None

    # ETL System (สำหรับ ETL Admin Tab)
    if 'etl_config_manager' not in st.session_state:
        st.session_state.etl_config_manager = None
    if 'etl_system' not in st.session_state:
        st.session_state.etl_system = None
    if 'etl_processing_status' not in st.session_state:
        st.session_state.etl_processing_status = None
    if 'etl_fi_completed' not in st.session_state:
        st.session_state.etl_fi_completed = False
    if 'etl_etl_completed' not in st.session_state:
        st.session_state.etl_etl_completed = False


def logout():
    """Logout user"""
    st.session_state.logged_in = False
    st.session_state.user_email = None
    st.session_state.user_data = None
    st.session_state.otp_sent = False
    st.session_state.otp_expires_at = None


# ========== Login Page ==========
def show_login_page():
    """แสดงหน้า Login"""
    st.title("🔐 Revenue Report Distribution System")
    st.markdown("---")

    # Dev mode warning
    if config.is_dev_mode():
        st.warning("⚙️ **DEV MODE**: OTP จะแสดงบนหน้าจอแทนการส่ง email")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("### เข้าสู่ระบบด้วย OTP")

        # Email input
        email_input = st.text_input(
            "Email",
            placeholder="ชื่อผู้ใช้ (จะเติม @ntplc.co.th ให้อัตโนมัติ)",
            help="กรอกชื่อผู้ใช้ หรือ email เต็ม"
        )

        # Request OTP button
        if st.button("🔑 ขอรหัส OTP", type="primary", use_container_width=True):
            if not email_input:
                st.error("❌ กรุณากรอก email")
            else:
                # Normalize email
                normalized_email = auth_manager.normalize_email(email_input)

                # Validate email domain
                if not auth_manager.is_valid_email_domain(normalized_email):
                    st.error(f"❌ Email ต้องเป็น @{config.get_allowed_email_domain()} เท่านั้น")
                else:
                    try:
                        # Generate OTP
                        otp_code, expires_at = auth_manager.generate_otp(normalized_email)

                        # Send OTP email
                        result = email_sender.send_otp_email(
                            normalized_email,
                            otp_code,
                            expires_at
                        )

                        if result['success']:
                            st.session_state.otp_sent = True
                            st.session_state.user_email = normalized_email
                            st.session_state.otp_expires_at = expires_at

                            if result.get('dev_mode'):
                                st.success(f"✓ Dev Mode: รหัส OTP ของคุณคือ **{otp_code}**")
                                st.info(f"⏰ หมดอายุเวลา: {expires_at.strftime('%H:%M:%S')}")
                            else:
                                st.success(f"✓ ส่งรหัส OTP ไปที่ {normalized_email} แล้ว")
                        else:
                            st.error(f"❌ ไม่สามารถส่ง OTP: {result['message']}")

                    except ValueError as e:
                        st.error(f"❌ {str(e)}")

        # OTP verification (show only if OTP was sent)
        if st.session_state.otp_sent:
            st.markdown("---")
            otp_input = st.text_input(
                "กรอกรหัส OTP",
                max_chars=6,
                placeholder="6 หลัก",
                help=f"กรอกรหัส OTP ที่ส่งไปที่ {st.session_state.user_email}"
            )

            if st.button("✓ ยืนยัน OTP", type="primary", use_container_width=True):
                if not otp_input:
                    st.error("❌ กรุณากรอกรหัส OTP")
                elif len(otp_input) != 6:
                    st.error("❌ รหัส OTP ต้องมี 6 หลัก")
                else:
                    # Verify OTP
                    if auth_manager.verify_otp(st.session_state.user_email, otp_input):
                        # Get user data
                        user = user_manager.get_user_by_email(st.session_state.user_email)

                        st.session_state.logged_in = True
                        st.session_state.user_data = user
                        st.success("✓ เข้าสู่ระบบสำเร็จ!")
                        st.rerun()
                    else:
                        st.error("❌ รหัส OTP ไม่ถูกต้องหรือหมดอายุแล้ว")


# ========== Main App ==========
def show_main_app():
    """แสดงหน้าหลักของระบบ"""
    user = st.session_state.user_data
    is_admin = user.get('is_admin', False)

    # Sidebar
    with st.sidebar:
        st.title("📊 Revenue Reports")
        st.markdown("---")

        # User info
        st.markdown(f"### 👤 {user['name']}")
        st.caption(f"📧 {user['email']}")

        if is_admin:
            st.markdown("**:green[⭐ Admin]**")

        st.markdown("---")

        # Logout button
        if st.button("🚪 ออกจากระบบ", use_container_width=True):
            logout()
            st.rerun()

    # Main content
    st.title("📊 Revenue Report Distribution System")

    # Create tabs
    if is_admin:
        tabs = st.tabs([
            "📁 Browse Reports",
            "📧 Send Email",
            "👥 User Management",
            "⚙️ Configuration",
            "📋 Email Logs",
            "🔧 ETL Admin"
        ])

        browse_tab, email_tab, users_tab, config_tab, logs_tab, etl_admin_tab = tabs

        with browse_tab:
            show_browse_reports_tab()

        with email_tab:
            show_send_email_tab()

        with users_tab:
            show_user_management_tab()

        with config_tab:
            show_configuration_tab()

        with logs_tab:
            show_email_logs_tab()

        with etl_admin_tab:
            # Lazy import to avoid sys.path pollution at module load time
            from etl_admin_tab import show_etl_admin_tab
            show_etl_admin_tab()

    else:
        tabs = st.tabs([
            "📁 Browse Reports",
            "📧 Send Email"
        ])

        browse_tab, email_tab = tabs

        with browse_tab:
            show_browse_reports_tab()

        with email_tab:
            show_send_email_tab()


# ========== Browse Reports Tab ==========
def show_browse_reports_tab():
    """แสดง tab Browse Reports"""
    st.markdown("### 📁 Browse Revenue Reports")

    # Get reports path
    reports_path = config.get_reports_path()

    col1, col2 = st.columns([4, 1])
    with col1:
        st.info(f"📂 Reports Location: `{reports_path}`")
    with col2:
        if st.button("🔄 Refresh", key="refresh_reports", help="Refresh file list"):
            st.rerun()

    # Check if path exists
    if not Path(reports_path).exists():
        st.error(f"❌ ไม่พบ directory: {reports_path}")
        st.info("💡 กรุณาตรวจสอบการตั้งค่า path ใน Configuration tab (admin only)")
        return

    # List Excel files
    excel_files = list(Path(reports_path).glob("*.xlsx"))
    # เรียงตามชื่อไฟล์ (มีวันที่อยู่ในชื่อ) แทนเวลาสร้าง
    excel_files.sort(key=lambda x: x.name, reverse=True)

    if not excel_files:
        st.warning("⚠️ ไม่พบไฟล์ Excel ใน directory นี้")
        return

    st.success(f"✓ พบ {len(excel_files)} ไฟล์")

    # File selection
    selected_files = []

    for file_path in excel_files:
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

        with col1:
            if st.checkbox(file_path.name, key=f"browse_{file_path.name}"):
                selected_files.append(str(file_path))

        with col2:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            st.caption(f"📦 {size_mb:.2f} MB")

        with col3:
            modified_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            st.caption(f"🕐 {modified_time.strftime('%Y-%m-%d %H:%M')}")

        with col4:
            # Download button
            with open(file_path, 'rb') as f:
                st.download_button(
                    "⬇️",
                    data=f.read(),
                    file_name=file_path.name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"download_{file_path.name}"
                )

    # Summary
    if selected_files:
        st.markdown("---")
        st.info(f"✓ เลือก {len(selected_files)} ไฟล์")


# ========== Send Email Tab ==========
def show_send_email_tab():
    """แสดง tab Send Email"""
    st.markdown("### 📧 Send Email with Reports")

    # Get active users
    active_users = user_manager.get_active_users()

    if not active_users:
        st.error("❌ ไม่มีผู้ใช้ในระบบ")
        return

    # Recipient selection
    st.markdown("#### 👥 เลือกผู้รับ")

    selected_emails = []
    for user in active_users:
        if st.checkbox(f"{user['name']} ({user['email']})", key=f"recipient_{user['email']}"):
            selected_emails.append(user['email'])

    if not selected_emails:
        st.warning("⚠️ กรุณาเลือกผู้รับอย่างน้อย 1 คน")

    st.markdown("---")

    # File selection
    st.markdown("#### 📎 เลือกไฟล์รายงาน")

    reports_path = config.get_reports_path()

    col1, col2 = st.columns([4, 1])
    with col1:
        st.info(f"📂 Reports Location: `{reports_path}`")
    with col2:
        if st.button("🔄 Refresh", key="refresh_email_files", help="Refresh file list"):
            st.rerun()

    if not Path(reports_path).exists():
        st.error(f"❌ ไม่พบ directory: {reports_path}")
        return

    excel_files = list(Path(reports_path).glob("*.xlsx"))
    # เรียงตามชื่อไฟล์ (มีวันที่อยู่ในชื่อ) แทนเวลาสร้าง
    excel_files.sort(key=lambda x: x.name, reverse=True)

    if not excel_files:
        st.warning("⚠️ ไม่พบไฟล์ Excel")
        return

    st.success(f"✓ พบ {len(excel_files)} ไฟล์")

    selected_files = []
    for file_path in excel_files:
        col1, col2, col3 = st.columns([3, 2, 2])

        with col1:
            if st.checkbox(file_path.name, key=f"email_file_{file_path.name}"):
                selected_files.append(str(file_path))

        with col2:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            st.caption(f"📦 {size_mb:.2f} MB")

        with col3:
            modified_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            st.caption(f"🕐 {modified_time.strftime('%Y-%m-%d %H:%M')}")

    if not selected_files:
        st.warning("⚠️ กรุณาเลือกไฟล์อย่างน้อย 1 ไฟล์")

    st.markdown("---")

    # Email preview
    if selected_emails and selected_files:
        st.markdown("#### 📝 Email Preview")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**ผู้รับ:** {len(selected_emails)} คน")
            for email in selected_emails:
                st.caption(f"  • {email}")

        with col2:
            st.markdown(f"**ไฟล์แนบ:** {len(selected_files)} ไฟล์")
            for file_path in selected_files:
                st.caption(f"  • {Path(file_path).name}")

        # Send button
        st.markdown("---")

        if st.button("📤 ส่ง Email", type="primary", use_container_width=True):
            with st.spinner("กำลังส่ง email..."):
                result = email_sender.send_report_email(
                    to_emails=selected_emails,
                    report_files=selected_files
                )

                if result['success']:
                    if result.get('dev_mode'):
                        st.success(f"✓ {result['message']}")
                        st.info("📧 Check console for email preview")
                    else:
                        st.success(f"✓ {result['message']}")
                        st.balloons()
                else:
                    st.error(f"❌ {result['message']}")


# ========== User Management Tab (Admin Only) ==========
def show_user_management_tab():
    """แสดง tab User Management (admin only)"""
    st.markdown("### 👥 User Management")

    # Add new user
    with st.expander("➕ Add New User", expanded=False):
        with st.form("add_user_form"):
            col1, col2 = st.columns(2)

            with col1:
                new_email = st.text_input("Email", placeholder="username@ntplc.co.th")
                new_name = st.text_input("Name", placeholder="ชื่อ-นามสกุล")

            with col2:
                new_is_admin = st.checkbox("Admin")
                new_is_active = st.checkbox("Active", value=True)

            submitted = st.form_submit_button("➕ Add User", type="primary")

            if submitted:
                if not new_email or not new_name:
                    st.error("❌ กรุณากรอกข้อมูลให้ครบ")
                else:
                    # Normalize email
                    normalized_email = auth_manager.normalize_email(new_email)

                    # Validate domain
                    if not auth_manager.is_valid_email_domain(normalized_email):
                        st.error(f"❌ Email ต้องเป็น @{config.get_allowed_email_domain()} เท่านั้น")
                    else:
                        try:
                            user = user_manager.create_user(
                                email=normalized_email,
                                name=new_name,
                                is_admin=new_is_admin
                            )

                            if not new_is_active:
                                user_manager.update_user(user['id'], is_active=False)

                            st.success(f"✓ เพิ่มผู้ใช้ {new_name} สำเร็จ")
                            st.rerun()

                        except ValueError as e:
                            st.error(f"❌ {str(e)}")

    st.markdown("---")

    # List users
    st.markdown("#### 📋 User List")

    users = user_manager.get_all_users()

    if not users:
        st.info("ไม่มีผู้ใช้ในระบบ")
        return

    for user in users:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 1])

            with col1:
                st.markdown(f"**{user['name']}**")
                st.caption(user['email'])

            with col2:
                if user.get('is_admin'):
                    st.markdown("**:green[⭐ Admin]**")
                if not user.get('is_active'):
                    st.markdown("**:red[❌ Inactive]**")

            with col3:
                # Toggle active
                current_active = user.get('is_active', False)
                if st.button(
                    "✓" if current_active else "✗",
                    key=f"toggle_active_{user['id']}",
                    help="Toggle Active/Inactive"
                ):
                    user_manager.update_user(user['id'], is_active=not current_active)
                    st.rerun()

            with col4:
                # Toggle admin
                current_admin = user.get('is_admin', False)
                if st.button(
                    "⭐" if current_admin else "👤",
                    key=f"toggle_admin_{user['id']}",
                    help="Toggle Admin"
                ):
                    user_manager.update_user(user['id'], is_admin=not current_admin)
                    st.rerun()

            with col5:
                # Delete user
                if st.button("🗑️", key=f"delete_{user['id']}", help="Delete User"):
                    if user_manager.delete_user(user['id']):
                        st.success(f"✓ ลบ {user['name']} สำเร็จ")
                        st.rerun()

            st.markdown("---")

    # Export/Import
    st.markdown("#### 📤 Export / Import")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📤 Export Users to CSV"):
            if user_manager.export_users_csv("users_export.csv"):
                with open("users_export.csv", 'rb') as f:
                    st.download_button(
                        "⬇️ Download CSV",
                        data=f.read(),
                        file_name="users_export.csv",
                        mime="text/csv"
                    )

    with col2:
        uploaded_file = st.file_uploader("📥 Import Users from CSV", type="csv")
        if uploaded_file:
            with open("users_import.csv", 'wb') as f:
                f.write(uploaded_file.getvalue())

            count = user_manager.import_users_csv("users_import.csv")
            st.success(f"✓ Import {count} users สำเร็จ")
            st.rerun()


# ========== Configuration Tab (Admin Only) ==========
def show_configuration_tab():
    """แสดง tab Configuration (admin only)"""
    st.markdown("### ⚙️ Configuration")

    st.warning("⚠️ การเปลี่ยนแปลง config จะมีผลทันที (ยกเว้น SMTP credentials ที่เก็บใน .env)")

    # App settings
    with st.expander("📱 App Settings", expanded=True):
        app_name = st.text_input("App Name", value=config.get('app.name', ''))
        dev_mode = st.checkbox("Dev Mode", value=config.is_dev_mode())
        allowed_domain = st.text_input(
            "Allowed Email Domain",
            value=config.get_allowed_email_domain()
        )

        if st.button("💾 Save App Settings"):
            config.set('app.name', app_name)
            config.set('app.dev_mode', dev_mode)
            config.set('app.allowed_email_domain', allowed_domain)

            if config.save_config(config.config):
                st.success("✓ บันทึก App Settings สำเร็จ")
            else:
                st.error("❌ ไม่สามารถบันทึก config")

    # Path settings
    with st.expander("📂 Path Settings", expanded=True):
        base_path = st.text_input(
            "Reports Base Path",
            value=config.get('paths.reports_base_path', '')
        )
        year = st.text_input(
            "Reports Year",
            value=config.get('paths.reports_year', '2025')
        )
        relative_path = st.text_input(
            "Reports Relative Path",
            value=config.get('paths.reports_relative_path', ''),
            help="ใช้ {year} เป็น placeholder"
        )

        # Show full path
        full_path = config.get_reports_path()
        st.info(f"📁 Full Path: `{full_path}`")

        # Check path existence
        if Path(full_path).exists():
            st.success("✓ Path exists")
        else:
            st.error("❌ Path not found")

        if st.button("💾 Save Path Settings"):
            config.set('paths.reports_base_path', base_path)
            config.set('paths.reports_year', year)
            config.set('paths.reports_relative_path', relative_path)

            if config.save_config(config.config):
                st.success("✓ บันทึก Path Settings สำเร็จ")
            else:
                st.error("❌ ไม่สามารถบันทึก config")

    # Email settings
    with st.expander("📧 Email Settings", expanded=False):
        st.caption("📝 SMTP credentials (username/password) จะเก็บใน .env file เท่านั้น")

        smtp_server = st.text_input("SMTP Server", value=config.get('email.smtp_server', ''))
        smtp_port = st.number_input("SMTP Port", value=config.get('email.smtp_port', 465))
        use_ssl = st.checkbox("Use SSL", value=config.get('email.use_ssl', True))
        from_email = st.text_input("From Email", value=config.get('email.from_email', ''))
        sender_name = st.text_input("Sender Name", value=config.get('email.sender_name', ''))

        if st.button("💾 Save Email Settings"):
            config.set('email.smtp_server', smtp_server)
            config.set('email.smtp_port', smtp_port)
            config.set('email.use_ssl', use_ssl)
            config.set('email.from_email', from_email)
            config.set('email.sender_name', sender_name)

            if config.save_config(config.config):
                st.success("✓ บันทึก Email Settings สำเร็จ")
            else:
                st.error("❌ ไม่สามารถบันทึก config")

    # OTP settings
    with st.expander("🔐 OTP Settings", expanded=False):
        code_length = st.number_input(
            "Code Length",
            value=config.get('otp.code_length', 6),
            min_value=4,
            max_value=8
        )
        expiry_minutes = st.number_input(
            "Expiry Minutes",
            value=config.get('otp.expiry_minutes', 5),
            min_value=1,
            max_value=60
        )
        max_attempts = st.number_input(
            "Max Attempts (per hour)",
            value=config.get('otp.max_attempts', 3),
            min_value=1,
            max_value=10
        )

        if st.button("💾 Save OTP Settings"):
            config.set('otp.code_length', code_length)
            config.set('otp.expiry_minutes', expiry_minutes)
            config.set('otp.max_attempts', max_attempts)

            if config.save_config(config.config):
                st.success("✓ บันทึก OTP Settings สำเร็จ")
            else:
                st.error("❌ ไม่สามารถบันทึก config")


# ========== Email Logs Tab (Admin Only) ==========
def show_email_logs_tab():
    """แสดง tab Email Logs (admin only)"""
    st.markdown("### 📋 Email Logs")

    # Get logs
    logs = email_sender.get_email_logs(limit=100)

    if not logs:
        st.info("ไม่มี email logs")
        return

    # Convert to dataframe
    df = pd.DataFrame(logs)

    # Format timestamp
    df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')

    # Format recipients
    df['recipients'] = df['to'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)

    # Format attachments
    df['files'] = df['attachments'].apply(
        lambda x: ', '.join(x) if isinstance(x, list) else str(len(x)) if x else '0'
    )

    # Status badge
    def format_status(status):
        if status == 'sent':
            return '✓ Sent'
        elif status == 'failed':
            return '❌ Failed'
        elif status == 'dev_mode':
            return '🔧 Dev Mode'
        return status

    df['status_display'] = df['status'].apply(format_status)

    # Display
    st.dataframe(
        df[['timestamp', 'recipients', 'subject', 'files', 'status_display']],
        use_container_width=True,
        hide_index=True,
        column_config={
            'timestamp': 'Time',
            'recipients': 'To',
            'subject': 'Subject',
            'files': 'Attachments',
            'status_display': 'Status'
        }
    )

    # Show failed emails
    failed = df[df['status'] == 'failed']
    if not failed.empty:
        st.markdown("---")
        st.error(f"⚠️ Failed Emails: {len(failed)}")

        for _, row in failed.iterrows():
            with st.expander(f"❌ {row['timestamp']} - {row['subject']}"):
                st.caption(f"**To:** {row['recipients']}")
                st.caption(f"**Error:** {row.get('error', 'Unknown error')}")


# ========== Main ==========
def main():
    """Main function"""
    init_session_state()

    if not st.session_state.logged_in:
        show_login_page()
    else:
        show_main_app()


if __name__ == "__main__":
    main()
