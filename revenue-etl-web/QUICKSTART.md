# Quick Start Guide

## ⚡ การเริ่มต้นใช้งานอย่างรวดเร็ว

### 1. ติดตั้ง Dependencies

```bash
cd /home/user/nt/revenue-etl-web
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. ตั้งค่า Environment

```bash
export SECRET_KEY='your-secret-key-change-this'
export FLASK_ENV='development'
```

### 3. Copy ETL Scripts ของคุณ

```bash
# Copy your actual ETL scripts to etl/ directory
cp /path/to/fi_revenue_expense.py etl/
cp /path/to/revenue_etl_report.py etl/
```

### 4. แก้ไข Config Files

แก้ไขไฟล์ 3 ไฟล์ใน `data/config/`:

#### `etl_config.json` - ตั้งค่า paths และ schedule
```json
{
  "paths": {
    "data_input": "/path/to/your/data",
    "master_files": "/path/to/master/files"
  },
  "schedule": {
    "enabled": true,
    "day_of_month": 10,
    "hour": 2,
    "minute": 0
  }
}
```

#### `email_config.json` - ตั้งค่า SMTP
```json
{
  "smtp": {
    "host": "mail.yourcompany.com",
    "port": 587,
    "username": "noreply@yourcompany.com",
    "password": "your-password"
  }
}
```

#### `auth_config.json` - ตั้งค่า domains และ admins
```json
{
  "allowed_domains": ["yourcompany.com"],
  "admin_emails": ["admin@yourcompany.com"]
}
```

### 5. รัน Development Server

```bash
source venv/bin/activate
python wsgi.py
```

เปิดเบราว์เซอร์ไปที่: http://localhost:5000

### 6. ทดสอบ Login

1. ใส่อีเมลที่ domain อนุญาต
2. รับ OTP ทางอีเมล
3. ใส่ OTP เพื่อเข้าสู่ระบบ

### 7. Deploy Production (Ubuntu Server)

#### 7.1 Install System Dependencies

```bash
sudo apt update
sudo apt install -y python3-venv nginx supervisor
```

#### 7.2 Setup Application

```bash
cd /opt
sudo git clone <your-repo> revenue-etl-web
cd revenue-etl-web
sudo python3 -m venv venv
sudo venv/bin/pip install -r requirements.txt
```

#### 7.3 Configure Supervisor

```bash
sudo nano /etc/supervisor/conf.d/revenue-etl-web.conf
```

แก้ไข paths ใน `supervisor.conf` แล้ว copy:

```bash
sudo cp supervisor.conf /etc/supervisor/conf.d/revenue-etl-web.conf
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start revenue-etl-web
```

#### 7.4 Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/revenue-etl-web
```

แก้ไข domain ใน `nginx.conf` แล้ว copy:

```bash
sudo cp nginx.conf /etc/nginx/sites-available/revenue-etl-web
sudo ln -s /etc/nginx/sites-available/revenue-etl-web /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 8. ตรวจสอบสถานะ

```bash
# Check supervisor
sudo supervisorctl status revenue-etl-web

# Check logs
tail -f data/logs/app.log
tail -f data/logs/access.log

# Check nginx
sudo systemctl status nginx
```

## 🎯 การใช้งานหลัก

### User
- Login → ดูรายการรายงาน → Download Excel

### Admin
- Login → Admin Dashboard
- **Run Job**: เลือก script → รันทันที
- **Config**: ตั้งค่า paths, SMTP, domains
- **Jobs**: ดูประวัติงานทั้งหมด
- **Logs**: ดู access logs

## 🚨 Troubleshooting

### ไม่สามารถ login ได้
```bash
# ตรวจสอบ SMTP config
cat data/config/email_config.json

# ตรวจสอบ allowed domains
cat data/config/auth_config.json
```

### งาน ETL ไม่ทำงาน
```bash
# ดู logs ของงาน
ls -lt data/logs/jobs/ | head -5

# ดู logs application
tail -50 data/logs/app.log
```

### Scheduler ไม่ทำงาน
```bash
# ตรวจสอบ schedule config
cat data/config/etl_config.json | grep -A 5 schedule

# Restart application
sudo supervisorctl restart revenue-etl-web
```

## 📚 เอกสารเพิ่มเติม

- **README.md** - เอกสารฉบับเต็ม
- **data/config/*.json** - ไฟล์ config พร้อมคำอธิบาย
- **app/routes/** - Routes documentation

## 🔒 Security Checklist

- [ ] เปลี่ยน `SECRET_KEY` ใน production
- [ ] ตั้งค่า HTTPS (SSL certificate)
- [ ] จำกัด allowed_domains ให้เฉพาะบริษัท
- [ ] เก็บ SMTP password ให้ปลอดภัย
- [ ] Backup config files เป็นประจำ
- [ ] จำกัดการเข้าถึง server ผ่าน firewall

---

**หากมีปัญหาหรือข้อสงสัย ติดต่อ Admin ของระบบ**
