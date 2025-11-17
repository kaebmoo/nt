# Revenue Report Distribution System

Web application สำหรับจัดการและส่งรายงาน Revenue ผ่าน email โดยใช้ OTP authentication (ไม่ใช้ password)

## 📋 Features

### ✨ Core Features
- 🔐 **OTP-based Authentication** - ไม่ต้องจำรหัสผ่าน เข้าสู่ระบบด้วย OTP 6 หลักที่ส่งทาง email
- 👥 **User Management** - จัดการผู้ใช้ (เพิ่ม/ลบ/แก้ไข) แบบ JSON-based (ไม่ใช้ database)
- 📁 **Browse Reports** - เรียกดูและดาวน์โหลดไฟล์รายงาน Excel
- 📧 **Email Distribution** - ส่ง email พร้อมแนบไฟล์รายงานให้ผู้ใช้หลายคน
- ⚙️ **Configuration Editor** - แก้ไข config ผ่าน web interface (admin only)
- 📋 **Email Logs** - ติดตามประวัติการส่ง email

### 🎯 Key Capabilities
- **Dev Mode** - แสดง OTP และ email preview บนหน้าจอแทนการส่งจริง
- **Auto Email Domain** - เติม @ntplc.co.th อัตโนมัติ
- **Role-based Access** - Admin vs Regular User
- **Session Management** - Secure session handling
- **File Attachments** - ส่งไฟล์ Excel พร้อม email

---

## 🏗️ Architecture

```
revenue-report-web/
├── app.py                    # Main Streamlit application
├── config_manager.py         # Configuration management
├── user_manager.py           # User CRUD operations
├── auth_manager.py           # OTP authentication
├── email_sender.py           # Email with attachments
├── config.json               # Application configuration
├── .env                      # Environment variables (sensitive data)
├── requirements.txt          # Python dependencies
├── data/
│   ├── users.json           # User database (JSON)
│   ├── otps.json            # OTP storage (JSON)
│   └── email_logs.json      # Email history (JSON)
└── README.md                # This file
```

### Technology Stack
- **Frontend**: Streamlit (Python web framework)
- **Data Storage**: JSON files (no database required)
- **Email**: SMTP with SSL (mail.ntplc.co.th)
- **Authentication**: OTP-based (6-digit codes, 5-minute expiry)

---

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- Access to SMTP server (mail.ntplc.co.th)
- Valid email account for sending OTPs

### Steps

1. **Clone/Copy the project**
   ```bash
   cd /path/to/revenue-report-web
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**

   Edit `.env` file:
   ```env
   # Email Configuration
   SMTP_USERNAME=your-email@ntplc.co.th
   SMTP_PASSWORD=your-password

   # Admin Emails (comma-separated)
   ADMIN_EMAILS=admin1@ntplc.co.th,admin2@ntplc.co.th

   # Secret Key (change in production)
   SECRET_KEY=change-this-to-random-secret-key

   # Development Mode
   DEV_MODE=True
   ```

4. **Configure application settings**

   Edit `config.json` to set:
   - Reports path (where Excel files are located)
   - Email settings
   - OTP settings

5. **Create initial admin user**

   Edit `data/users.json`:
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

6. **Run the application**
   ```bash
   streamlit run app.py
   ```

7. **Access the application**

   Open browser: `http://localhost:8501`

---

## ⚙️ Configuration

### config.json

```json
{
  "app": {
    "name": "Revenue Report Distribution System",
    "version": "1.0.0",
    "dev_mode": true,
    "allowed_email_domain": "ntplc.co.th"
  },
  "paths": {
    "reports_base_path": "/path/to/Datasource",
    "reports_year": "2025",
    "reports_relative_path": "all/revenue/{year}"
  },
  "email": {
    "smtp_server": "mail.ntplc.co.th",
    "smtp_port": 465,
    "use_ssl": true,
    "from_email": "noreply@ntplc.co.th",
    "sender_name": "Revenue Report System"
  },
  "otp": {
    "code_length": 6,
    "expiry_minutes": 5,
    "max_attempts": 3
  }
}
```

### Configuration Sections

#### App Settings
- `name` - Application name
- `dev_mode` - Enable dev mode (shows OTP on screen instead of emailing)
- `allowed_email_domain` - Email domain (auto-appended if not provided)

#### Path Settings
- `reports_base_path` - Base directory for reports
- `reports_year` - Current year for reports
- `reports_relative_path` - Relative path from base (use `{year}` placeholder)

#### Email Settings
- `smtp_server` - SMTP server address
- `smtp_port` - SMTP port (465 for SSL)
- `use_ssl` - Use SSL connection
- `from_email` - Sender email address
- `sender_name` - Sender display name

#### OTP Settings
- `code_length` - OTP code length (default: 6)
- `expiry_minutes` - OTP validity period (default: 5 minutes)
- `max_attempts` - Max OTP generation attempts per hour (default: 3)

---

## 📖 Usage

### Login Process

1. **Enter email**
   - Type username (will auto-append @ntplc.co.th)
   - Or type full email address

2. **Request OTP**
   - Click "ขอรหัส OTP"
   - OTP will be sent to your email
   - In Dev Mode: OTP will be displayed on screen

3. **Enter OTP**
   - Enter the 6-digit code
   - Click "ยืนยัน OTP"
   - OTP expires after 5 minutes

### Browse Reports Tab

- View all Excel files from configured reports path
- Download individual files
- See file size and modification date

