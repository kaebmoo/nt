# Revenue ETL Web Application

Web-based interface for managing and monitoring Revenue ETL processes.

## Features

### For Users
- **OTP Authentication** - Login with email + OTP (no password required)
- **Download Reports** - Access and download Excel reports
- **Domain Whitelist** - Only authorized email domains can access

### For Admins
- **Dashboard** - Overview of jobs, scheduler, and system status
- **Configuration Management** - Manage ETL paths, SMTP settings, auth settings
- **Run Jobs** - Manually trigger ETL scripts
- **Job Monitoring** - View job history, status, and detailed logs
- **Access Logs** - Monitor user activities

### Automation
- **Scheduled Jobs** - Automatically run ETL on specified day/time each month
- **Email Notifications** - Get notified when jobs complete or fail
- **Background Processing** - Jobs run as subprocesses without blocking

## Technology Stack

- **Backend**: Flask 3.0
- **Scheduler**: APScheduler
- **Storage**: JSON files (no database required)
- **Authentication**: OTP via Email (SMTP)
- **Deployment**: Gunicorn + Nginx + Supervisor

## Project Structure

```
revenue-etl-web/
├── app/
│   ├── __init__.py          # Flask application factory
│   ├── auth.py              # OTP authentication system
│   ├── config.py            # Configuration management
│   ├── logger.py            # JSON-based logging
│   ├── etl_runner.py        # ETL script executor
│   ├── scheduler.py         # Job scheduler
│   ├── routes/              # Flask routes
│   │   ├── auth.py          # Login, OTP, logout
│   │   ├── user.py          # User dashboard
│   │   └── admin.py         # Admin dashboard, config, jobs
│   ├── templates/           # HTML templates
│   │   ├── base.html
│   │   ├── auth/            # Login pages
│   │   ├── user/            # User dashboard
│   │   └── admin/           # Admin pages
│   ├── static/              # CSS, JS
│   └── utils/               # Utilities
│       └── email_sender.py  # Email/OTP sender
├── data/
│   ├── config/              # JSON config files
│   │   ├── etl_config.json
│   │   ├── email_config.json
│   │   └── auth_config.json
│   ├── logs/                # Application logs
│   │   ├── app.log
│   │   ├── access.log
│   │   └── jobs/            # Job-specific logs
│   └── sessions/            # Session files
├── etl/                     # ETL scripts directory
│   ├── fi_revenue_expense.py
│   ├── revenue_etl_report.py
│   └── revenue_reconciliation.py
├── reports/                 # Generated reports output
├── requirements.txt         # Python dependencies
├── wsgi.py                 # WSGI entry point
├── gunicorn_config.py      # Gunicorn configuration
├── supervisor.conf         # Supervisor configuration
├── nginx.conf              # Nginx configuration
└── README.md               # This file
```

## Installation

### Prerequisites
- Python 3.8+
- Ubuntu Server (or similar Linux)
- Nginx
- Supervisor

### Step 1: Clone/Upload Project

```bash
# Upload project to server
cd /opt  # or your preferred directory
# ... upload revenue-etl-web directory ...
cd revenue-etl-web
```

### Step 2: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Copy ETL Scripts

```bash
# Copy your ETL scripts to etl/ directory
cp /path/to/fi_revenue_expense.py etl/
cp /path/to/revenue_etl_report.py etl/
cp /path/to/revenue_reconciliation.py etl/
```

### Step 4: Configure Application

Edit the 3 JSON config files in `data/config/`:

#### 4.1 ETL Configuration (`data/config/etl_config.json`)

```json
{
  "paths": {
    "data_input": "/path/to/your/input/data",
    "master_files": "/path/to/your/master/files",
    "output": "reports",
    "etl_scripts": "etl"
  },
  "schedule": {
    "enabled": true,
    "day_of_month": 10,
    "hour": 2,
    "minute": 0,
    "timezone": "Asia/Bangkok"
  },
  "scripts": {
    "fi_revenue_expense": "fi_revenue_expense",
    "revenue_etl_report": "revenue_etl_report",
    "revenue_reconciliation": "revenue_reconciliation"
  },
  "notifications": {
    "enabled": true,
    "on_success": true,
    "on_failure": true,
    "recipients": ["admin@example.com"]
  }
}
```

#### 4.2 Email Configuration (`data/config/email_config.json`)

