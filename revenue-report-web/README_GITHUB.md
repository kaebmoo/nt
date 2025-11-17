# Revenue Report Distribution System

> 🚀 Web application สำหรับจัดการและส่งรายงาน Revenue ผ่าน email โดยใช้ OTP authentication

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red.svg)](https://streamlit.io/)

## ⚡ Quick Start

### 1. Clone และติดตั้ง

```bash
git clone <repository-url>
cd revenue-report-web
pip install -r requirements.txt
```

### 2. Setup Configuration

⚠️ **สำคัญ**: ต้อง copy template files ก่อนใช้งาน

```bash
# Environment variables
cp .env.example .env

# Application config
cp config.json.example config.json

# Data files
cp data/users.json.example data/users.json
cp data/otps.json.example data/otps.json
cp data/email_logs.json.example data/email_logs.json
```

### 3. แก้ไข Configuration

แก้ไขไฟล์ `.env`:
```env
SMTP_USERNAME=your-email@ntplc.co.th
SMTP_PASSWORD=your-password
ADMIN_EMAILS=admin@ntplc.co.th
SECRET_KEY=<generate-random-key>
DEV_MODE=True
```

แก้ไขไฟล์ `config.json`:
- ตั้งค่า `paths.reports_base_path` ให้ชี้ไปที่ตำแหน่งไฟล์รายงาน

แก้ไขไฟล์ `data/users.json`:
- เพิ่ม admin user แรก

### 4. Run Application

```bash
streamlit run app.py
```

เปิดบราวเซอร์: `http://localhost:8501`

## 📖 Documentation

- **[README.md](README.md)** - คู่มือการใช้งานโดยละเอียด
- **[SETUP.md](SETUP.md)** - คู่มือการติดตั้งและตั้งค่า

## ✨ Features

- 🔐 OTP-based Authentication (ไม่ใช้ password)
- 👥 User Management (JSON-based, no database)
- 📁 Browse & Download Excel Reports
- 📧 Email Distribution with Attachments
- ⚙️ Web-based Configuration Editor
- 📋 Email Sending Logs

## 🔒 Security Notice

ไฟล์เหล่านี้ **ไม่อยู่ใน Git** (มี sensitive data):
- `.env` - SMTP credentials
- `config.json` - อาจมี sensitive paths
- `data/users.json` - ข้อมูล user จริง
- `data/otps.json` - OTP codes
- `data/email_logs.json` - Email history

ต้อง **copy จาก `.example` files** และแก้ไขเองหลัง clone

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **Data Storage**: JSON files
- **Email**: SMTP with SSL
- **Authentication**: OTP (6-digit, 5-min expiry)

## 📦 Project Structure

```
revenue-report-web/
├── app.py                    # Main Streamlit app
├── config_manager.py         # Configuration management
├── user_manager.py           # User CRUD
├── auth_manager.py           # OTP authentication
├── email_sender.py           # Email with attachments
├── .env.example              # Template for .env
├── config.json.example       # Template for config.json
├── data/
│   ├── *.json.example       # Templates for data files
│   └── *.json               # Actual data (gitignored)
└── README.md                # Full documentation
```

## 🚀 For Developers

### Install Dev Dependencies

```bash
pip install -r requirements.txt
# Add optional dev tools:
pip install pytest black flake8
```

### Run in Dev Mode

ตั้งค่าใน `.env`:
```env
DEV_MODE=True
```

Dev Mode จะ:
- แสดง OTP บนหน้าจอแทนการส่ง email
- แสดง email preview แทนการส่งจริง
- Log detailed output

## 📝 License

Internal use only - NT Public Company Limited

## 🆘 Support

หากพบปัญหา:
1. อ่าน [SETUP.md](SETUP.md) สำหรับขั้นตอนติดตั้ง
2. อ่าน [README.md](README.md) สำหรับคู่มือการใช้งาน
3. ตรวจสอบว่า template files ถูก copy และแก้ไขครบถ้วน
4. เปิด Dev Mode เพื่อดู debug info

---

⚠️ **อย่าลืม**: หลัง clone ต้อง copy `.example` files และแก้ไขก่อนใช้งาน!