### Send Email Tab

1. **Select recipients** - Choose users from the list
2. **Select report files** - Choose Excel files to attach
3. **Preview email** - Check recipients and attachments
4. **Send** - Click "ส่ง Email"

### User Management Tab (Admin Only)

#### Add New User
- Enter email and name
- Choose admin/regular user role
- Set active status

#### Manage Users
- Toggle active/inactive status
- Toggle admin role
- Delete users
- Export users to CSV
- Import users from CSV

### Configuration Tab (Admin Only)

Edit all configuration settings through web interface:
- App settings
- Path settings
- Email settings
- OTP settings

Changes are saved immediately to `config.json`.

### Email Logs Tab (Admin Only)

- View email sending history
- See failed emails with error messages
- Filter by status

---

## 🔒 Security

### Authentication
- **Passwordless**: No password storage or management
- **OTP-based**: One-time passwords with expiration
- **Email verification**: OTP sent to registered email only

### Session Management
- Server-side session state
- Automatic logout on browser close
- No sensitive data in session cookies

### Data Storage
- **JSON files**: No database required
- **Environment variables**: Sensitive data in `.env` (not committed to git)
- **OTP cleanup**: Expired and used OTPs are automatically removed

### Email Security
- **SSL/TLS**: Encrypted SMTP connection
- **Credentials**: Stored in `.env` file only
- **Dev Mode**: Prevents accidental email sending during development

---

## 🔧 Troubleshooting

### Cannot login

**Problem**: Email domain error
- **Solution**: Check `allowed_email_domain` in `config.json`

**Problem**: User not found
- **Solution**: Verify user exists in `data/users.json` and is `is_active: true`

**Problem**: OTP not received
- **Solution**: Check SMTP settings in `.env` and `config.json`
- **Dev Mode**: Enable `dev_mode: true` to see OTP on screen

### Cannot send emails

**Problem**: SMTP authentication failed
- **Solution**: Verify `SMTP_USERNAME` and `SMTP_PASSWORD` in `.env`

**Problem**: Connection error
- **Solution**: Check `smtp_server` and `smtp_port` in `config.json`
- **Solution**: Verify SSL is enabled (`use_ssl: true`)

### Reports not found

**Problem**: Path not found
- **Solution**: Check `paths.reports_base_path` in config
- **Solution**: Verify directory exists
- **Solution**: Check `reports_year` matches actual folder structure

### Permission issues

**Problem**: User cannot access admin features
- **Solution**: Set `is_admin: true` in `data/users.json`

---

## 📊 Data Files

### users.json
```json
{
  "users": [
    {
      "id": "unique-id",
      "email": "user@ntplc.co.th",
      "name": "User Name",
      "is_admin": false,
      "is_active": true,
      "created_at": "2025-11-18T10:00:00",
      "last_login": "2025-11-18T14:30:00"
    }
  ]
}
```

### otps.json
```json
{
  "otps": [
    {
      "email": "user@ntplc.co.th",
      "otp_code": "123456",
      "created_at": "2025-11-18T14:25:00",
      "expires_at": "2025-11-18T14:30:00",
      "used": false
    }
  ]
}
```

### email_logs.json
```json
{
  "emails": [
    {
      "timestamp": "2025-11-18T14:30:00",
      "to": ["user1@ntplc.co.th", "user2@ntplc.co.th"],
      "subject": "รายงานรายได้ประจำเดือน ส.ค. 2025",
      "attachments": ["report_202508.xlsx"],
      "status": "sent",
      "error": null
    }
  ]
}
```

---

## 🧪 Development Mode

Enable dev mode in `.env`:
```env
DEV_MODE=True
```

Or in `config.json`:
```json
{
  "app": {
    "dev_mode": true
  }
}
```

### Dev Mode Features
- **OTP Display**: Shows OTP code on screen instead of emailing
- **Email Preview**: Displays email content without actually sending
- **Console Logging**: Detailed output in terminal

---

## 🔄 Updates & Maintenance

### Update Configuration
1. Edit `config.json` directly, or
2. Use Configuration tab in web interface (admin only)

### Add Users
1. Edit `data/users.json` directly, or
2. Use User Management tab (admin only), or
3. Import from CSV

### View Logs
- Email logs: `data/email_logs.json`
- Streamlit logs: Terminal output
- Check failed emails in Email Logs tab

### Backup
Important files to backup:
- `data/users.json` - User database
- `config.json` - Application configuration
- `.env` - Environment variables (credentials)

---

## 📞 Support

For issues or questions:
1. Check this README
2. Review configuration files
3. Enable dev mode for debugging
4. Contact system administrator

---

## 📝 License

Internal use only - NT Public Company Limited

---

## 🔗 Related Projects

- **revenue-report** - Main ETL system that generates the Excel reports
- **floor_price_validator** - Reference project for authentication architecture

---

## ✅ Checklist for Production

Before deploying to production:

- [ ] Change `SECRET_KEY` in `.env` to a strong random value
- [ ] Set `DEV_MODE=False` in `.env`
- [ ] Verify SMTP credentials are correct
- [ ] Test email sending
- [ ] Verify reports path is correct
- [ ] Create admin user(s)
- [ ] Test OTP authentication
- [ ] Backup `data/` directory
- [ ] Document admin contacts
- [ ] Set up regular backups

---

**Last Updated**: 2025-11-18
**Version**: 1.0.0
