# Quick Start Guide

## ✅ สิ่งที่ได้สร้างเสร็จแล้ว

### Backend (100% Complete)
- ✅ Flask Application Factory
- ✅ OTP Authentication System
- ✅ ETL Runner & Scheduler
- ✅ Configuration Management (JSON-based)
- ✅ Logging System (JSON logs)
- ✅ Routes (Auth, User, Admin)
- ✅ File Manager
- ✅ Email Sender

### Frontend (Basic Templates)
- ✅ base.html - Base template
- ✅ login.html - Login page
- ✅ verify_otp.html - OTP verification
- ✅ user_dashboard.html - User dashboard
- ✅ admin_dashboard.html - Admin dashboard
- ✅ Basic CSS & JS

### Deployment
- ✅ requirements.txt
- ✅ wsgi.py
- ✅ supervisor.conf
- ✅ nginx.conf

## 🚀 ขั้นตอนการ Deploy (5 Steps)

### Step 1: Setup Environment
```bash
cd /path/to/your/server
git clone <repo> revenue-etl-web  # หรือ upload files
cd revenue-etl-web

# สร้าง virtual environment
python3 -m venv venv
source venv/bin/activate

# ติดตั้ง dependencies
pip install -r requirements.txt
```

### Step 2: Copy ETL Scripts
```bash
# สร้าง directories
mkdir -p etl data/{config,logs,sessions} reports

# Copy ETL scripts ของคุณ (3 ไฟล์)
cp /path/to/fi_revenue_expense.py etl/
cp /path/to/revenue_etl_report.py etl/
cp /path/to/revenue_reconciliation.py etl/

# ตรวจสอบ
ls -l etl/
```

### Step 3: Configure (แก้ไข 3 ไฟล์ JSON)

#### 3.1 ETL Config
```bash
nano data/config/etl_config.json
```
```json
{
  "input_path": "/actual/path/to/input/",
  "output_path": "/actual/path/to/output/",
  "master_path": "/actual/path/to/master/",
  "report_path": "/actual/path/to/reports/",
  "year": "2025",
  "reconcile_tolerance": 0.00,
  "enable_reconciliation": true,
  "schedule": {
    "enabled": true,
    "day_of_month": 10,
    "hour": 2,
    "minute": 0
  }
}
```

#### 3.2 Email Config
```bash
nano data/config/email_config.json
```
```json
{
  "smtp_server": "smtp.yourcompany.com",
  "smtp_port": 587,
  "smtp_use_tls": true,
  "smtp_username": "etl@yourcompany.com",
  "smtp_password": "actual-password",
  "sender_email": "etl@yourcompany.com",
  "sender_name": "Revenue ETL System",
  "otp_expiry_minutes": 10
}
```

#### 3.3 Auth Config
```bash
nano data/config/auth_config.json
```
```json
{
  "allowed_domains": ["yourcompany.com"],
  "admin_emails": ["yourname@yourcompany.com"],
  "session_timeout_minutes": 120,
  "max_otp_attempts": 3
}
```

### Step 4: Test (Development Mode)
```bash
# Run Flask development server
python wsgi.py

# เปิดเบราว์เซอร์: http://localhost:5000
# ทดสอบ login ด้วย email ของคุณ
# ตรวจสอบว่าได้รับ OTP email
```

### Step 5: Production Deployment

#### 5.1 Setup Supervisor
```bash
# แก้ไข supervisor.conf
nano supervisor.conf

# เปลี่ยน:
# - /path/to/revenue-etl-web → actual path
# - your-username → actual user
# - SECRET_KEY → generate new key

# Generate SECRET_KEY:
python -c "import secrets; print(secrets.token_hex(32))"

# Copy config
sudo cp supervisor.conf /etc/supervisor/conf.d/revenue-etl.conf

# Reload
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start revenue-etl-web

# Check
sudo supervisorctl status
```

