# Revenue ETL Web Application

Web-based interface สำหรับจัดการ Revenue ETL Pipeline พร้อม OTP authentication และ automated scheduling

## 📋 Features

### สำหรับ User ทั่วไป
- ✅ Login ด้วย Email OTP (ไม่ต้องใช้ password)
- ✅ ดาวน์โหลด Excel reports ที่ถูกสร้างโดย ETL
- ✅ Filter reports ตาม year/month
- ✅ ดูสถิติ reports

### สำหรับ Admin
- ✅ ทุกอย่างที่ User ทำได้
- ✅ จัดการ Configuration (paths, schedule settings)
- ✅ Run ETL jobs manually หรือ schedule อัตโนมัติ
- ✅ Monitor job progress และ logs
- ✅ ดู access logs และ audit trail
- ✅ จัดการ schedule (วัน-เวลาที่รัน auto)

## 🏗️ Architecture

```
Web Interface (Flask)
    ↓
OTP Authentication (Email-based)
    ↓
├── User Dashboard → Download Reports
└── Admin Dashboard
    ├── Config Management
    ├── Job Management (Manual/Auto)
    ├── ETL Runner (subprocess)
    │   ├── fi_revenue_expense.py
    │   └── revenue_etl_report.py
    └── Logs Viewer
```

**Technology Stack:**
- Backend: Flask + APScheduler
- Auth: OTP via SMTP (no password)
- Storage: JSON files (no SQL database)
- Task: Subprocess execution
- Deploy: Gunicorn + Supervisor + Nginx

## 📁 โครงสร้างไฟล์

```
revenue-etl-web/
├── app/
│   ├── __init__.py                 # Flask app factory
│   ├── config.py                   # Configuration management
│   ├── auth.py                     # OTP authentication
│   ├── scheduler.py                # APScheduler
│   ├── etl_runner.py              # ETL execution wrapper
│   ├── logger.py                   # Logging system
│   ├── routes/                     # Flask routes
│   ├── templates/                  # HTML templates
│   ├── static/                     # CSS/JS
│   └── utils/                      # Utilities
│
├── data/                           # Application data
│   ├── config/                     # JSON configs
│   ├── logs/                       # Log files
│   └── sessions/                   # Session data
│
├── etl/                            # ETL scripts
│   ├── fi_revenue_expense.py
│   ├── revenue_etl_report.py
│   └── revenue_reconciliation.py
│
├── reports/                        # Generated reports
│
├── requirements.txt
├── wsgi.py
├── supervisor.conf
└── nginx.conf
```

## 🚀 Installation & Setup

### 1. Prerequisites

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.9 python3-pip python3-venv nginx supervisor

# Python dependencies
# ดู requirements.txt
```

### 2. Clone & Setup

```bash
# Clone หรือ copy โปรเจค
cd /path/to/your/projects
git clone <repo> revenue-etl-web
cd revenue-etl-web

# สร้าง virtual environment
python3 -m venv venv
source venv/bin/activate

# ติดตั้ง dependencies
pip install -r requirements.txt
```

### 3. Setup Directories

```bash
# สร้าง directories จำเป็น
mkdir -p etl data/{config,logs,sessions} reports

# Copy ETL scripts ของคุณ
cp /path/to/fi_revenue_expense.py etl/
cp /path/to/revenue_etl_report.py etl/
cp /path/to/revenue_reconciliation.py etl/