```json
{
  "smtp": {
    "host": "mail.yourcompany.com",
    "port": 587,
    "use_tls": true,
    "username": "noreply@yourcompany.com",
    "password": "your-smtp-password"
  },
  "sender": {
    "name": "Revenue ETL System",
    "email": "noreply@yourcompany.com"
  },
  "otp": {
    "length": 6,
    "expiry_minutes": 10
  }
}
```

#### 4.3 Authentication Configuration (`data/config/auth_config.json`)

```json
{
  "allowed_domains": [
    "yourcompany.com"
  ],
  "admin_emails": [
    "admin@yourcompany.com"
  ],
  "session": {
    "timeout_minutes": 60
  }
}
```

### Step 5: Set Environment Variables

```bash
cp .env.example .env
nano .env

# Set your SECRET_KEY
SECRET_KEY=your-very-secret-key-here-change-this
```

### Step 6: Test Development Mode

```bash
python wsgi.py
# Visit http://localhost:5000
```

### Step 7: Deploy to Production

#### 7.1 Configure Supervisor

```bash
sudo cp supervisor.conf /etc/supervisor/conf.d/revenue-etl-web.conf

# Edit paths in the file
sudo nano /etc/supervisor/conf.d/revenue-etl-web.conf

# Update supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start revenue-etl-web
sudo supervisorctl status
```

#### 7.2 Configure Nginx

```bash
sudo cp nginx.conf /etc/nginx/sites-available/revenue-etl-web
sudo ln -s /etc/nginx/sites-available/revenue-etl-web /etc/nginx/sites-enabled/

# Edit domain and paths
sudo nano /etc/nginx/sites-available/revenue-etl-web

# Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

## Usage

### User Access

1. Visit the web application URL
2. Enter your email address
3. Receive OTP code via email
4. Enter OTP to login
5. Download reports from dashboard

### Admin Access

1. Login with admin email (configured in auth_config.json)
2. Access admin dashboard
3. Manage configurations
4. Run ETL jobs manually
5. Monitor job status and logs

## Configuration

All configurations are stored in JSON files under `data/config/`:

### ETL Configuration
- **Paths**: Input data, master files, output directories
- **Schedule**: Enable/disable auto-run, set date/time
- **Notifications**: Email alerts on job completion

### Email Configuration
- **SMTP**: Server, port, credentials
- **Sender**: From name and email address
- **OTP**: Code length and expiry time

### Authentication Configuration
- **Allowed Domains**: Whitelist email domains
- **Admin Emails**: Admin user emails
- **Session**: Timeout duration

## Logging

The application maintains several logs:

- `data/logs/app.log` - Application events
- `data/logs/access.log` - User access (JSON Lines format)
- `data/logs/jobs/*.json` - Individual job logs
- `data/logs/gunicorn-*.log` - Gunicorn logs

## Troubleshooting

### Application won't start

```bash
# Check logs
tail -f data/logs/app.log
tail -f data/logs/gunicorn-error.log

# Check supervisor
sudo supervisorctl status revenue-etl-web
```

### Can't login / OTP not received

- Check SMTP configuration in `data/config/email_config.json`
- Test SMTP connection manually
- Check email domain is in allowed list

### Jobs fail to run

- Check ETL script paths in config
- Ensure scripts are executable: `chmod +x etl/*.py`
- Check job logs in `data/logs/jobs/`

### Scheduler not running

- Check `enabled: true` in `etl_config.json`
- Restart application: `sudo supervisorctl restart revenue-etl-web`

## Security Notes

1. **Change SECRET_KEY** in production
2. **Use HTTPS** for production (configure SSL in nginx)
3. **Restrict email domains** to authorized users only
4. **Secure SMTP credentials** - use environment variables or encrypted storage
5. **Regular backups** of config and log files

## Maintenance

### View Logs

```bash
# Application logs
tail -f data/logs/app.log

# Access logs
tail -f data/logs/access.log

# Latest job log
ls -t data/logs/jobs/ | head -1 | xargs -I {} cat data/logs/jobs/{}
```

### Restart Application

```bash
sudo supervisorctl restart revenue-etl-web
```

### Update Application

```bash
cd /opt/revenue-etl-web
source venv/bin/activate
git pull  # or upload new files
pip install -r requirements.txt
sudo supervisorctl restart revenue-etl-web
```

## Support

For issues or questions, contact your system administrator.

---

**Version**: 1.0
**Last Updated**: 2025-01-14
