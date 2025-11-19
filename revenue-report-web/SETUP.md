คู่มือการติดตั้งและตั้งค่าระบบ Revenue Report Distribution

## 📋 Prerequisites

- Python 3.10 or higher
- Access to SMTP server (mail.ntplc.co.th)
- Valid email account for sending OTPs

## 🚀 Installation Steps

### 1. Clone Repository

```bash
git clone <repository-url>
cd revenue-report-web
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Create Configuration Files from Templates

ระบบมี template files (`.example`) ที่ต้องนำไป copy และแก้ไขเป็นข้อมูลจริง

#### 3.1 Environment Variables

```bash
# Copy template
cp .env.example .env
```

แก้ไขไฟล์ `.env`:
```env
SMTP_USERNAME=your-actual-email@ntplc.co.th
SMTP_PASSWORD=your-actual-password
ADMIN_EMAILS=admin1@ntplc.co.th,admin2@ntplc.co.th
SECRET_KEY=generate-random-key-here
DEV_MODE=True
```

**วิธีสร้าง SECRET_KEY:**
```bash
# ใช้ Python
python -c "import secrets; print(secrets.token_hex(32))"

# หรือใช้ OpenSSL
openssl rand -hex 32
```

#### 3.2 Application Configuration

```bash
# Copy template
cp config.json.example config.json
```

แก้ไขไฟล์ `config.json`:
- ตั้งค่า `paths.reports_base_path` ให้ชี้ไปที่ตำแหน่งไฟล์รายงานจริง
- ปรับแต่ง email settings ตามต้องการ
- ตั้งค่า OTP parameters

#### 3.3 Data Files

```bash
# Copy all data templates
cp data/users.json.example data/users.json
cp data/otps.json.example data/otps.json
cp data/email_logs.json.example data/email_logs.json
```

**แก้ไข `data/users.json`** - เพิ่ม admin user แรก:
```json
{
  "users": [
    {
      "id": "admin-001",
      "email": "your-email@ntplc.co.th",
      "name": "Your Name",
      "is_admin": true,
      "is_active": true,
      "created_at": "2025-11-18T10:00:00",
      "last_login": null
    }
  ]
}
```

**แก้ไข `data/otps.json`** - เริ่มต้นด้วยข้อมูลว่าง:
```json
{
  "otps": []
}
```

**แก้ไข `data/email_logs.json`** - เริ่มต้นด้วยข้อมูลว่าง:
```json
{
  "emails": []
}
```

### 4. Verify Configuration

ตรวจสอบว่าทุกไฟล์ถูกสร้างแล้ว:

```bash
# ต้องมีไฟล์เหล่านี้ (ไม่ใช่ .example)
ls -la .env
ls -la config.json
ls -la data/users.json
ls -la data/otps.json
ls -la data/email_logs.json
```

### 5. Test Run (Dev Mode)

```bash
streamlit run app.py
```

เปิดบราวเซอร์: `http://localhost:8501`

## 🔒 Security Checklist

ก่อน deploy production:

- [ ] เปลี่ยน `SECRET_KEY` เป็นค่าที่สร้างแบบสุ่ม
- [ ] ตั้ง `DEV_MODE=False` ใน `.env`
- [ ] ตรวจสอบ SMTP credentials
- [ ] ทดสอบการส่ง email
- [ ] ตรวจสอบ reports path ว่าถูกต้อง
- [ ] สร้าง admin user
- [ ] ทดสอบ OTP authentication
- [ ] Backup ไฟล์ใน `data/` directory

## 📁 File Structure

```
revenue-report-web/
├── .env                      # ❌ ห้าม commit (มี sensitive data)
├── .env.example              # ✅ Template สำหรับ .env
├── config.json               # ❌ ห้าม commit (อาจมี sensitive paths)
├── config.json.example       # ✅ Template สำหรับ config.json
├── data/
│   ├── users.json           # ❌ ห้าม commit (มีข้อมูล user จริง)
│   ├── users.json.example   # ✅ Template
│   ├── otps.json            # ❌ ห้าม commit
│   ├── otps.json.example    # ✅ Template
│   ├── email_logs.json      # ❌ ห้าม commit
│   └── email_logs.json.example  # ✅ Template
├── .gitignore               # ป้องกันไฟล์ sensitive ถูก commit
└── ...
```

## 🌐 Production Deployment

### 6. Streamlit Configuration

สร้างไฟล์ config สำหรับ Streamlit:

```bash
mkdir -p .streamlit
nano .streamlit/config.toml
```

เพิ่มเนื้อหา:

```toml
[server]
baseUrlPath = ""
enableCORS = false
enableXsrfProtection = false
headless = true
port = 8501

[browser]
serverAddress = "centraldigital.cattelecom.com"
serverPort = 443
```