# สร้าง logs directories
mkdir -p data/logs/jobs
```

### 4. Configuration

#### 4.1 ETL Config (`data/config/etl_config.json`)

```json
{
  "input_path": "/path/to/input/data/",
  "output_path": "/path/to/output/data/",
  "master_path": "/path/to/master/files/",
  "report_path": "/path/to/reports/",
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

#### 4.2 Email Config (`data/config/email_config.json`)

```json
{
  "smtp_server": "smtp.company.com",
  "smtp_port": 587,
  "smtp_use_tls": true,
  "smtp_username": "etl@company.com",
  "smtp_password": "your-smtp-password",
  "sender_email": "etl@company.com",
  "sender_name": "Revenue ETL System",
  "otp_expiry_minutes": 10
}
```

#### 4.3 Auth Config (`data/config/auth_config.json`)

```json
{
  "allowed_domains": ["company.com"],
  "admin_emails": ["admin@company.com", "boss@company.com"],
  "session_timeout_minutes": 120,
  "max_otp_attempts": 3
}
```

#### 4.4 Environment Variables (`.env`)

```bash
# Copy example
cp .env.example .env

# Edit .env
SECRET_KEY=your-secret-key-here
APP_URL=https://your-domain.com
```

### 5. ทดสอบ (Development Mode)

```bash
# เปิด Flask development server
python wsgi.py

# เปิดเบราว์เซอร์
http://localhost:5000
```

## 🔧 Production Deployment

### 1. Setup Supervisor

```bash
# แก้ไข supervisor.conf ให้ถูกต้อง
# - เปลี่ยน /path/to/revenue-etl-web
# - เปลี่ยน user
# - เปลี่ยน SECRET_KEY

# Copy config
sudo cp supervisor.conf /etc/supervisor/conf.d/revenue-etl.conf

# Reload supervisor
sudo supervisorctl reread
sudo supervisorctl update

# Start application
sudo supervisorctl start revenue-etl-web

# Check status
sudo supervisorctl status revenue-etl-web
```

### 2. Setup Nginx

```bash
# แก้ไข nginx.conf
# - เปลี่ยน server_name
# - เปลี่ยน paths

# Copy config
sudo cp nginx.conf /etc/nginx/sites-available/revenue-etl

# Enable site
sudo ln -s /etc/nginx/sites-available/revenue-etl /etc/nginx/sites-enabled/

# Test config
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

### 3. SSL (Optional แต่แนะนำ)

```bash
# ใช้ Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## 📖 Usage

### สำหรับ User

1. เข้า https://your-domain.com
2. กรอก email (ต้องเป็น domain ที่อนุญาต)
3. กรอก OTP ที่ได้รับทาง email
4. เข้าสู่ dashboard
5. เลือก report และ download

### สำหรับ Admin

1. Login เหมือน user (แต่ใช้ admin email)
2. เข้าสู่ Admin Dashboard
3. **Config Tab**: แก้ไข paths, schedule settings
4. **Jobs Tab**: 
   - กด "Run Now" เพื่อรัน manual
   - ดู job history และ logs
   - Monitor progress
5. **Logs Tab**: ดู access logs

## 🔄 Automation

ETL จะรันอัตโนมัติตาม schedule ที่ตั้งค่า:
- Default: วันที่ 10 ของทุกเดือน เวลา 02:00
- สามารถแก้ไขได้ใน Admin → Config

เมื่อ job เสร็จสมบูรณ์:
- ส่ง email notification ให้ admins
- Log ทุกขั้นตอน
- Report files พร้อม download

## 🔒 Security

- ✅ OTP authentication (6 digits, 10 min expiry)
- ✅ Session-based (2 hours timeout)
- ✅ Domain whitelist
- ✅ Admin role separation
- ✅ Path validation
- ✅ No SQL injection (ใช้ JSON files)
- ✅ HTTPS recommended

## 📊 Monitoring

### Log Files

```bash
# Application logs
tail -f data/logs/app.log

# Access logs (JSON Lines)
tail -f data/logs/access.log

# Job logs (JSON per job)
ls -lah data/logs/jobs/

# Gunicorn logs
tail -f data/logs/gunicorn-error.log
```

### Supervisor Commands

```bash
# ดูสถานะ
sudo supervisorctl status revenue-etl-web

# Restart
sudo supervisorctl restart revenue-etl-web

# Stop
sudo supervisorctl stop revenue-etl-web

# Start
sudo supervisorctl start revenue-etl-web

# View logs
sudo supervisorctl tail -f revenue-etl-web
```

## 🐛 Troubleshooting

### ETL Jobs ไม่ทำงาน

1. ตรวจสอบว่า ETL scripts อยู่ใน `etl/` directory
2. ตรวจสอบ paths ใน `data/config/etl_config.json`
3. ดู job logs ใน `data/logs/jobs/`
4. ลอง run manual ผ่าน Admin dashboard

### ไม่ได้รับ OTP Email

1. ตรวจสอบ SMTP config ใน `data/config/email_config.json`
2. ทดสอบ SMTP connection:
```bash
python -c "from app.utils.email_sender import EmailSender; from app.config import ConfigManager; cm = ConfigManager(); es = EmailSender(cm); print('SMTP Config:', cm.get_email_config())"
```

### Session หมดอายุเร็วเกินไป

แก้ไข `session_timeout_minutes` ใน `data/config/auth_config.json`

### Permission Errors

```bash
# ตรวจสอบ ownership
chown -R your-username:your-username revenue-etl-web/

# ตรวจสอบ permissions
chmod -R 755 revenue-etl-web/
chmod -R 775 revenue-etl-web/data/
```

## 🔧 Maintenance

### Backup

```bash
# Backup configs
tar -czf backup-configs-$(date +%Y%m%d).tar.gz data/config/

# Backup logs
tar -czf backup-logs-$(date +%Y%m%d).tar.gz data/logs/
```

### Cleanup Old Logs

```bash
# ลบ job logs เก่ากว่า 90 วัน
find data/logs/jobs/ -name "job_*.json" -mtime +90 -delete

# Rotate access logs
# (ควรใช้ logrotate)
```

## 📝 Development

### ทดสอบ Local

```bash
# Activate venv
source venv/bin/activate

# Run development server
python wsgi.py

# หรือใช้ Flask CLI
export FLASK_APP=wsgi:app
flask run --debug
```

### Code Structure

- `app/__init__.py`: Application factory
- `app/routes/`: All HTTP routes
- `app/config.py`: Config management
- `app/auth.py`: Authentication logic
- `app/etl_runner.py`: ETL execution
- `app/scheduler.py`: Job scheduling

## 📞 Support

หากมีปัญหาหรือข้อสงสัย:
1. ดู logs ที่ `data/logs/`
2. ตรวจสอบ config files
3. ทดสอบ ETL scripts แยกก่อน

## 📄 License

Internal use only
