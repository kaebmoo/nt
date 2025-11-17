# Setup Guide - Revenue Report Distribution System

คู่มือการติดตั้งและตั้งค่าระบบ Revenue Report Distribution

## 📋 Prerequisites

- Python 3.8 or higher
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

**Last Updated:** 2025-11-18