**หมายเหตุ:**
- `baseUrlPath = ""` - ไม่ต้องใส่ base path เพราะใช้ nginx rewrite
- `serverAddress` - แก้เป็นโดเมนของคุณ
- `serverPort = 443` - ใช้ HTTPS

### 7. Nginx Configuration

#### 7.1 เพิ่ม Upstream Block

แก้ไฟล์ `/etc/nginx/sites-available/default`:

```bash
sudo nano /etc/nginx/sites-available/default
```

เพิ่ม upstream block (ใกล้ upstream อื่นๆ ด้านบน):

```nginx
upstream streamlit_revenue {
    server localhost:8501;
    keepalive 64;
}
```

#### 7.2 เพิ่ม Location Block

เพิ่มใน `server` block ที่ `listen 443 ssl`:

```nginx
# ✅ START: Streamlit Revenue Report App
location /revenue/ {
    rewrite ^/revenue/(.*)$ /$1 break;
    proxy_pass http://streamlit_revenue/;
    
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    
    proxy_read_timeout 300s;
    proxy_buffering off;
    proxy_redirect off;
}
# ✅ END: Streamlit Revenue Report App
```

#### 7.3 ทดสอบและ Reload Nginx

```bash
# ทดสอบ config
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

### 8. Systemd Service (Auto-start on Boot)

#### 8.1 สร้าง Service File

```bash
sudo nano /etc/systemd/system/streamlit-revenue.service
```

เพิ่มเนื้อหา:

```ini
[Unit]
Description=Streamlit Revenue Report Application
After=network.target

[Service]
Type=simple
User=seal
Group=seal
WorkingDirectory=/home/seal/nt/revenue-report-web
Environment="PATH=/home/seal/nt/revenue-report-web/venv/bin"

# รัน Streamlit
ExecStart=/home/seal/nt/revenue-report-web/venv/bin/streamlit run app.py

# Restart policy
Restart=always
RestartSec=10

# Logging
StandardOutput=append:/home/seal/nt/revenue-report-web/logs/streamlit.log
StandardError=append:/home/seal/nt/revenue-report-web/logs/streamlit-error.log

[Install]
WantedBy=multi-user.target
```

**แก้ไขตามสภาพแวดล้อมของคุณ:**
- `User=seal` → เปลี่ยนเป็น username ของคุณ
- `Group=seal` → เปลี่ยนเป็น group ของคุณ
- `WorkingDirectory=/home/seal/nt/revenue-report-web` → เปลี่ยนเป็น path โปรเจคของคุณ
- Path ของ venv → ปรับให้ตรงกับของคุณ

#### 8.2 สร้าง Logs Directory

```bash
mkdir -p /home/seal/nt/revenue-report-web/logs
```

#### 8.3 Enable และ Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (รันอัตโนมัติตอน boot)
sudo systemctl enable streamlit-revenue.service

# Start service
sudo systemctl start streamlit-revenue.service

# ตรวจสอบสถานะ
sudo systemctl status streamlit-revenue.service
```

#### 8.4 คำสั่งจัดการ Service

```bash
# Restart service
sudo systemctl restart streamlit-revenue.service

# Stop service
sudo systemctl stop streamlit-revenue.service

# ดู log real-time
sudo journalctl -u streamlit-revenue.service -f

# หรือดูจากไฟล์
tail -f /home/seal/nt/revenue-report-web/logs/streamlit.log
tail -f /home/seal/nt/revenue-report-web/logs/streamlit-error.log

# ปิดการรันอัตโนมัติ
sudo systemctl disable streamlit-revenue.service
```

### 9. เข้าใช้งานระบบ

เปิดบราวเซอร์:

```
https://your-domain.com/revenue/
```

เช่น: `https://centraldigital.cattelecom.com/revenue/`

### 10. Session State Initialization Fix

**สำคัญ:** แก้ไขไฟล์ `app.py` เพื่อป้องกัน session state error:

```bash
nano app.py
```

เพิ่มการ initialize session state ในฟังก์ชัน `main()`:

```python
def main():
    # ✅ Initialize session state variables (ต้องมีก่อน check authentication)
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'etl_config_manager' not in st.session_state:
        st.session_state.etl_config_manager = None
    if 'etl_status' not in st.session_state:
        st.session_state.etl_status = None
    # เพิ่มตัวแปร session_state อื่นๆ ที่ใช้ในแอป...
    
    # ตรวจสอบ authentication
    if not st.session_state.authenticated:
        show_login_page()
    else:
        show_main_app()
```