#### 5.2 Setup Nginx
```bash
# แก้ไข nginx.conf
nano nginx.conf

# เปลี่ยน:
# - your-domain.com → actual domain
# - /path/to/revenue-etl-web → actual path

# Copy config
sudo cp nginx.conf /etc/nginx/sites-available/revenue-etl
sudo ln -s /etc/nginx/sites-available/revenue-etl /etc/nginx/sites-enabled/

# Test & Reload
sudo nginx -t
sudo systemctl reload nginx
```

## 📝 ทดสอบระบบ

### 1. ทดสอบ Login (User)
- เข้า https://your-domain.com
- กรอก email ของคุณ
- ตรวจสอบว่าได้รับ OTP email
- กรอก OTP
- ควรเห็น User Dashboard

### 2. ทดสอบ Admin Functions
- Login ด้วย admin email
- ควรเห็น Admin Dashboard พร้อม menu เพิ่ม
- ทดสอบ Config → แก้ path (optional)
- ทดสอบ Jobs → กด "Run Now"
- ตรวจสอบ Logs

### 3. ทดสอบ ETL
```bash
# ดู logs แบบ real-time
tail -f data/logs/app.log

# จาก Admin Dashboard กด "Run ETL Now"
# สังเกต logs ว่า ETL scripts ถูก execute
# ตรวจสอบว่า report files ถูกสร้าง

# หรือรันทดสอบ manually
cd etl
python3 fi_revenue_expense.py
python3 revenue_etl_report.py
```

## 🔍 Troubleshooting

### ปัญหา: ไม่ได้รับ OTP email
**วิธีแก้:**
1. ตรวจสอบ SMTP config ใน `data/config/email_config.json`
2. ทดสอบ SMTP:
```bash
python -c "
from app.config import ConfigManager
cm = ConfigManager()
print(cm.get_email_config())
"
```
3. ตรวจสอบ spam folder
4. ลอง telnet ไปที่ SMTP server

### ปัญหา: ETL scripts ไม่ทำงาน
**วิธีแก้:**
1. ตรวจสอบว่าไฟล์อยู่ใน `etl/` directory
2. ลองรัน manual: `cd etl && python3 fi_revenue_expense.py`
3. ดู job logs: `cat data/logs/jobs/job_*.json`
4. ตรวจสอบ paths ใน config

### ปัญหา: Permission denied
```bash
chown -R youruser:youruser revenue-etl-web/
chmod -R 755 revenue-etl-web/
chmod -R 775 revenue-etl-web/data/
```

## 📋 Templates ที่ต้องสร้างเพิ่ม (Optional)

หากต้องการหน้า Admin ครบถ้วน ให้สร้างเพิ่ม:
- `admin_config.html` - Config management page
- `admin_jobs.html` - Job list page
- `admin_job_detail.html` - Job detail page
- `admin_logs.html` - Logs viewer

**วิธีสร้าง:** Copy pattern จาก `admin_dashboard.html` และปรับให้เหมาะสม

## ✅ Checklist

- [ ] Virtual environment สร้างแล้ว
- [ ] Dependencies ติดตั้งแล้ว
- [ ] ETL scripts copy แล้ว (3 ไฟล์)
- [ ] Config files แก้แล้ว (3 ไฟล์ JSON)
- [ ] ทดสอบ development mode แล้ว
- [ ] Supervisor setup แล้ว
- [ ] Nginx setup แล้ว
- [ ] ทดสอบ login ได้
- [ ] ได้รับ OTP email
- [ ] ทดสอบ run ETL ได้

## 🎉 เสร็จแล้ว!

ตอนนี้ระบบพร้อมใช้งาน:
- User สามารถ login และ download reports
- Admin สามารถ run jobs และจัดการ config
- ETL จะรันอัตโนมัติตาม schedule

**Next Steps:**
1. เพิ่ม SSL certificate (Let's Encrypt)
2. Setup backup สำหรับ config files
3. Setup logrotate สำหรับ logs
4. Monitor disk space สำหรับ reports

## 📞 Need Help?
ดู logs:
```bash
# Application logs
tail -f data/logs/app.log

# Job logs
ls -lh data/logs/jobs/

# Supervisor logs
sudo supervisorctl tail -f revenue-etl-web
```