**เหตุผล:** เมื่อ deploy ผ่าน nginx อาจเข้า path ที่ไม่ผ่าน login ทำให้ session state ยังไม่ถูก initialize

## 📊 Monitoring

### ตรวจสอบสถานะระบบ

```bash
# ดูว่า Streamlit ทำงานไหม
sudo systemctl is-active streamlit-revenue.service

# ดู resource usage
ps aux | grep streamlit

# ดู port ที่ใช้
netstat -tulpn | grep 8501

# ดู nginx access log
sudo tail -f /var/log/nginx/access.log | grep revenue

# ดู nginx error log
sudo tail -f /var/log/nginx/error.log
```

### Log Rotation (Optional)

สร้างไฟล์ logrotate config:

```bash
sudo nano /etc/logrotate.d/streamlit-revenue
```

เพิ่ม:

```
/home/seal/nt/revenue-report-web/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    missingok
    copytruncate
}
```

## 🔄 Update Deployment

เมื่อมีการอัพเดทโค้ด:

```bash
# 1. Pull latest code
cd /home/seal/nt/revenue-report-web
git pull

# 2. Update dependencies (ถ้ามี)
source venv/bin/activate
pip install -r requirements.txt

# 3. Restart service
sudo systemctl restart streamlit-revenue.service

# 4. ตรวจสอบสถานะ
sudo systemctl status streamlit-revenue.service
```

## 🐛 Production Troubleshooting

### Service ไม่ start

```bash
# ดู error message
sudo journalctl -u streamlit-revenue.service -n 50

# ตรวจสอบ permissions
ls -la /home/seal/nt/revenue-report-web/

# ทดสอบรันด้วยมือ
cd /home/seal/nt/revenue-report-web
source venv/bin/activate
streamlit run app.py
```

### Nginx 502 Bad Gateway

```bash
# ตรวจสอบว่า Streamlit ทำงานไหม
sudo systemctl status streamlit-revenue.service

# ตรวจสอบ port
netstat -tulpn | grep 8501

# ดู nginx error log
sudo tail -f /var/log/nginx/error.log
```

### Static Files ไม่โหลด (Firefox/Safari)

**อาการ:** หน้าเว็บขาว หรือ JavaScript error

**แก้ไข:** ตรวจสอบ nginx config ว่าใช้ `rewrite` และไม่มี baseUrlPath ใน Streamlit config

### Session State Error

**อาการ:** `AttributeError: st.session_state has no attribute...`

**แก้ไข:** ตรวจสอบว่ามีการ initialize session state ครบทุกตัวแปรในฟังก์ชัน `main()` (ดูข้อ 10)

## 🔐 Production Security Checklist

ก่อน deploy production ให้ตรวจสอบ:

- [ ] ตั้ง `DEV_MODE=False` ใน `.env`
- [ ] เปลี่ยน `SECRET_KEY` เป็นค่าที่ปลอดภัย
- [ ] ตรวจสอบ file permissions (data files ควร 600)
- [ ] Backup `data/` directory ก่อน deploy
- [ ] ทดสอบ OTP authentication
- [ ] ทดสอบส่ง email จริง
- [ ] ตรวจสอบ nginx SSL certificate
- [ ] ตั้งค่า log rotation
- [ ] เพิ่ม monitoring/alerting

## 🔧 Troubleshooting

### Error: FileNotFoundError: config.json

**สาเหตุ:** ยังไม่ได้ copy template file

**แก้ไข:**
```bash
cp config.json.example config.json
```

### Error: SMTP authentication failed

**สาเหตุ:** SMTP credentials ใน `.env` ไม่ถูกต้อง

**แก้ไข:**
1. ตรวจสอบ `SMTP_USERNAME` และ `SMTP_PASSWORD`
2. ทดสอบ login ที่ mail server ด้วย credentials เดียวกัน

### Error: User not found

**สาเหตุ:** ไม่มี user ใน `data/users.json`

**แก้ไข:**
1. Copy จาก template: `cp data/users.json.example data/users.json`
2. แก้ไข email และ name ให้ตรงกับของคุณ

## 📚 Additional Resources

- [README.md](README.md) - คู่มือการใช้งานโดยละเอียด
- [.env.example](.env.example) - Template สำหรับ environment variables
- [config.json.example](config.json.example) - Template สำหรับ configuration

## 🆘 Support

หากพบปัญหาในการติดตั้ง:
1. ตรวจสอบ error message ใน terminal
2. เปิด Dev Mode (`DEV_MODE=True`) เพื่อดู debug info
3. ตรวจสอบว่า template files ถูก copy และแก้ไขครบถ้วน
4. ติดต่อ system administrator

---

**Last Updated:** 2025-11-20
**Version:** 2.0 - Production Deployment